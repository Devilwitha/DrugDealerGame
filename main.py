# -*- coding: utf-8 -*-
# main.py - Kompletter, korrigierter Code MIT Button für Hauptspiel
import pygame
import sys
import os
import traceback
import subprocess # <-- Hinzugefügt für das Starten von game.py

# --- Pfad zum Skriptverzeichnis ermitteln ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"DEBUG: Skriptverzeichnis ermittelt: {script_dir}")
except NameError:
    script_dir = os.getcwd()
    print(f"WARNUNG: __file__ nicht gefunden, nutze aktuelles Arbeitsverzeichnis: {script_dir}")

# --- Pfade ---
data_dir = os.path.join(script_dir, "data")
music_file_path = os.path.join(data_dir, "sounds", "background", "menu_background_music.wav")
settings_dir = os.path.join(data_dir, "settings")
settings_file_path = os.path.join(settings_dir, "settings.json")
image_dir = os.path.join(data_dir, "bilder") # Pfad für Bilder
background_image_path = os.path.join(image_dir, "main_menu_background.png") # Name des Hintergrundbilds (anpassen!)
game_script_path = os.path.join(script_dir, "data", "etc", "game.py") # <-- Pfad zum Hauptspiel-Skript

print(f"DEBUG: Vollständiger Pfad zur Musikdatei wird sein: {music_file_path}")
print(f"DEBUG: Vollständiger Pfad zur Einstellungsdatei wird sein: {settings_file_path}")
print(f"DEBUG: Vollständiger Pfad zum Hintergrundbild wird sein: {background_image_path}")
print(f"DEBUG: Vollständiger Pfad zum Hauptspiel-Skript wird sein: {game_script_path}")


# --- Importiere Hilfsmodule ---
try:
    import data.etc.settings_utils as settings_utils
    import data.etc.options_menu as options_menu_module
    print("DEBUG: Hilfsmodule (settings, options) erfolgreich importiert.")
except ImportError as e_imp_utils:
     print(f"FEHLER: Konnte Hilfsmodule nicht importieren: {e_imp_utils}")
     print(f"Aktueller Python-Pfad: {sys.path}")
     traceback.print_exc()
     pygame.quit()
     sys.exit()
except Exception as e_utils:
     print(f"FEHLER beim Import der Hilfsmodule: {e_utils}")
     traceback.print_exc()
     pygame.quit()
     sys.exit()

# --- Einstellungen laden ---
current_settings = settings_utils.load_settings(settings_file_path)
# ------------------------------------

# --- Android Immersive Mode & Platform Detection --- ### WICHTIG ###
# (Android Code bleibt unverändert)
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
# --- Ende Android Immersive Mode ---

# --- Importiere die Minispiel-Skripte ---
zipWeedGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.zipWeed.zipWeed")
    import data.miniGame.zipWeed.zipWeed as zipWeedGame
    print(f"DEBUG: Import von {zipWeedGame.__name__} erfolgreich.")
except ImportError as e_imp_zw:
    print(f"FEHLER: Konnte das ZipWeed-Modul nicht importieren: {e_imp_zw}")
    print(f"Aktueller Python-Pfad: {sys.path}")
    traceback.print_exc()
except Exception as e_zw:
    print(f"FEHLER beim Import von ZipWeed: {e_zw}")
    traceback.print_exc()

cockCrackGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.cockCrack.cockCrack")
    import data.miniGame.cockCrack.cockCrack as cockCrackGame
    print(f"DEBUG: Import von {cockCrackGame.__name__} erfolgreich.")
except ImportError as e_imp_cc:
    print(f"FEHLER: Konnte das CockCrack-Modul nicht importieren: {e_imp_cc}")
    print(f"Aktueller Python-Pfad: {sys.path}")
    traceback.print_exc()
except Exception as e_cc:
    print(f"FEHLER beim Import von CockCrack: {e_cc}")
    traceback.print_exc()
# --- Ende Minispiel-Import ---


# --- Grundlegende Pygame Initialisierung ---
pygame.init()

