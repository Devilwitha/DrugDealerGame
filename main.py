# -*- coding: utf-8 -*-
import pygame
import sys
import os
import traceback

# --- Pfad zum Skriptverzeichnis ermitteln ---
# Dies ist der entscheidende Teil für Android-Kompatibilität
try:
    # __file__ gibt den Pfad zur aktuell ausgeführten Datei an
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"DEBUG: Skriptverzeichnis ermittelt: {script_dir}")
except NameError:
    # Fallback, falls __file__ nicht definiert ist (z.B. in manchen interaktiven Umgebungen)
    script_dir = os.getcwd()
    print(f"WARNUNG: __file__ nicht gefunden, nutze aktuelles Arbeitsverzeichnis: {script_dir}")


# --- Pfad zur Musikdatei ---
# Konstruiere den Pfad RELATIV zum Skriptverzeichnis
music_file_path = os.path.join(script_dir, "data", "sounds", "background", "menu_background_music.wav")
print(f"DEBUG: Vollständiger Pfad zur Musikdatei wird sein: {music_file_path}")
# ------------------------------------

# --- Android Immersive Mode & Platform Detection --- ### WICHTIG ###
is_android = False # Standardmäßig nicht Android
try: # Android Specific Code
    from jnius import autoclass, cast, PythonJavaClass, java_method
    print("DEBUG (zipWeed): Pyjnius importiert.")
    Build = autoclass('android.os.Build$VERSION')
    sdk_int = Build.SDK_INT
    if sdk_int > 0:
        is_android = True # Hier wird erkannt, dass es Android ist
        print(f"DEBUG (zipWeed): Android erkannt (SDK: {sdk_int}).")
    else:
         raise RuntimeError("Nicht Android") # Explizit Fehler werfen wenn SDK <= 0
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    assert activity is not None # Stellen sicher, dass wir eine Activity haben
    View = autoclass('android.view.View')
    Window = autoclass('android.view.Window')
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    flags = (
        View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
        View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
        View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
        View.SYSTEM_UI_FLAG_FULLSCREEN |
        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
    )
    class SetUiVisibilityRunnablePJC(PythonJavaClass):
            __javainterfaces__ = ['java/lang/Runnable']
            def __init__(self, a, f):
                super().__init__()
                self.a = a
                self.f = f
            @java_method('()V')
            def run(self):
                try:
                    w = self.a.getWindow()
                    d = w.getDecorView()
                    d.setSystemUiVisibility(self.f)
                    w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                except Exception as e:
                    print(f"FEHLER (Runnable): {e}")
                    traceback.print_exc()
    runnable = SetUiVisibilityRunnablePJC(activity, flags)
    if activity:
        activity.runOnUiThread(runnable)
        print("DEBUG (zipWeed): Runnable Immersive gestartet.")
except ImportError:
    print("INFO (zipWeed): Pyjnius nicht gefunden. Nehme an, es ist nicht Android.")
    is_android = False # Sicherstellen, dass es False ist, wenn Import fehlschlägt
except Exception as e:
    print(f"FEHLER oder Info (zipWeed): Immersive Mode fehlgeschlagen oder nicht Android: {e}")
    # traceback.print_exc() # Optional: Traceback nur bei echtem Fehler anzeigen
    is_android = False # Sicherstellen, dass es False ist bei anderen Fehlern

# --- Importiere die Minispiel-Skripte ---
# Stelle sicher, dass die Pfade korrekt sind, relativ zu diesem Skript

# ZipWeed Minispiel
zipWeedGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.zipWeed.zipWeed")
    # Füge ggf. den übergeordneten Ordner zum Python-Pfad hinzu, falls nötig
    # sys.path.append(os.path.join(script_dir, '..')) # Beispiel, falls Ordnerstruktur anders
    import data.miniGame.zipWeed.zipWeed as zipWeedGame
    print(f"DEBUG: Import von {zipWeedGame.__name__} erfolgreich.")
