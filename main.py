# -*- coding: utf-8 -*-
# main.py - Kompletter, korrigierter Code OHNE Minispiel-Buttons, MIT Button für Hauptspiel (Verwendet os.execv) MIT File-Logging
import pygame
import sys
import os
import traceback
import subprocess
import logging # Importiere Logging
import time # Importiere Time für Zeitstempel

# --- Pfad zum Skriptverzeichnis ermitteln ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()

# --- Pfade ---
data_dir = os.path.join(script_dir, "data")
log_dir = os.path.join(data_dir, "logs") # NEU: Log-Verzeichnis
music_file_path = os.path.join(data_dir, "sounds", "background", "menu_background_music.wav")
settings_dir = os.path.join(data_dir, "settings")
settings_file_path = os.path.join(settings_dir, "settings.json")
image_dir = os.path.join(data_dir, "bilder")
background_image_path = os.path.join(image_dir, "main_menu_background.png")
game_script_path = os.path.join(script_dir, "data", "etc", "game.py") # Pfad zum Hauptspiel

# --- Logging Konfiguration (Erweitert) ---
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
log_level = logging.DEBUG # Stufe für Konsole UND Datei (kann unterschiedlich sein)
date_fmt = '%Y-%m-%d %H:%M:%S'

# Basiskonfiguration für Konsole
logging.basicConfig(level=log_level, format=log_format, datefmt=date_fmt)

# Zusätzlicher File Handler
try:
    # Stelle sicher, dass das Log-Verzeichnis existiert
    os.makedirs(log_dir, exist_ok=True)
    # Erstelle Log-Dateinamen mit Zeitstempel
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"main_{timestamp}.log"
    log_file_path = os.path.join(log_dir, log_filename)

    # Erstelle FileHandler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG) # Logge alles ab DEBUG in die Datei

    # Erstelle Formatter und weise ihn dem Handler zu
    formatter = logging.Formatter(log_format, datefmt=date_fmt)
    file_handler.setFormatter(formatter)

    # Füge den Handler zum Root-Logger hinzu
    logging.getLogger().addHandler(file_handler)

    logging.info(f"File logging initialisiert. Log-Datei: {log_file_path}")

except Exception as e_log_setup:
    logging.error(f"Fehler beim Einrichten des File Logging für main.py: {e_log_setup}", exc_info=True)

# Logger Instanz für dieses Modul
logger = logging.getLogger(__name__)

# Logge Start und Pfade
logger.debug(f"Skriptverzeichnis ermittelt: {script_dir}")
logger.debug(f"Vollständiger Pfad zur Musikdatei wird sein: {music_file_path}")
logger.debug(f"Vollständiger Pfad zur Einstellungsdatei wird sein: {settings_file_path}")
logger.debug(f"Vollständiger Pfad zum Hintergrundbild wird sein: {background_image_path}")
logger.debug(f"Vollständiger Pfad zum Hauptspiel-Skript wird sein: {game_script_path}")
logger.info("Main Menu wird initialisiert...")


# --- Importiere Hilfsmodule ---
try:
    import data.etc.settings_utils as settings_utils
    import data.etc.options_menu as options_menu_module
    logger.debug("Hilfsmodule (settings, options) erfolgreich importiert.")
except ImportError as e_imp_utils:
     logger.critical(f"Konnte Hilfsmodule nicht importieren: {e_imp_utils}")
     logger.debug(f"Aktueller Python-Pfad: {sys.path}")
     logger.exception(e_imp_utils) # Loggt den Traceback
     sys.exit(1)
except Exception as e_utils:
     logger.critical(f"FEHLER beim Import der Hilfsmodule: {e_utils}", exc_info=True)
     sys.exit(1)

# --- Einstellungen laden ---
try:
    current_settings = settings_utils.load_settings(settings_file_path)
    logger.info(f"Einstellungen geladen aus {settings_file_path}: {current_settings}")
except Exception as e_load:
    logger.error(f"Fehler beim Laden der Einstellungen: {e_load}", exc_info=True)
    current_settings = {'music_volume': 0.5, 'sfx_volume': 0.5, 'master_volume': 0.5} # Fallback
    logger.warning(f"Fallback-Einstellungen werden verwendet: {current_settings}")
# ------------------------------------

