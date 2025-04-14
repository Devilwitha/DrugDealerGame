# platform_utils.py
import os
import logging
import traceback # Für detaillierte Fehlermeldungen

logger = logging.getLogger(__name__)

# --- Plattformerkennung ---
IS_ANDROID = False # Standardwert
ANDROID_SDK_INT = 0
_android_activity = None # Zwischenspeicher für die Activity

try:
    # Versuche Pyjnius zu importieren (nur auf Android erfolgreich)
    from jnius import autoclass, cast, PythonJavaClass, java_method
    logger.info("Pyjnius erfolgreich importiert.")

    # Prüfe Android Version
    Build = autoclass('android.os.Build$VERSION')
    sdk_int = Build.SDK_INT
    if sdk_int > 0:
        IS_ANDROID = True
        ANDROID_SDK_INT = sdk_int
        logger.info(f"Android erkannt (SDK: {ANDROID_SDK_INT}).")

        # Hole die aktuelle Activity (wird für UI-Änderungen benötigt)
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity') # Standard für Kivy/Buildozer
            # Alternativ, falls anderer Bootstrapper:
            # PythonActivity = autoclass('org.beeware.android.MainActivity') # Beispiel für BeeWare
            # PythonActivity = autoclass('ru.iiec.pydroid3.PythonActivity') # Beispiel für Pydroid? (Ungetestet)

            # Prüfe, welche Activity verfügbar ist
            if hasattr(PythonActivity, 'mActivity') and PythonActivity.mActivity:
                _android_activity = PythonActivity.mActivity
                logger.info("Android Activity (mActivity) gefunden.")
            elif hasattr(PythonActivity, 'getInstance') and PythonActivity.getInstance():
                 # Manchmal über statische Methode, z.B. in älteren p4a Versionen?
                 _android_activity = PythonActivity.getInstance()
                 logger.info("Android Activity (getInstance) gefunden.")
            else:
                 logger.warning("Konnte Android Activity nicht automatisch finden (weder mActivity noch getInstance). Immersive Mode / Screen On nicht verfügbar.")

        except Exception as e_activity:
            logger.error(f"Fehler beim Zugriff auf PythonActivity: {e_activity}")
            IS_ANDROID = False # Wenn Activity nicht geholt werden kann, behandeln wir es als nicht-Android

    else:
        # SDK <= 0 bedeutet normalerweise nicht Android
        logger.info("Kein Android (SDK <= 0).")
        IS_ANDROID = False

except ImportError:
    logger.info("Pyjnius nicht gefunden. Es wird angenommen, dass die Plattform nicht Android ist.")
    IS_ANDROID = False
except Exception as e:
    logger.error(f"Unerwarteter Fehler bei der Android-Erkennung: {e}")
    # traceback.print_exc() # Bei Bedarf Traceback ausgeben
    IS_ANDROID = False


def set_android_immersive_mode():
    """
    Versucht, den Immersive Sticky Mode auf Android zu aktivieren und den Bildschirm an zu lassen.
    Funktioniert nur, wenn IS_ANDROID True ist und die Activity gefunden wurde.
    """
    if not IS_ANDROID or not _android_activity:
        if IS_ANDROID and not _android_activity:
             logger.warning("set_android_immersive_mode: Kann nicht ausgeführt werden, keine Android Activity gefunden.")
        # else: logger.debug("set_android_immersive_mode: Nicht Android, keine Aktion.")
        return

    try:
        logger.info("Versuche Android Immersive Mode zu aktivieren...")
        View = autoclass('android.view.View')
        Window = autoclass('android.view.Window')
        WindowManager = autoclass('android.view.WindowManager$LayoutParams')

        # Flags für Immersive Sticky Mode + Keep Screen On
        flags = (
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        )
        window_flags_add = WindowManager.FLAG_KEEP_SCREEN_ON

        # Erstelle ein Runnable, das im UI-Thread von Android ausgeführt wird
        class SetUiVisibilityRunnable(PythonJavaClass):
            __javainterfaces__ = ['java/lang/Runnable']
            def __init__(self, activity, view_flags, window_flags_add):
                super().__init__()
                self.activity = activity
                self.view_flags = view_flags
                self.window_flags_add = window_flags_add

            @java_method('()V')
            def run(self):
                try:
                    w = self.activity.getWindow()
                    if not w:
                        logger.error("Immersive Runnable: Konnte Window nicht bekommen.")
                        return
                    d = w.getDecorView()
                    if not d:
                         logger.error("Immersive Runnable: Konnte DecorView nicht bekommen.")
                         return

                    logger.debug("Immersive Runnable: Setze System UI Visibility Flags.")
                    d.setSystemUiVisibility(self.view_flags)

                    logger.debug("Immersive Runnable: Füge Window Flags hinzu (Keep Screen On).")
                    w.addFlags(self.window_flags_add)
                    logger.info("Immersive Mode und Keep Screen On sollten jetzt aktiv sein.")
                except Exception as e_run:
                    logger.error(f"Fehler im Immersive Runnable: {e_run}")
                    traceback.print_exc()

        runnable = SetUiVisibilityRunnable(_android_activity, flags, window_flags_add)
        # Führe das Runnable im UI-Thread aus
        _android_activity.runOnUiThread(runnable)
        logger.debug("Immersive Mode Runnable an UI-Thread übergeben.")

    except Exception as e:
        logger.error(f"Fehler beim Setzen des Immersive Mode: {e}")
        traceback.print_exc()

# Optional: Direkt beim Import prüfen (kann aber Seiteneffekte haben)
# set_android_immersive_mode()

# Man kann auch eine Funktion anbieten, um die Activity zu holen, falls sie später gebraucht wird
def get_android_activity():
    return _android_activity