except ImportError as e_imp_zw:
    print(f"FEHLER: Konnte das ZipWeed-Modul nicht importieren: {e_imp_zw}")
    print(f"Aktueller Python-Pfad: {sys.path}") # Hilft beim Debuggen von Import-Problemen
    traceback.print_exc()
except Exception as e_zw:
    print(f"FEHLER beim Import von ZipWeed: {e_zw}")
    traceback.print_exc()

# CockCrack Minispiel
cockCrackGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.cockCrack.cockCrack")
    # Importiert das Paket/Modul
    import data.miniGame.cockCrack.cockCrack as cockCrackGame
    print(f"DEBUG: Import von {cockCrackGame.__name__} erfolgreich.")
except ImportError as e_imp_cc:
    print(f"FEHLER: Konnte das CockCrack-Modul nicht importieren: {e_imp_cc}")
    print(f"Aktueller Python-Pfad: {sys.path}") # Hilft beim Debuggen von Import-Problemen
    traceback.print_exc()
except Exception as e_cc:
    print(f"FEHLER beim Import von CockCrack: {e_cc}")
    traceback.print_exc()

# --- Grundlegende Pygame Initialisierung ---
pygame.init()

# --- NEU: Mixer initialisieren für Musik ---
try:
    pygame.mixer.init()
    print("INFO: Pygame Mixer erfolgreich initialisiert.")
    mixer_initialized = True
except pygame.error as e_mixer:
    print(f"FEHLER: Pygame Mixer konnte nicht initialisiert werden: {e_mixer}")
    print(">>> Musikwiedergabe wird nicht funktionieren.")
    mixer_initialized = False
# --- Ende Mixer Initialisierung ---


# Bildschirmgröße
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
try:
    # Versuche, die volle Bildschirmgröße zu bekommen
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
    print(f"Hauptmenü Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    # Setze den Modus auf Scaled (passt sich an, Fullscreen kann Probleme machen)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
except Exception as e_display:
    print(f"Konnte Bildschirmgröße nicht ermitteln oder Modus nicht setzen: {e_display}. Nutze Standardgröße 800x600.")
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    except Exception as e_fallback_display:
        print(f"FEHLER: Konnte auch Fallback-Bildschirm (800x600) nicht initialisieren: {e_fallback_display}")
        pygame.quit()
        sys.exit()

pygame.display.set_caption("Hauptmenü - DrugsDealerGame")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
GREEN = (0, 128, 0)
RED = (200, 0, 0) # Für Text, falls benötigt

# --- Inventarvariablen ---
# ZipWeed / Allgemein
weed = 20
grips = 20
sorte = "Normal"
packed_weed_total = 0
# NEU: Variablen für CockCrack
pills = 3
liquid = 3
Crack = 0  # Startwert für Crack
liquidName = "Wasser"
pillsName = "Tafelgan"
# --- Ende neue Variablen ---

# --- Button Definition (Proportional) ---
BUTTON_WIDTH_PERCENT = 0.40
BUTTON_HEIGHT_PERCENT = 0.12
BUTTON_SPACING_PERCENT = 0.05
FONT_SIZE_REF_H = 600.0  # Referenzhöhe für Schriftgröße
BASE_FONT_SIZE = 40      # Basis Schriftgröße bei Referenzhöhe

button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_spacing = int(SCREEN_HEIGHT * BUTTON_SPACING_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2

total_buttons_height = 2 * button_height + button_spacing
# Zentriere die Buttons vertikal
button1_y = (SCREEN_HEIGHT - total_buttons_height) // 2
button2_y = button1_y + button_height + button_spacing

button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height) # ZipWeed Button
button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height) # CockCrack Button