# --- Android Immersive Mode & Platform Detection --- ### WICHTIG ###
is_android = False
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    logger.debug("(main): Pyjnius importiert.")
    Build = autoclass('android.os.Build$VERSION')
    sdk_int = Build.SDK_INT
    if sdk_int > 0:
        is_android = True
        logger.debug(f"(main): Android erkannt (SDK: {sdk_int}).")
    else:
         raise RuntimeError("Nicht Android")
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    assert activity is not None
    View = autoclass('android.view.View')
    Window = autoclass('android.view.Window')
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    flags = (View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
             View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
             View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)
    class SetUiVisibilityRunnablePJC(PythonJavaClass):
             __javainterfaces__ = ['java/lang/Runnable']
             def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
             @java_method('()V')
             def run(self):
                 try:
                     w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f)
                     w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                 except Exception as e: logger.error(f"FEHLER (Runnable): {e}", exc_info=True)
    runnable = SetUiVisibilityRunnablePJC(activity, flags)
    if activity: activity.runOnUiThread(runnable); logger.debug("(main): Runnable Immersive gestartet.")
except ImportError: logger.info("(main): Pyjnius nicht gefunden. Nehme an, es ist nicht Android."); is_android = False
except Exception as e: logger.warning(f"Immersive Mode fehlgeschlagen oder nicht Android: {e}"); is_android = False
# --- Ende Android Immersive Mode ---

# --- Minispiel-Imports entfernt, da Buttons entfernt wurden ---
# zipWeedGame = None # Entfernt
# cockCrackGame = None # Entfernt

# --- Grundlegende Pygame Initialisierung ---
try:
    pygame.init()
    logger.info("Pygame initialisiert.")
except Exception as e_pygame_init:
    logger.critical(f"Pygame konnte nicht initialisiert werden: {e_pygame_init}", exc_info=True)
    sys.exit(1)


# --- Mixer initialisieren ---
mixer_initialized = False
try:
    pygame.mixer.init()
    logger.info("Pygame Mixer erfolgreich initialisiert.")
    mixer_initialized = True
    # --- LAUTSTÄRKE ANWENDEN ---
    try:
        pygame.mixer.music.set_volume(current_settings["music_volume"])
        logger.info(f"Musiklautstärke auf {current_settings['music_volume']:.2f} gesetzt.")
    except pygame.error as e_set_vol:
        logger.warning(f"Konnte initiale Musiklautstärke nicht setzen: {e_set_vol}")
except pygame.error as e_mixer:
    logger.error(f"Pygame Mixer konnte nicht initialisiert werden: {e_mixer}", exc_info=True)

# --- Bildschirm Setup ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = None
try:
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
    logger.info(f"Hauptmenü Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    # pygame.SCALED wird für Android empfohlen, kann auf Desktop zu Problemen führen
    # flags = pygame.SCALED if is_android else 0 # Alternativ Fullscreen: pygame.FULLSCREEN
    flags = pygame.SCALED # Behalte SCALED vorerst bei
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
except Exception as e_display:
    logger.warning(f"Konnte Bildschirmgröße nicht ermitteln oder Modus nicht setzen: {e_display}. Nutze Standardgröße 800x600.")
    SCREEN_WIDTH = 800; SCREEN_HEIGHT = 600
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED) # Fallback auch mit SCALED
    except Exception as e_fallback_display:
        logger.critical(f"Konnte auch Fallback-Bildschirm (800x600) nicht initialisieren: {e_fallback_display}", exc_info=True)
        pygame.quit(); sys.exit()

if screen is None:
    logger.critical("Bildschirm konnte nicht initialisiert werden.")
    pygame.quit(); sys.exit()

pygame.display.set_caption("Hauptmenü - DrugsDealerGame")

# --- Hintergrundbild laden ---
background_image = None
try:
    if os.path.exists(background_image_path):
        loaded_image = pygame.image.load(background_image_path).convert()
        background_image = pygame.transform.scale(loaded_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        logger.info(f"Hintergrundbild geladen und skaliert: {background_image_path}")
    else:
        logger.warning(f"Hintergrundbild nicht gefunden: {background_image_path}. Nutze weiße Füllung.")
except pygame.error as e_img:
    logger.error(f"Fehler beim Laden/Skalieren des Hintergrundbildes: {e_img}", exc_info=True)
except Exception as e:
    logger.error(f"Allgemeiner Fehler beim Verarbeiten des Hintergrundbildes: {e}", exc_info=True)
# --- Ende Hintergrundbild ---

# Farben
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GRAY = (200, 200, 200); DARK_GRAY = (150, 150, 150); GREEN = (0, 128, 0); RED = (200, 0, 0)

# --- Inventarvariablen (Beispiel) ---
# Diese sollten idealerweise aus einer Speicherdatei geladen oder vom Hauptspiel übergeben werden
weed = 20; grips = 20; sorte = "Normal"; packed_weed_total = 0; pills = 3; liquid = 3; Crack = 0; liquidName = "Wasser"; pillsName = "Tafelgan"

# --- Button Definition (Hauptmenü) --- # ANGEPASST: Nur 2 Buttons
BUTTON_WIDTH_PERCENT = 0.40; BUTTON_HEIGHT_PERCENT = 0.09; BUTTON_SPACING_PERCENT = 0.03; FONT_SIZE_REF_H = 600.0; BASE_FONT_SIZE = 30
button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_spacing = int(SCREEN_HEIGHT * BUTTON_SPACING_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2

# Berechnung für 2 Buttons
total_buttons_height = 2 * button_height + 1 * button_spacing
button1_y = (SCREEN_HEIGHT - total_buttons_height) // 2 # Y für Button 1 (Hauptspiel)
button2_y = button1_y + button_height + button_spacing # Y für Button 2 (Optionen)

# Rechtecke für die Buttons
button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height) # Hauptspiel
button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height) # Optionen