# --- Mixer initialisieren ---
mixer_initialized = False
try:
    pygame.mixer.init()
    print("INFO: Pygame Mixer erfolgreich initialisiert.")
    mixer_initialized = True
    # --- LAUTSTÄRKE ANWENDEN ---
    try:
        pygame.mixer.music.set_volume(current_settings["music_volume"])
        print(f"INFO: Musiklautstärke auf {current_settings['music_volume']:.2f} gesetzt.")
    except pygame.error as e_set_vol:
        print(f"WARNUNG: Konnte initiale Musiklautstärke nicht setzen: {e_set_vol}")
except pygame.error as e_mixer:
    print(f"FEHLER: Pygame Mixer konnte nicht initialisiert werden: {e_mixer}")

# --- Bildschirm Setup ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = None # Initialisieren
try:
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
    print(f"Hauptmenü Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
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

if screen is None:
    print("FEHLER: Bildschirm konnte nicht initialisiert werden.")
    pygame.quit()
    sys.exit()

pygame.display.set_caption("Hauptmenü - DrugsDealerGame")

# --- Hintergrundbild laden ---
background_image = None
try:
    if os.path.exists(background_image_path):
        loaded_image = pygame.image.load(background_image_path).convert()
        background_image = pygame.transform.scale(loaded_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        print(f"INFO: Hintergrundbild geladen und skaliert: {background_image_path}")
    else:
        print(f"INFO: Hintergrundbild nicht gefunden: {background_image_path}. Nutze weiße Füllung.")
except pygame.error as e_img:
    print(f"FEHLER beim Laden/Skalieren des Hintergrundbildes: {e_img}")
    background_image = None
except Exception as e:
    print(f"Allgemeiner FEHLER beim Verarbeiten des Hintergrundbildes: {e}")
    traceback.print_exc()
    background_image = None
# --- Ende Hintergrundbild ---

# Farben
WHITE = (255, 255, 255) # Fallback-Farbe
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
GREEN = (0, 128, 0)
RED = (200, 0, 0)

# --- Inventarvariablen ---
weed = 20
grips = 20
sorte = "Normal"
packed_weed_total = 0
pills = 3
liquid = 3
Crack = 0
liquidName = "Wasser"
pillsName = "Tafelgan"

# --- Button Definition (Hauptmenü) --- # NEU MIT 4 BUTTONS
BUTTON_WIDTH_PERCENT = 0.40
BUTTON_HEIGHT_PERCENT = 0.09 # Etwas kleiner, damit 4 passen
BUTTON_SPACING_PERCENT = 0.03 # Etwas weniger Abstand
FONT_SIZE_REF_H = 600.0 # Für Font-Skalierung
BASE_FONT_SIZE = 30     # Für Font-Skalierung, etwas kleiner

button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_spacing = int(SCREEN_HEIGHT * BUTTON_SPACING_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2

total_buttons_height = 4 * button_height + 3 * button_spacing # Höhe für VIER Buttons
# Zentriere die Buttons vertikal
button1_y = (SCREEN_HEIGHT - total_buttons_height) // 2 # Oberster Button (ZipWeed)
button2_y = button1_y + button_height + button_spacing # CockCrack
button3_y = button2_y + button_height + button_spacing # Optionen
button4_y = button3_y + button_height + button_spacing # Hauptspiel

# --- Button Rects erstellen ---
button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height) # ZipWeed
button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height) # CockCrack
button3_rect = pygame.Rect(button_x, button3_y, button_width, button_height) # Optionen
button4_rect = pygame.Rect(button_x, button4_y, button_width, button_height) # Hauptspiel

# --- Schriftarten für Hauptmenü-Buttons und Status ---
# Proportionale Schriftgröße Button
button_font_size = max(15, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text1_surface = None
text2_surface = None
text3_surface = None
text4_surface = None # <-- Für Hauptspiel Button
button1_text = "Starte ZipWeed Minispiel"
button2_text = "Starte CockCrack Minispiel"
button3_text = "Optionen"
button4_text = "Starte Hauptspiel" # <-- Text für Hauptspiel Button

try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    if button_font:
        text1_surface = button_font.render(button1_text, True, BLACK)
        text2_surface = button_font.render(button2_text, True, BLACK)
        text3_surface = button_font.render(button3_text, True, BLACK)
        text4_surface = button_font.render(button4_text, True, BLACK) # <-- Rendern Hauptspiel
    else:
        raise Exception("SysFont lieferte None")
except Exception as e_font:
    print(f"WARNUNG beim Laden der Button-Schriftart 'arial': {e_font}. Nutze Fallback.")
    try:
        button_font = pygame.font.Font(None, int(button_font_size * 1.1)) # Fallback oft etwas größer nötig
        if button_font:
             text1_surface = button_font.render(button1_text, True, BLACK)
             text2_surface = button_font.render(button2_text, True, BLACK)
             text3_surface = button_font.render(button3_text, True, BLACK)
             text4_surface = button_font.render(button4_text, True, BLACK) # <-- Rendern Hauptspiel
        else:
             raise Exception("Fallback Font lieferte None")
    except Exception as e_font_fallback:
        print(f"FEHLER: Konnte auch Fallback-Button-Schriftart nicht laden: {e_font_fallback}")
        # Setze Surfaces auf None, damit Blit übersprungen wird
        text1_surface = text2_surface = text3_surface = text4_surface = None

# Schriftart und Position für Statusanzeige (Inventar)
STATUS_FONT_SIZE_REF_H = 600.0
BASE_STATUS_FONT_SIZE = 22
status_font_size = max(12, int(SCREEN_HEIGHT * (BASE_STATUS_FONT_SIZE / STATUS_FONT_SIZE_REF_H)))
status_font = None
try:
    status_font = pygame.font.SysFont("arial", status_font_size)
    if not status_font: raise Exception("SysFont lieferte None")
    print(f"DEBUG: Status-Schriftart 'arial' geladen (Größe {status_font_size}).")
except Exception as e_sfont:
    print(f"WARNUNG: Konnte Status-Schriftart 'arial' nicht laden: {e_sfont}. Nutze Fallback.")
    try:
        status_font = pygame.font.Font(None, status_font_size + 1) # Fallback
        if not status_font: raise Exception("Fallback Font lieferte None")
        print(f"DEBUG: Fallback-Status-Schriftart geladen (Größe {status_font_size+1}).")
    except Exception as e_sfont_fallback:
        print(f"FEHLER: Konnte auch Fallback-Status-Schriftart nicht laden: {e_sfont_fallback}")
        status_font = None # Kein Status-Font verfügbar

STATUS_X = 15
STATUS_Y = 15
STATUS_LINE_HEIGHT = 0
if status_font:
    STATUS_LINE_HEIGHT = status_font.get_height() + 5
else:
    STATUS_LINE_HEIGHT = status_font_size + 5 # Ungefähre Schätzung

# --- KEINE Options-Elemente mehr hier ---

clock = pygame.time.Clock()

# --- Musik Helper Funktion ---
def play_menu_music():
    global music_playing
    if mixer_initialized:
        print(f"DEBUG: Prüfe Existenz von: {music_file_path}")
        if os.path.exists(music_file_path):
            try:
                pygame.mixer.music.load(music_file_path)
                print(f"INFO: Musikdatei '{music_file_path}' geladen.")
                # Lautstärke anwenden (falls geändert)
                pygame.mixer.music.set_volume(current_settings.get("music_volume", 0.5))
                pygame.mixer.music.play(loops=-1)
                print("INFO: Musikwiedergabe gestartet (Looping).")
                music_playing = True
            except pygame.error as e_load_music:
                print(f"FEHLER: Musikdatei '{music_file_path}' konnte nicht geladen oder abgespielt werden: {e_load_music}")
                music_playing = False
        else:
            print(f"FEHLER: Musikdatei nicht gefunden unter: '{music_file_path}'")
            music_playing = False
    else:
        print("INFO: Mixer wurde nicht initialisiert, keine Musikwiedergabe.")
        music_playing = False

def stop_menu_music():
    global music_playing
    if mixer_initialized and music_playing:
        try:
            pygame.mixer.music.stop()
            print("INFO: Musik gestoppt.")
            music_playing = False
        except pygame.error as e_stop_music:
            print(f"WARNUNG: Fehler beim Stoppen der Musik: {e_stop_music}")

# --- Initiale Musik starten ---
music_playing = False # Wird in play_menu_music gesetzt
play_menu_music()
# --- Ende Musik Laden ---

# --- Spielzustand-Variable ---
current_screen_state = "main_menu" # Mögliche Zustände: "main_menu", "zipweed_game", "cockcrack_game", "calling_options", "main_game"

# --- Hauptschleife ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if current_screen_state == "main_menu":
                    running = False
                # ESC in Spielen/Optionen wird dort behandelt

        # --- MOUSEBUTTONDOWN Events (für Klicks) ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Linksklick
                # === HAUPTMENÜ Klicks ===
                if current_screen_state == "main_menu":
                    # Button 1: ZipWeed
                    if button1_rect.collidepoint(mouse_pos):
                        print("INFO: Starte ZipWeed Minispiel...")
                        if zipWeedGame:
                            current_screen_state = "zipweed_game"
                        else:
                            print("FEHLER: ZipWeed Modul nicht geladen.")
                    # Button 2: CockCrack
                    elif button2_rect.collidepoint(mouse_pos):
                        print("INFO: Starte CockCrack Minispiel...")
                        if cockCrackGame:
                             current_screen_state = "cockcrack_game"
                        else:
                            print("FEHLER: CockCrack Modul nicht geladen.")
                    # Button 3: Optionen
                    elif button3_rect.collidepoint(mouse_pos):
                        print("INFO: Öffne Optionen...")
                        previous_state = current_screen_state
                        current_screen_state = "calling_options" # Zwischenzustand
                        try:
                            returned_settings = options_menu_module.run_options_menu(
                                screen,
                                current_settings.copy(),
                                settings_file_path
                            )
                            if returned_settings is None:
                                running = False
                                print("INFO: Spiel wird nach Optionsmenü-Quit beendet.")
                            else:
                                current_settings = returned_settings
                                # Wende Lautstärke direkt an, falls geändert
                                if mixer_initialized:
                                    try:
                                        pygame.mixer.music.set_volume(current_settings["music_volume"])
                                        print(f"INFO: Musiklautstärke nach Optionen auf {current_settings['music_volume']:.2f} gesetzt.")
                                    except pygame.error as e_set_vol_opt:
                                        print(f"WARNUNG: Konnte Musiklautstärke nach Optionen nicht setzen: {e_set_vol_opt}")
                                print("INFO: Einstellungen nach Optionsmenü aktualisiert.")
                            current_screen_state = previous_state # Zurück zum Hauptmenü
                        except Exception as e_opt_run:
                            print(f"FEHLER beim Ausführen des Optionsmenüs: {e_opt_run}")
                            traceback.print_exc()
                            current_screen_state = previous_state # Im Fehlerfall zurück

                    # Button 4: Hauptspiel (NEU)
                    elif button4_rect.collidepoint(mouse_pos):
                        print(f"INFO: Versuche Hauptspiel zu starten: {game_script_path}")
                        if os.path.exists(game_script_path):
                            stop_menu_music() # Menümusik stoppen
                            print("INFO: Menümusik gestoppt. Starte Hauptspiel...")
                            try:
                                # Starte game.py als separaten Prozess
                                result = subprocess.run([sys.executable, game_script_path], check=True, capture_output=True, text=True)
                                print(f"INFO: Hauptspiel beendet. Exit Code: {result.returncode}")
                                # Optional: Output des Spiels anzeigen
                                # print("STDOUT:", result.stdout)
                                # print("STDERR:", result.stderr)

                            except FileNotFoundError:
                                print(f"FEHLER: Python Interpreter '{sys.executable}' oder Spiel-Skript '{game_script_path}' nicht gefunden.")
                            except subprocess.CalledProcessError as e:
                                print(f"FEHLER: Hauptspiel-Skript ist mit Fehlern beendet. Exit Code: {e.returncode}")
                                print("STDERR vom Spiel:", e.stderr)
                                print("STDOUT vom Spiel:", e.stdout)
                            except Exception as e_subproc:
                                print(f"FEHLER beim Ausführen des Hauptspiels via Subprocess: {e_subproc}")
                                traceback.print_exc()
                            finally:
                                # Nach Beendigung des Spiels (oder bei Fehler)
                                print("INFO: Hauptspiel beendet oder Fehler. Starte Menümusik neu...")
                                # Mixer neu initialisieren könnte nötig sein, falls game.py ihn beendet hat
                                try:
                                     pygame.mixer.quit() # Sicherstellen, dass alter Zustand weg ist
                                     pygame.mixer.init()
                                     mixer_initialized = True
                                except pygame.error as e_reinit:
                                     print(f"WARNUNG: Mixer Re-Initialisierung fehlgeschlagen: {e_reinit}")
                                     mixer_initialized = False
                                # Musik wieder starten
                                play_menu_music()
                                # Bildschirm neu zeichnen erzwingen (könnte durch Spiel verändert worden sein)
                                pygame.display.flip() # Sicherstellen, dass das Menü wieder da ist
                        else:
                            print(f"FEHLER: Hauptspiel-Skript nicht gefunden unter: {game_script_path}")

    # --- Zeichnen (abhängig vom Zustand) ---

    # Hintergrund zeichnen (immer, außer wenn ein Spiel läuft)
    if current_screen_state == "main_menu":
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(WHITE) # Fallback

    # === HAUPTMENÜ ZEICHNEN ===
    if current_screen_state == "main_menu":
        # Button 1 (ZipWeed)
        button1_color = GRAY if not button1_rect.collidepoint(mouse_pos) else DARK_GRAY
        pygame.draw.rect(screen, button1_color, button1_rect)
        pygame.draw.rect(screen, BLACK, button1_rect, 3)
        if text1_surface and button_font:
            text1_rect = text1_surface.get_rect(center=button1_rect.center)
            screen.blit(text1_surface, text1_rect.topleft)

        # Button 2 (CockCrack)
        button2_color = GRAY if not button2_rect.collidepoint(mouse_pos) else DARK_GRAY
        pygame.draw.rect(screen, button2_color, button2_rect)
        pygame.draw.rect(screen, BLACK, button2_rect, 3)
        if text2_surface and button_font:
            text2_rect = text2_surface.get_rect(center=button2_rect.center)
            screen.blit(text2_surface, text2_rect.topleft)

        # Button 3 (Optionen)
        button3_color = GRAY if not button3_rect.collidepoint(mouse_pos) else DARK_GRAY
        pygame.draw.rect(screen, button3_color, button3_rect)
        pygame.draw.rect(screen, BLACK, button3_rect, 3)
        if text3_surface and button_font:
            text3_rect = text3_surface.get_rect(center=button3_rect.center)
            screen.blit(text3_surface, text3_rect.topleft)

        # Button 4 (Hauptspiel) (NEU)
        button4_color = GRAY if not button4_rect.collidepoint(mouse_pos) else DARK_GRAY
        pygame.draw.rect(screen, button4_color, button4_rect)
        pygame.draw.rect(screen, BLACK, button4_rect, 3)
        if text4_surface and button_font:
            text4_rect = text4_surface.get_rect(center=button4_rect.center)
            screen.blit(text4_surface, text4_rect.topleft)

        # Statusanzeige (Inventar)
        if status_font:
            try:
                current_y = STATUS_Y
                texts_to_render = [
                    (f"Weed ({sorte}): {weed}", BLACK),
                    (f"Grips: {grips}", BLACK),
                    (f"Verpackt: {packed_weed_total}", GREEN),
                    ("", BLACK), # Leere Zeile
                    (f"{pillsName}: {pills}", BLACK),
                    (f"{liquidName}: {liquid}", BLACK),
                    (f"Crack: {Crack}", RED)
                ]
                for text, color in texts_to_render:
                    if text:
                        text_surf = status_font.render(text, True, color)
                        screen.blit(text_surf, (STATUS_X, current_y))
                    current_y += STATUS_LINE_HEIGHT
            except Exception as e_render_status:
                print(f"FEHLER beim Rendern des Status-Textes: {e_render_status}")
                # Optional: Kleine Fehlermeldung auf dem Schirm
                if status_font:
                     try:
                         error_surf = status_font.render("Fehler Status", True, RED)
                         screen.blit(error_surf, (STATUS_X, STATUS_Y))
                     except: pass # Wenn selbst das fehlschlägt

    # === MINISPIELE AUSFÜHREN / ZEICHNEN ===
    elif current_screen_state == "zipweed_game":
        stop_menu_music() # Stoppe Menümusik für Minispiel
        try:
            result_tuple = zipWeedGame.run_zip_weed_game(screen, weed, grips, sorte, current_settings)
            if result_tuple is not None:
                try:
                    remaining_weed, remaining_grips, packed_count, returned_sorte = result_tuple
                    weed = remaining_weed
                    grips = remaining_grips
                    packed_weed_total += packed_count
                    print(f"DEBUG: Inventar nach ZipWeed aktualisiert: Weed={weed}, Grips={grips}, Gesamt Verpackt={packed_weed_total}")
                except (TypeError, ValueError) as e_unpack_zw:
                    print(f"FEHLER: Rückgabewert von ZipWeed falsch: {e_unpack_zw}")
            else:
                 print("WARNUNG: ZipWeed hat kein Ergebnis (None) zurückgegeben!")
            print("INFO: Zurück im Hauptmenü nach ZipWeed.")
            current_screen_state = "main_menu"
            play_menu_music() # Starte Menümusik wieder
        except AttributeError as e_attr_zw:
            print(f"FEHLER (AttributeError ZipWeed): {e_attr_zw} - Funktion 'run_zip_weed_game' nicht gefunden?")
            traceback.print_exc()
            current_screen_state = "main_menu"
            play_menu_music()
        except TypeError as e_type_zw:
             print(f"FEHLER (TypeError ZipWeed): {e_type_zw} - Falsche Argumente übergeben?")
             traceback.print_exc()
             current_screen_state = "main_menu"
             play_menu_music()
        except Exception as e_game_zw:
            print(f"FEHLER während ZipWeed Ausführung: {e_game_zw}")
            traceback.print_exc()
            current_screen_state = "main_menu"
            play_menu_music()

    elif current_screen_state == "cockcrack_game":
        stop_menu_music() # Stoppe Menümusik für Minispiel
        try:
            function_to_call_cc = cockCrackGame.run_cock_crack_game
            if callable(function_to_call_cc):
                result_cc = function_to_call_cc(screen, pills, liquid, Crack, liquidName, pillsName, current_settings)
                if result_cc is not None:
                    try:
                        remaining_pills_cc, remaining_liquid_cc, new_crack_total_cc = result_cc
                        pills = remaining_pills_cc
                        liquid = remaining_liquid_cc
                        Crack = new_crack_total_cc
                        print(f"DEBUG: Inventar nach CockCrack aktualisiert: Pills={pills}, Liquid={liquid}, Crack={Crack}")
                    except (TypeError, ValueError) as e_unpack_cc:
                        print(f"FEHLER: Rückgabewert von CockCrack falsch: {e_unpack_cc}")
                else:
                    print("WARNUNG: CockCrack hat kein Ergebnis (None) zurückgegeben!")
                print("INFO: Zurück im Hauptmenü nach CockCrack.")
                current_screen_state = "main_menu"
                play_menu_music() # Starte Menümusik wieder
            else:
                print(f"FEHLER: 'run_cock_crack_game' ist nicht aufrufbar!")
                current_screen_state = "main_menu"
                play_menu_music()
        except AttributeError as e_attr_cc:
            print(f"FEHLER (AttributeError CockCrack): {e_attr_cc} - Funktion nicht gefunden?")
            traceback.print_exc()
            current_screen_state = "main_menu"
            play_menu_music()
        except TypeError as e_type_cc:
            print(f"FEHLER (TypeError CockCrack): {e_type_cc} - Falsche Argumente?")
            traceback.print_exc()
            current_screen_state = "main_menu"
            play_menu_music()
        except Exception as e_game_cc:
            print(f"FEHLER während CockCrack Ausführung: {e_game_cc}")
            traceback.print_exc()
            current_screen_state = "main_menu"
            play_menu_music()

    # --- Bildschirm aktualisieren (nur wenn nicht gerade ein Subprozess läuft) ---
    if current_screen_state != "main_game": # Verhindert Flackern, während Spiel läuft
         pygame.display.flip()

    # --- Framerate begrenzen ---
    clock.tick(60)

# --- Aufräumen nach der Hauptschleife ---
stop_menu_music() # Stoppe Musik endgültig

print("INFO: Hauptmenü wird beendet. Pygame wird heruntergefahren.")
pygame.quit()
sys.exit()