# Proportionale Schriftgröße Button
# Stelle sicher, dass die Schriftgröße nicht zu klein wird
button_font_size = max(15, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text1_surface = None
text2_surface = None
button1_text = "Starte ZipWeed Minispiel"
button2_text = "Starte CockCrack Minispiel" # Angepasster Text

try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    if button_font:
        text1_surface = button_font.render(button1_text, True, BLACK)
        text2_surface = button_font.render(button2_text, True, BLACK)
    else:
        raise Exception("SysFont lieferte None") # Erzwinge Fallback, wenn Font nicht geladen
except Exception as e_font:
    print(f"WARNUNG beim Laden der Button-Schriftart 'arial': {e_font}. Nutze Fallback.")
    try:
        # Skaliere Fallback-Font ggf. leicht anders, da er anders rendern kann
        button_font = pygame.font.Font(None, int(button_font_size * 1.1))
        if button_font:
             text1_surface = button_font.render(button1_text, True, BLACK)
             text2_surface = button_font.render(button2_text, True, BLACK)
        else:
             raise Exception("Fallback Font lieferte None")
    except Exception as e_font_fallback:
        print(f"FEHLER: Konnte auch Fallback-Button-Schriftart nicht laden: {e_font_fallback}")
        # Hier könnte man noch einen ganz simplen Font versuchen oder ohne Text weitermachen

# Schriftart und Position für Statusanzeige (Inventar)
STATUS_FONT_SIZE_REF_H = 600.0
BASE_STATUS_FONT_SIZE = 22 # Kleinere Basisgröße für Status
status_font_size = max(12, int(SCREEN_HEIGHT * (BASE_STATUS_FONT_SIZE / STATUS_FONT_SIZE_REF_H)))
status_font = None
try:
    status_font = pygame.font.SysFont("arial", status_font_size)
    if not status_font: raise Exception("SysFont lieferte None")
    print(f"DEBUG: Status-Schriftart 'arial' geladen (Größe {status_font_size}).")
except Exception as e_sfont:
    print(f"WARNUNG: Konnte Status-Schriftart 'arial' nicht laden: {e_sfont}. Nutze Fallback.")
    try:
        status_font = pygame.font.Font(None, status_font_size)
        if not status_font: raise Exception("Fallback Font lieferte None")
        print(f"DEBUG: Fallback-Status-Schriftart geladen (Größe {status_font_size}).")
    except Exception as e_sfont_fallback:
        print(f"FEHLER: Konnte auch Fallback-Status-Schriftart nicht laden: {e_sfont_fallback}")

STATUS_X = 15
STATUS_Y = 15
STATUS_LINE_HEIGHT = 0
if status_font:
    # Berechne Zeilenhöhe basierend auf der geladenen Schriftart
    STATUS_LINE_HEIGHT = status_font.get_height() + 5
else:
    # Fallback-Wert, falls keine Schriftart geladen werden konnte
    STATUS_LINE_HEIGHT = status_font_size + 5 # Annäherung


clock = pygame.time.Clock()

# --- NEU: Musik laden und abspielen ---
music_playing = False
if mixer_initialized:
    # Überprüfe, ob die Datei existiert, BEVOR du versuchst, sie zu laden
    # Verwende den NEUEN, potenziell absoluten Pfad
    print(f"DEBUG: Prüfe Existenz von: {music_file_path}") # Zusätzliches Debugging
    if os.path.exists(music_file_path):
        try:
            pygame.mixer.music.load(music_file_path)
            print(f"INFO: Musikdatei '{music_file_path}' (existiert) geladen.")
            pygame.mixer.music.play(loops=-1) # -1 für unendlichen Loop
            print("INFO: Musikwiedergabe gestartet (Looping).")
            music_playing = True
        except pygame.error as e_load_music:
            print(f"FEHLER: Musikdatei '{music_file_path}' konnte nicht geladen oder abgespielt werden: {e_load_music}")
            print(">>> Stelle sicher, dass die WAV-Datei nicht korrupt ist und vom Mixer unterstützt wird.")
    else:
        # Gib den Pfad aus, den Python zu finden versucht hat
        print(f"FEHLER: Musikdatei nicht gefunden unter dem konstruierten Pfad: '{music_file_path}'")
        print(f">>> Aktuelles Arbeitsverzeichnis: {os.getcwd()}") # Immer noch nützlich zum Vergleich
        print(f">>> Verzeichnis des Skripts (__file__): {script_dir}") # Zeigt, wo das Skript liegt
        print(">>> Überprüfe:")
        print("    1. Ob die Datei 'menu_background_music.wav' wirklich im Unterordner 'data/sounds/background' relativ zum Skript liegt.")
        print("    2. Ob dieser Ordner und die Datei korrekt mit der App gepackt wurden (z.B. in buildozer.spec).")
else:
    print("INFO: Mixer wurde nicht initialisiert, keine Musikwiedergabe.")
# --- Ende Musik Laden ---

# --- Hauptschleife des Menüs ---
menu_running = True
while menu_running:
    # Hole Mausposition einmal pro Frame
    mouse_pos = pygame.mouse.get_pos()

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            menu_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                menu_running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Prüfe nur auf Linksklick (Button 1)
            if event.button == 1:
                # --- Button 1: ZipWeed ---
                if button1_rect.collidepoint(mouse_pos): # Verwende gespeicherte mouse_pos
                    print("INFO: Starte ZipWeed Minispiel...")
                    if zipWeedGame:
                        try:
                            # MUSIK LÄUFT HIER WEITER!
                            print(f"DEBUG: Rufe zipWeedGame.run_zip_weed_game mit screen, weed={weed}, grips={grips}, sorte='{sorte}' auf")
                            # WICHTIG: Die Minispiel-Funktion muss die Kontrolle zurückgeben!
                            result_tuple = zipWeedGame.run_zip_weed_game(screen, weed, grips, sorte)

                            # Verarbeite das Ergebnis NACHDEM das Minispiel beendet ist
                            if result_tuple is not None: # Expliziter Check auf None ist sicherer
                                try:
                                    remaining_weed, remaining_grips, packed_count, returned_sorte = result_tuple
                                    print(f"DEBUG: ZipWeed Ergebnis erhalten: Weed={remaining_weed}, Grips={remaining_grips}, Packed in Runde={packed_count}, Sorte='{returned_sorte}'")
                                    # Aktualisiere Inventar
                                    weed = remaining_weed
                                    grips = remaining_grips
                                    packed_weed_total += packed_count
                                    # sorte = returned_sorte # Optional: Sorte aktualisieren
                                    print(f"DEBUG: Inventar aktualisiert: Weed={weed}, Grips={grips}, Gesamt Verpackt={packed_weed_total}")
                                except (TypeError, ValueError) as e_unpack_zw:
                                    print(f"FEHLER: Rückgabewert von ZipWeed konnte nicht korrekt entpackt werden: {e_unpack_zw}")
                                    print(f">>> Erhalten: {result_tuple}. Erwartet: (weed, grips, packed, sorte)")
                            else:
                                # Funktion gab None zurück, vielleicht weil sie vorzeitig beendet wurde?
                                print("WARNUNG: ZipWeed hat kein Ergebnis (None) zurückgegeben!")

                            print("INFO: Zurück im Hauptmenü nach ZipWeed.")
                            # MUSIK LÄUFT IMMER NOCH!

                        # Spezifischere Fehlerbehandlung
                        except AttributeError as e_attr_zw:
                            print(f"FEHLER (AttributeError ZipWeed): {e_attr_zw}")
                            print(">>> Funktion 'run_zip_weed_game' wurde nicht im Modul 'zipWeedGame' gefunden.")
                            traceback.print_exc()
                        except TypeError as e_type_zw:
                            print(f"FEHLER (TypeError ZipWeed): {e_type_zw}")
                            print(">>> Funktion 'run_zip_weed_game' wurde mit falschen Argumenten aufgerufen oder gab ein unerwartetes Format zurück.")
                            traceback.print_exc()
                        except Exception as e_game_zw:
                            # Fängt alle anderen Fehler während der Ausführung des Minispiels ab
                            print(f"FEHLER während der Ausführung des ZipWeed Minispiels: {e_game_zw}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: ZipWeed-Modul (zipWeedGame) konnte nicht importiert werden. Minispiel nicht verfügbar.")

                # --- Button 2: CockCrack ---
                elif button2_rect.collidepoint(mouse_pos): # Verwende gespeicherte mouse_pos
                    print("INFO: Starte CockCrack Minispiel...")
                    if cockCrackGame:
                        try:
                            # MUSIK LÄUFT HIER WEITER!
                            print(f"DEBUG: Rufe cockCrackGame.run_cock_crack_game mit screen, pills={pills}, liquid={liquid}, Crack={Crack}, liquidName='{liquidName}', pillsName='{pillsName}' auf")
                            # Direkter Aufruf der Funktion im importierten Modul
                            function_to_call_cc = cockCrackGame.run_cock_crack_game

                            if callable(function_to_call_cc): # Sicherstellen, dass es eine Funktion ist
                                # WICHTIG: Die Minispiel-Funktion muss die Kontrolle zurückgeben!
                                result_cc = function_to_call_cc(screen, pills, liquid, Crack, liquidName, pillsName)

                                # Verarbeite das Ergebnis NACHDEM das Minispiel beendet ist
                                if result_cc is not None: # Expliziter Check auf None
                                    try:
                                        # Passe die erwartete Struktur an, was CockCrack zurückgibt
                                        remaining_pills_cc, remaining_liquid_cc, new_crack_total_cc = result_cc
                                        print(f"DEBUG: CockCrack Ergebnis erhalten: Pills={remaining_pills_cc}, Liquid={remaining_liquid_cc}, Crack={new_crack_total_cc}")
                                        # Aktualisiere Inventar
                                        pills = remaining_pills_cc
                                        liquid = remaining_liquid_cc
                                        Crack = new_crack_total_cc
                                        print(f"DEBUG: Inventar aktualisiert: Pills={pills}, Liquid={liquid}, Crack={Crack}")
                                    except (TypeError, ValueError) as e_unpack_cc:
                                         print(f"FEHLER: Rückgabewert von CockCrack konnte nicht korrekt entpackt werden: {e_unpack_cc}")
                                         print(f">>> Erhalten: {result_cc}. Erwartet: (pills, liquid, crack)") # Beispiel

                                else:
                                    # Funktion gab None zurück
                                    print("WARNUNG: CockCrack hat kein Ergebnis (None) zurückgegeben!")

                                print("INFO: Zurück im Hauptmenü nach CockCrack.")
                                # MUSIK LÄUFT IMMER NOCH!
                            else:
                                # function_to_call_cc war nicht aufrufbar
                                print(f"FEHLER: 'run_cock_crack_game' in cockCrackGame ist nicht aufrufbar!")

                        # Spezifischere Fehlerbehandlung
                        except AttributeError as e_attr_cc:
                            print(f"FEHLER (AttributeError CockCrack): {e_attr_cc}")
                            print(f">>> Funktion 'run_cock_crack_game' wurde nicht im Modul '{cockCrackGame.__name__}' gefunden.")
                            traceback.print_exc()
                        except TypeError as e_type_cc:
                            print(f"FEHLER (TypeError CockCrack): {e_type_cc}")
                            print(">>> Funktion 'run_cock_crack_game' wurde mit falschen Argumenten aufgerufen oder gab ein unerwartetes Format zurück.")
                            print(">>> Erwartete Argumente: (screen, pills, liquid, Crack, liquidName, pillsName)")
                            traceback.print_exc()
                        except Exception as e_game_cc:
                            # Fängt alle anderen Fehler während der Ausführung des Minispiels ab
                            print(f"FEHLER während der Ausführung des CockCrack Minispiels: {e_game_cc}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: CockCrack-Modul (cockCrackGame) konnte nicht importiert werden. Minispiel nicht verfügbar.")

    # Zeichnen (findet jeden Frame statt)
    screen.fill(WHITE) # Hintergrund löschen

    # --- Buttons zeichnen ---
    # Button 1 (ZipWeed)
    button1_color = GRAY
    # Highlight wenn Maus drüber ist
    if button1_rect.collidepoint(mouse_pos):
        button1_color = DARK_GRAY
    pygame.draw.rect(screen, button1_color, button1_rect) # Füllung
    pygame.draw.rect(screen, BLACK, button1_rect, 3)      # Rand
    # Zeichne Text nur, wenn Font und Surface erfolgreich erstellt wurden
    if text1_surface and button_font:
        text1_rect = text1_surface.get_rect(center=button1_rect.center)
        screen.blit(text1_surface, text1_rect.topleft)

    # Button 2 (CockCrack)
    button2_color = GRAY
    if button2_rect.collidepoint(mouse_pos):
        button2_color = DARK_GRAY
    pygame.draw.rect(screen, button2_color, button2_rect) # Füllung
    pygame.draw.rect(screen, BLACK, button2_rect, 3)      # Rand
    if text2_surface and button_font:
        text2_rect = text2_surface.get_rect(center=button2_rect.center)
        screen.blit(text2_surface, text2_rect.topleft)

    # --- Statusanzeige (Inventar) zeichnen ---
    if status_font: # Nur zeichnen, wenn Schriftart verfügbar ist
        try:
            current_y = STATUS_Y # Y-Position für die erste Zeile
            # Definiere Texte für Inventar
            texts_to_render = [
                (f"Weed ({sorte}): {weed}", BLACK),
                (f"Grips: {grips}", BLACK),
                (f"Verpackt: {packed_weed_total}", GREEN),
                ("", BLACK), # Leere Zeile für Abstand
                (f"{pillsName}: {pills}", BLACK),
                (f"{liquidName}: {liquid}", BLACK),
                (f"Crack: {Crack}", RED)
            ]

            # Rendere und blitte jede Zeile
            for text, color in texts_to_render:
                if text: # Überspringe leere Zeilen fürs Rendering
                    text_surf = status_font.render(text, True, color)
                    screen.blit(text_surf, (STATUS_X, current_y))
                # Erhöhe Y für die nächste Zeile, auch für leere Zeilen (für den Abstand)
                current_y += STATUS_LINE_HEIGHT

        except Exception as e_render_status:
            # Fängt Fehler ab, die spezifisch beim Rendern/Blitten auftreten könnten
            print(f"FEHLER beim Rendern des Status-Textes: {e_render_status}")
            # Optional: Zeige Fehlermeldung auf dem Bildschirm an
            try:
                error_surf = status_font.render("Fehler Status Anzeige", True, RED)
                screen.blit(error_surf, (STATUS_X, STATUS_Y))
            except: pass # Verhindere Fehler im Fehlerhandler
    else:
        # Optional: Nachricht, wenn kein Status-Font geladen wurde
        # print("DEBUG: Kein Status-Font geladen, Anzeige übersprungen.")
        pass

    # Aktualisiere den Bildschirm, um alles Gezeichnete anzuzeigen
    pygame.display.flip()

    # Begrenze die Framerate
    clock.tick(60) # Lässt das Spiel mit maximal 60 FPS laufen

# --- Aufräumen nach der Hauptschleife ---

# --- NEU: Musik stoppen (optional, aber sauber) ---
if mixer_initialized and music_playing:
    try:
        pygame.mixer.music.stop()
        print("INFO: Musik gestoppt.")
    except pygame.error as e_stop_music:
        # Fehler beim Stoppen ist normalerweise nicht kritisch
        print(f"WARNUNG: Fehler beim Stoppen der Musik: {e_stop_music}")
# --- Ende Musik stoppen ---

# Pygame Module beenden
print("INFO: Hauptmenü wird beendet. Pygame wird heruntergefahren.")
pygame.quit()

# Skript beenden
sys.exit()