# --- Schriftarten für Hauptmenü-Buttons und Status ---
button_font_size = max(15, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text1_surface = None # Für Hauptspiel
text2_surface = None # Für Optionen

button1_text = "Starte Hauptspiel" # Text für Button 1
button2_text = "Optionen"        # Text für Button 2

try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    if button_font:
        text1_surface = button_font.render(button1_text, True, BLACK)
        text2_surface = button_font.render(button2_text, True, BLACK)
    else:
        raise Exception("SysFont lieferte None")
except Exception as e_font:
    logger.warning(f"Laden der Button-Schriftart 'arial' fehlgeschlagen: {e_font}. Nutze Fallback.")
    try:
        button_font = pygame.font.Font(None, int(button_font_size * 1.1))
        if button_font:
            text1_surface = button_font.render(button1_text, True, BLACK)
            text2_surface = button_font.render(button2_text, True, BLACK)
        else:
            raise Exception("Fallback Font lieferte None")
    except Exception as e_font_fallback:
        logger.error(f"Konnte auch Fallback-Button-Schriftart nicht laden: {e_font_fallback}", exc_info=True)
        text1_surface = text2_surface = None

# Status Schriftart (unverändert)
STATUS_FONT_SIZE_REF_H = 600.0; BASE_STATUS_FONT_SIZE = 22; status_font_size = max(12, int(SCREEN_HEIGHT * (BASE_STATUS_FONT_SIZE / STATUS_FONT_SIZE_REF_H))); status_font = None
try:
    status_font = pygame.font.SysFont("arial", status_font_size)
    logger.debug(f"Status-Schriftart 'arial' geladen (Größe {status_font_size}).")
except Exception as e_sfont:
    logger.warning(f"Konnte Status-Schriftart 'arial' nicht laden: {e_sfont}. Nutze Fallback.")
    try:
        status_font = pygame.font.Font(None, status_font_size + 1)
        logger.debug(f"Fallback-Status-Schriftart geladen (Größe {status_font_size+1}).")
    except Exception as e_sfont_fallback:
        logger.error(f"Konnte auch Fallback-Status-Schriftart nicht laden: {e_sfont_fallback}", exc_info=True)
        status_font = None
STATUS_X = 15; STATUS_Y = 15; STATUS_LINE_HEIGHT = status_font.get_height() + 5 if status_font else status_font_size + 5

clock = pygame.time.Clock()

# --- Musik Helper Funktion ---
def play_menu_music():
    global music_playing, mixer_initialized, current_settings
    if not pygame.mixer.get_init():
        logger.warning("Versuche Mixer neu zu initialisieren in play_menu_music.")
        try:
            pygame.mixer.init()
            mixer_initialized = True
            logger.info("Pygame Mixer wurde neu initialisiert.")
        except pygame.error as e_reinit:
            logger.error(f"Mixer Re-Initialisierung fehlgeschlagen: {e_reinit}", exc_info=True)
            mixer_initialized = False
            return
    if mixer_initialized:
        logger.debug(f"Prüfe Existenz von: {music_file_path}")
        if os.path.exists(music_file_path):
            try:
                pygame.mixer.music.load(music_file_path)
                logger.info(f"Musikdatei '{music_file_path}' geladen.")
                pygame.mixer.music.set_volume(current_settings.get("music_volume", 0.5))
                logger.debug(f"Lautstärke gesetzt auf {current_settings.get('music_volume', 0.5):.2f}")
                pygame.mixer.music.play(loops=-1)
                logger.info("Musikwiedergabe gestartet (Looping).")
                music_playing = True
            except pygame.error as e_load_music:
                logger.error(f"Musikdatei '{music_file_path}' konnte nicht geladen/abgespielt werden: {e_load_music}", exc_info=True)
                music_playing = False
        else:
            logger.error(f"Musikdatei nicht gefunden unter: '{music_file_path}'")
            music_playing = False
    else:
        logger.warning("Mixer nicht initialisiert, keine Musikwiedergabe.")
        music_playing = False

def stop_menu_music():
    global music_playing
    if mixer_initialized and music_playing and pygame.mixer.get_init():
        try:
            pygame.mixer.music.stop()
            logger.info("Musik gestoppt.")
            music_playing = False
        except pygame.error as e_stop_music:
            logger.warning(f"Fehler beim Stoppen der Musik: {e_stop_music}")

# --- Initiale Musik starten ---
music_playing = False
play_menu_music()

# --- Spielzustand-Variable ---
# Nur noch "main_menu" und temporär "calling_options" relevant hier
current_screen_state = "main_menu"

# --- Hauptschleife ---
logger.info("Hauptschleife startet.")
running = True
while running:
    try: # Füge try/except um die Hauptschleife hinzu für besseres Error-Logging
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                logger.info("QUIT Event empfangen.")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Im Hauptmenü führt ESC zum Beenden
                    if current_screen_state == "main_menu":
                        running = False
                        logger.info("ESC im Hauptmenü -> Beenden.")
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    if current_screen_state == "main_menu":
                        # Button 1: Hauptspiel (os.execv)
                        if button1_rect.collidepoint(mouse_pos):
                            logger.info(f"Button 'Hauptspiel' geklickt. Versuche Spiel zu starten: {game_script_path}")
                            if os.path.exists(game_script_path):
                                logger.info("Beende Menü-Pygame und starte Hauptspiel via os.execv...")
                                stop_menu_music()
                                pygame.quit() # Pygame beenden BEVOR execv
                                logger.info("Menü-Pygame beendet.")
                                try:
                                    # Stelle sicher, dass sys.executable der richtige Python-Interpreter ist
                                    python_executable = sys.executable
                                    args_for_exec = [python_executable, game_script_path]
                                    logger.info(f"Führe os.execv aus mit: {args_for_exec}")
                                    os.execv(python_executable, args_for_exec)
                                    # WICHTIG: Code nach os.execv wird nur ausgeführt, wenn execv fehlschlägt!
                                except FileNotFoundError:
                                    logger.critical(f"Python Interpreter '{python_executable}' oder Spiel-Skript '{game_script_path}' nicht gefunden.", exc_info=True)
                                    # Versuch, den Fehler anzuzeigen, bevor das Programm beendet wird
                                    # Da Pygame beendet ist, können wir keine Grafik mehr anzeigen. Loggen ist der beste Weg.
                                    sys.exit(1) # Beenden, da execv fehlschlug
                                except Exception as e_exec:
                                    logger.critical(f"Fehler beim Versuch, os.execv auszuführen: {e_exec}", exc_info=True)
                                    sys.exit(1) # Beenden, da execv fehlschlug
                            else:
                                logger.error(f"Hauptspiel-Skript nicht gefunden unter: {game_script_path}")
                                # Optional: Visuelles Feedback geben, dass das Skript fehlt (wenn Pygame noch liefe)

                        # Button 2: Optionen
                        elif button2_rect.collidepoint(mouse_pos):
                            logger.info("Button 'Optionen' geklickt.")
                            previous_state = current_screen_state
                            current_screen_state = "calling_options" # Temporärer Status
                            try:
                                # Übergebe eine Kopie der Einstellungen, um Seiteneffekte zu vermeiden
                                returned_settings = options_menu_module.run_options_menu(screen, current_settings.copy(), settings_file_path)
                                logger.debug(f"Optionsmenü hat zurückgegeben: {returned_settings}") # Behalte Debug drin

                                # Prüfe, ob das Optionsmenü das Beenden signalisiert (None zurückgibt)
                                if returned_settings is None:
                                    running = False
                                    logger.info("Optionsmenü gab None zurück -> Spiel beenden.")
                                else:
                                    # Einstellungen aktualisieren
                                    current_settings = returned_settings
                                    # Musiklautstärke sofort anwenden
                                    if mixer_initialized:
                                        try:
                                            pygame.mixer.music.set_volume(current_settings["music_volume"])
                                            logger.info(f"Musiklautstärke nach Optionen auf {current_settings['music_volume']:.2f} gesetzt.")
                                        except pygame.error as e_set_vol_opt:
                                            logger.warning(f"Konnte Musiklautstärke nach Optionen nicht setzen: {e_set_vol_opt}")
                                    logger.info("Einstellungen nach Optionsmenü aktualisiert.")
                                    # Musik ggf. neu starten, falls sie im Optionsmenü gestoppt wurde
                                    if not music_playing:
                                         play_menu_music()

                            except Exception as e_opt_run:
                                logger.error(f"Fehler beim Ausführen des Optionsmenüs: {e_opt_run}", exc_info=True)
                                # Fehlerbehandlung: Zurück zum vorherigen Zustand
                            finally:
                                # Stelle sicher, dass der Zustand zurückgesetzt wird, außer wenn das Spiel beendet wird
                                if running:
                                     current_screen_state = previous_state
                                     # Bildschirm neu zeichnen erzwingen, falls nötig (hier durch flip am Ende)

        # --- Zeichnen ---
        if current_screen_state == "main_menu":
            # Hintergrund
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill(WHITE) # Fallback-Hintergrund

            # Buttons zeichnen (ANGEPASST für 2 Buttons)
            btn_rects = [button1_rect, button2_rect]
            btn_surfaces = [text1_surface, text2_surface]
            btn_colors = [GRAY if not rect.collidepoint(mouse_pos) else DARK_GRAY for rect in btn_rects]

            for i, rect in enumerate(btn_rects):
                pygame.draw.rect(screen, btn_colors[i], rect) # Hintergrund des Buttons
                pygame.draw.rect(screen, BLACK, rect, 3)       # Rand des Buttons
                if btn_surfaces[i] and button_font:
                    text_rect = btn_surfaces[i].get_rect(center=rect.center)
                    screen.blit(btn_surfaces[i], text_rect.topleft)

            # Statusanzeige zeichnen (unverändert)
            if status_font:
                current_y = STATUS_Y
                texts_to_render = [
                    (f"Weed ({sorte}): {weed}", BLACK),
                    (f"Grips: {grips}", BLACK),
                    (f"Verpackt: {packed_weed_total}", GREEN),
                    ("", BLACK), # Leere Zeile für Abstand
                    (f"{pillsName}: {pills}", BLACK),
                    (f"{liquidName}: {liquid}", BLACK),
                    (f"Crack: {Crack}", RED)
                ]
                for text, color in texts_to_render:
                    if text: # Nur rendern, wenn Text vorhanden ist
                        try:
                             text_surf = status_font.render(text, True, color)
                             screen.blit(text_surf, (STATUS_X, current_y))
                        except Exception as e_render_status:
                             logger.error(f"Fehler beim Rendern des Status-Textes '{text}': {e_render_status}")
                    current_y += STATUS_LINE_HEIGHT

        # --- Minispiel-Ausführung entfernt ---
        # elif current_screen_state == "zipweed_game": ... (Entfernt)
        # elif current_screen_state == "cockcrack_game": ... (Entfernt)

        # --- Bildschirm aktualisieren ---
        # Nur aktualisieren, wenn wir im Hauptmenü sind oder ein Frame gezeichnet werden muss
        if current_screen_state == "main_menu":
             try:
                 pygame.display.flip()
             except pygame.error as e_flip:
                 logger.error(f"Fehler bei pygame.display.flip(): {e_flip}")
                 # Ggf. versuchen, Pygame neu zu initialisieren oder beenden?
                 # Fürs Erste loggen wir den Fehler und machen weiter oder beenden.
                 running = False # Sicherer Ausweg bei Display-Fehler

        # --- Framerate begrenzen ---
        clock.tick(60)

    except Exception as e_main_loop:
        logger.critical(f"Unerwarteter Fehler in der Hauptschleife: {e_main_loop}", exc_info=True)
        running = False # Schleife sicher beenden bei unerwartetem Fehler

# --- Aufräumen nach der Hauptschleife ---
logger.info("Hauptschleife beendet.")
stop_menu_music() # Musik stoppen

# Prüfen, ob Pygame noch initialisiert ist, bevor quit() aufgerufen wird
# Dies ist wichtig, falls os.execv aufgerufen wurde (dann ist Pygame hier schon beendet)
if pygame.get_init():
    logger.info("Hauptmenü wird beendet. Pygame wird heruntergefahren.")
    pygame.quit()
else:
    logger.info("Hauptmenü wird beendet (Pygame war bereits beendet, z.B. durch os.execv).")

# Expliziter Exit-Aufruf am Ende
sys.exit()