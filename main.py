# -*- coding: utf-8 -*-
import pygame
import sys
import os
import traceback
import json # Besser für strukturierte Einstellungen als reines Textfile

# --- Pfad zum Skriptverzeichnis ermitteln ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"DEBUG: Skriptverzeichnis ermittelt: {script_dir}")
except NameError:
    script_dir = os.getcwd()
    print(f"WARNUNG: __file__ nicht gefunden, nutze aktuelles Arbeitsverzeichnis: {script_dir}")

# --- Pfad zur Musikdatei und Einstellungsdatei ---
music_file_path = os.path.join(script_dir, "data", "sounds", "background", "menu_background_music.wav")
settings_dir = os.path.join(script_dir, "data", "settings")
settings_file_path = os.path.join(settings_dir, "settings.json") # Geändert zu JSON
print(f"DEBUG: Vollständiger Pfad zur Musikdatei wird sein: {music_file_path}")
print(f"DEBUG: Vollständiger Pfad zur Einstellungsdatei wird sein: {settings_file_path}")

# --- Standardeinstellungen ---
DEFAULT_SETTINGS = {
    "music_volume": 0.7,  # Standard Musiklautstärke (0.0 bis 1.0)
    "sfx_volume": 0.8,    # Standard Soundeffekt-Lautstärke (Platzhalter)
    "master_volume": 1.0  # Standard Gesamtlautstärke (Platzhalter)
}
current_settings = DEFAULT_SETTINGS.copy() # Aktuelle Einstellungen, starten mit Defaults

# --- Funktion zum Laden der Einstellungen ---
def load_settings(filepath):
    global current_settings
    try:
        # Sicherstellen, dass der Ordner existiert (nur für den Leseversuch, nicht kritisch)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                loaded_data = json.load(f)
                # Überprüfe, ob geladene Daten gültige Keys haben und aktualisiere
                valid_settings = {}
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key in loaded_data and isinstance(loaded_data[key], (int, float)):
                         # Clamping: Stelle sicher, dass Werte im gültigen Bereich sind
                         valid_settings[key] = max(0.0, min(1.0, float(loaded_data[key])))
                    else:
                         print(f"WARNUNG: Ungültiger oder fehlender Wert für '{key}' in {filepath}. Nutze Standardwert {default_value}.")
                         valid_settings[key] = default_value
                current_settings = valid_settings
                print(f"INFO: Einstellungen geladen aus {filepath}: {current_settings}")
        else:
            print(f"INFO: Einstellungsdatei {filepath} nicht gefunden. Nutze Standardeinstellungen und erstelle Datei beim Speichern.")
            current_settings = DEFAULT_SETTINGS.copy()
            # Optional: Datei direkt mit Defaults erstellen? Besser beim ersten Speichern.
            # save_settings(filepath, current_settings)
    except json.JSONDecodeError:
        print(f"FEHLER: Einstellungsdatei {filepath} ist korrupt (ungültiges JSON). Nutze Standardeinstellungen.")
        current_settings = DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"FEHLER beim Laden der Einstellungen aus {filepath}: {e}")
        traceback.print_exc()
        current_settings = DEFAULT_SETTINGS.copy() # Fallback zu Defaults

# --- Funktion zum Speichern der Einstellungen ---
def save_settings(filepath, settings_dict):
    try:
        # Sicherstellen, dass der Ordner existiert, bevor geschrieben wird
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(settings_dict, f, indent=4) # indent=4 für Lesbarkeit
        print(f"INFO: Einstellungen gespeichert in {filepath}: {settings_dict}")
    except Exception as e:
        print(f"FEHLER beim Speichern der Einstellungen in {filepath}: {e}")
        traceback.print_exc()

# --- Einstellungen laden BEVOR Pygame initialisiert wird (vor allem der Mixer) ---
load_settings(settings_file_path)
# ------------------------------------

# --- Android Immersive Mode & Platform Detection --- ### WICHTIG ###
# (Code unverändert)
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
# (Code unverändert)
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

# --- Mixer initialisieren NACH Pygame Init ---
mixer_initialized = False
try:
    pygame.mixer.init()
    print("INFO: Pygame Mixer erfolgreich initialisiert.")
    mixer_initialized = True
    # --- LAUTSTÄRKE ANWENDEN ---
    try:
        pygame.mixer.music.set_volume(current_settings["music_volume"])
        print(f"INFO: Musiklautstärke auf {current_settings['music_volume']:.2f} gesetzt.")
        # Hinweis: SFX und Master Volume erfordern komplexere Handhabung
        # z.B. individuelle Lautstärke für jeden Sound setzen oder Kanäle nutzen.
        # Hier setzen wir erstmal nur die Musiklautstärke.
    except pygame.error as e_set_vol:
        print(f"WARNUNG: Konnte initiale Musiklautstärke nicht setzen: {e_set_vol}")
    # --- Ende Lautstärke anwenden ---
except pygame.error as e_mixer:
    print(f"FEHLER: Pygame Mixer konnte nicht initialisiert werden: {e_mixer}")
    print(">>> Musik- und Soundwiedergabe wird nicht funktionieren.")
# --- Ende Mixer Initialisierung ---


# Bildschirmgröße
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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

pygame.display.set_caption("Hauptmenü - DrugsDealerGame")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
GREEN = (0, 128, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200) # Für Slider-Handles

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

# --- Button Definition (Proportional) ---
BUTTON_WIDTH_PERCENT = 0.40
BUTTON_HEIGHT_PERCENT = 0.10 # Etwas kleiner, um Platz für 3. Button zu machen
BUTTON_SPACING_PERCENT = 0.04 # Etwas weniger Abstand
FONT_SIZE_REF_H = 600.0
BASE_FONT_SIZE = 35 # Etwas kleiner

button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_spacing = int(SCREEN_HEIGHT * BUTTON_SPACING_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2

total_buttons_height = 3 * button_height + 2 * button_spacing # Höhe für DREI Buttons
# Zentriere die Buttons vertikal
button1_y = (SCREEN_HEIGHT - total_buttons_height) // 2
button2_y = button1_y + button_height + button_spacing
button3_y = button2_y + button_height + button_spacing # Y für den Optionen Button

button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height) # ZipWeed
button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height) # CockCrack
button3_rect = pygame.Rect(button_x, button3_y, button_width, button_height) # Optionen NEU

# Proportionale Schriftgröße Button
button_font_size = max(15, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text1_surface = None
text2_surface = None
text3_surface = None # Für Optionen Button
button1_text = "Starte ZipWeed Minispiel"
button2_text = "Starte CockCrack Minispiel"
button3_text = "Optionen" # NEU

try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    if button_font:
        text1_surface = button_font.render(button1_text, True, BLACK)
        text2_surface = button_font.render(button2_text, True, BLACK)
        text3_surface = button_font.render(button3_text, True, BLACK) # Optionen Text rendern
    else:
        raise Exception("SysFont lieferte None")
except Exception as e_font:
    print(f"WARNUNG beim Laden der Button-Schriftart 'arial': {e_font}. Nutze Fallback.")
    try:
        button_font = pygame.font.Font(None, int(button_font_size * 1.1))
        if button_font:
             text1_surface = button_font.render(button1_text, True, BLACK)
             text2_surface = button_font.render(button2_text, True, BLACK)
             text3_surface = button_font.render(button3_text, True, BLACK) # Optionen Text rendern (Fallback)
        else:
             raise Exception("Fallback Font lieferte None")
    except Exception as e_font_fallback:
        print(f"FEHLER: Konnte auch Fallback-Button-Schriftart nicht laden: {e_font_fallback}")

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
        status_font = pygame.font.Font(None, status_font_size)
        if not status_font: raise Exception("Fallback Font lieferte None")
        print(f"DEBUG: Fallback-Status-Schriftart geladen (Größe {status_font_size}).")
    except Exception as e_sfont_fallback:
        print(f"FEHLER: Konnte auch Fallback-Status-Schriftart nicht laden: {e_sfont_fallback}")

STATUS_X = 15
STATUS_Y = 15
STATUS_LINE_HEIGHT = 0
if status_font:
    STATUS_LINE_HEIGHT = status_font.get_height() + 5
else:
    STATUS_LINE_HEIGHT = status_font_size + 5

# --- NEU: Elemente für den Optionsbildschirm ---
OPTIONS_TITLE_FONT_SIZE = 40
OPTIONS_ITEM_FONT_SIZE = 25
SLIDER_WIDTH_PERCENT = 0.6
SLIDER_HEIGHT = 20
SLIDER_HANDLE_WIDTH = 10
SLIDER_HANDLE_HEIGHT = 30
OPTIONS_BACK_BUTTON_WIDTH_PERCENT = 0.3
OPTIONS_BACK_BUTTON_HEIGHT_PERCENT = 0.08

options_title_font = None
options_item_font = None
options_back_button_font = None

try:
    options_title_font = pygame.font.SysFont("arial", OPTIONS_TITLE_FONT_SIZE)
    options_item_font = pygame.font.SysFont("arial", OPTIONS_ITEM_FONT_SIZE)
    options_back_button_font = pygame.font.SysFont("arial", int(button_font_size * 0.8)) # Etwas kleiner als Hauptbuttons
    if not options_title_font or not options_item_font or not options_back_button_font:
        raise Exception("Einige Options-Schriftarten konnten nicht geladen werden.")
except Exception as e_opt_font:
    print(f"WARNUNG: Konnte Options-Schriftarten nicht laden: {e_opt_font}. Nutze Fallback.")
    try:
        options_title_font = pygame.font.Font(None, OPTIONS_TITLE_FONT_SIZE + 5) # Fallback oft größer
        options_item_font = pygame.font.Font(None, OPTIONS_ITEM_FONT_SIZE + 5)
        options_back_button_font = pygame.font.Font(None, int(button_font_size * 0.9))
        if not options_title_font or not options_item_font or not options_back_button_font:
            raise Exception("Fallback Options-Schriftarten fehlgeschlagen.")
    except Exception as e_opt_font_fb:
        print(f"FEHLER: Konnte auch Fallback-Options-Schriftarten nicht laden: {e_opt_font_fb}")
        # Kritisch? Setzen wir sie auf None, Zeichnen wird übersprungen
        options_title_font = options_item_font = options_back_button_font = None


# Slider-Definitionen (werden dynamisch in der Options-Schleife berechnet)
slider_music_rect = None
slider_sfx_rect = None
slider_master_rect = None
options_back_button_rect = None
active_slider = None # Welcher Slider gerade gezogen wird

# --- Ende Options-Elemente ---

clock = pygame.time.Clock()

# --- Musik laden und abspielen ---
music_playing = False
if mixer_initialized:
    print(f"DEBUG: Prüfe Existenz von: {music_file_path}")
    if os.path.exists(music_file_path):
        try:
            pygame.mixer.music.load(music_file_path)
            print(f"INFO: Musikdatei '{music_file_path}' geladen.")
            # Lautstärke wurde bereits vorher gesetzt!
            pygame.mixer.music.play(loops=-1)
            print("INFO: Musikwiedergabe gestartet (Looping).")
            music_playing = True
        except pygame.error as e_load_music:
            print(f"FEHLER: Musikdatei '{music_file_path}' konnte nicht geladen oder abgespielt werden: {e_load_music}")
            print(">>> Stellen Sie sicher, dass die WAV-Datei nicht korrupt ist und vom Mixer unterstützt wird.")
    else:
        print(f"FEHLER: Musikdatei nicht gefunden unter: '{music_file_path}'")
        print(f">>> Aktuelles Arbeitsverzeichnis: {os.getcwd()}")
        print(f">>> Verzeichnis des Skripts (__file__): {script_dir}")
        print(">>> Überprüfe: Pfad, Existenz der Datei, Buildozer-Konfiguration.")
else:
    print("INFO: Mixer wurde nicht initialisiert, keine Musikwiedergabe.")
# --- Ende Musik Laden ---

# --- NEU: Spielzustand-Variable ---
current_screen_state = "main_menu" # Mögliche Zustände: "main_menu", "options_menu", "zipweed_game", "cockcrack_game"

# --- Hauptschleife ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed() # Linksklick: mouse_pressed[0]

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC schließt Optionen oder das Spiel
                if current_screen_state == "options_menu":
                    current_screen_state = "main_menu"
                    # Einstellungen speichern beim Verlassen der Optionen
                    save_settings(settings_file_path, current_settings)
                else:
                    running = False # Im Hauptmenü beendet ESC das Spiel

        # --- MOUSEBUTTONDOWN Events (für Klicks) ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Linksklick
                # === HAUPTMENÜ Klicks ===
                if current_screen_state == "main_menu":
                    # Button 1: ZipWeed
                    if button1_rect.collidepoint(mouse_pos):
                        print("INFO: Starte ZipWeed Minispiel...")
                        if zipWeedGame:
                            current_screen_state = "zipweed_game" # Zustand ändern
                            # Musik läuft weiter! Minispiel muss eigenen Sound verwalten
                        else:
                            print("FEHLER: ZipWeed Modul nicht geladen.")

                    # Button 2: CockCrack
                    elif button2_rect.collidepoint(mouse_pos):
                        print("INFO: Starte CockCrack Minispiel...")
                        if cockCrackGame:
                             current_screen_state = "cockcrack_game" # Zustand ändern
                             # Musik läuft weiter!
                        else:
                            print("FEHLER: CockCrack Modul nicht geladen.")

                    # Button 3: Optionen NEU
                    elif button3_rect.collidepoint(mouse_pos):
                        print("INFO: Öffne Optionen...")
                        current_screen_state = "options_menu" # Zustand ändern
                        active_slider = None # Sicherstellen, dass kein Slider aktiv ist

                # === OPTIONEN Klicks ===
                elif current_screen_state == "options_menu":
                    # Zurück-Button in Optionen
                    if options_back_button_rect and options_back_button_rect.collidepoint(mouse_pos):
                        current_screen_state = "main_menu"
                        # Einstellungen speichern beim Verlassen der Optionen
                        save_settings(settings_file_path, current_settings)
                    # Slider-Klick (Start des Ziehens)
                    elif slider_music_rect and slider_music_rect.collidepoint(mouse_pos):
                        active_slider = "music"
                    elif slider_sfx_rect and slider_sfx_rect.collidepoint(mouse_pos):
                        active_slider = "sfx"
                    elif slider_master_rect and slider_master_rect.collidepoint(mouse_pos):
                         active_slider = "master"

                    # Wenn auf einen Slider geklickt wurde, direkt Lautstärke anpassen
                    if active_slider:
                        slider_rect = None
                        if active_slider == "music": slider_rect = slider_music_rect
                        elif active_slider == "sfx": slider_rect = slider_sfx_rect
                        elif active_slider == "master": slider_rect = slider_master_rect

                        if slider_rect:
                             # Berechne neue Lautstärke basierend auf Klickposition
                             relative_x = mouse_pos[0] - slider_rect.left
                             new_volume = max(0.0, min(1.0, relative_x / slider_rect.width))
                             current_settings[f"{active_slider}_volume"] = new_volume
                             print(f"DEBUG: Slider '{active_slider}' Klick/Update auf {new_volume:.2f}")
                             # Musiklautstärke direkt anwenden
                             if active_slider == "music" and mixer_initialized:
                                 try:
                                     pygame.mixer.music.set_volume(new_volume)
                                 except pygame.error as e_set_vol:
                                     print(f"WARNUNG: Konnte Musiklautstärke nicht setzen: {e_set_vol}")
                             # Hier Logik für SFX/Master hinzufügen, falls implementiert

        # --- MOUSEBUTTONUP Events (für Loslassen) ---
        if event.type == pygame.MOUSEBUTTONUP:
             if event.button == 1:
                 # Beende das Ziehen des Sliders
                 if current_screen_state == "options_menu" and active_slider:
                     print(f"DEBUG: Slider '{active_slider}' losgelassen.")
                     active_slider = None


    # --- Slider Handling (während Maus gedrückt gehalten wird) ---
    if current_screen_state == "options_menu" and active_slider and mouse_pressed[0]:
        slider_rect = None
        if active_slider == "music": slider_rect = slider_music_rect
        elif active_slider == "sfx": slider_rect = slider_sfx_rect
        elif active_slider == "master": slider_rect = slider_master_rect

        if slider_rect:
            # Berechne neue Lautstärke basierend auf Mausposition
            relative_x = mouse_pos[0] - slider_rect.left
            new_volume = max(0.0, min(1.0, relative_x / slider_rect.width))
            current_settings[f"{active_slider}_volume"] = new_volume
            # print(f"DEBUG: Slider '{active_slider}' Drag Update auf {new_volume:.2f}") # Optional: für Debugging
            # Musiklautstärke direkt anwenden
            if active_slider == "music" and mixer_initialized:
                try:
                    pygame.mixer.music.set_volume(new_volume)
                except pygame.error as e_set_vol:
                    print(f"WARNUNG: Konnte Musiklautstärke nicht setzen: {e_set_vol}")
            # Hier Logik für SFX/Master hinzufügen

    # --- Zeichnen (abhängig vom Zustand) ---
    screen.fill(WHITE) # Hintergrund immer löschen

    # === HAUPTMENÜ ZEICHNEN ===
    if current_screen_state == "main_menu":
        # --- Buttons zeichnen ---
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

        # Button 3 (Optionen) NEU
        button3_color = GRAY if not button3_rect.collidepoint(mouse_pos) else DARK_GRAY
        pygame.draw.rect(screen, button3_color, button3_rect)
        pygame.draw.rect(screen, BLACK, button3_rect, 3)
        if text3_surface and button_font:
            text3_rect = text3_surface.get_rect(center=button3_rect.center)
            screen.blit(text3_surface, text3_rect.topleft)

        # --- Statusanzeige (Inventar) zeichnen ---
        if status_font:
            try:
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
                    if text:
                        text_surf = status_font.render(text, True, color)
                        screen.blit(text_surf, (STATUS_X, current_y))
                    current_y += STATUS_LINE_HEIGHT
            except Exception as e_render_status:
                print(f"FEHLER beim Rendern des Status-Textes: {e_render_status}")
                try:
                    error_surf = status_font.render("Fehler Status Anzeige", True, RED)
                    screen.blit(error_surf, (STATUS_X, STATUS_Y))
                except: pass
        else:
            pass # Kein Status-Font

    # === OPTIONEN ZEICHNEN ===
    elif current_screen_state == "options_menu":
        if options_title_font and options_item_font and options_back_button_font:
            try:
                # Titel
                title_surf = options_title_font.render("Optionen", True, BLACK)
                title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.1))
                screen.blit(title_surf, title_rect)

                # Slider-Bereich definieren
                slider_width = int(SCREEN_WIDTH * SLIDER_WIDTH_PERCENT)
                slider_x = (SCREEN_WIDTH - slider_width) // 2
                slider_start_y = SCREEN_HEIGHT * 0.25
                slider_spacing = SCREEN_HEIGHT * 0.15

                # Slider für Musiklautstärke
                slider_music_y = slider_start_y
                slider_music_rect = pygame.Rect(slider_x, slider_music_y, slider_width, SLIDER_HEIGHT)
                text_music_surf = options_item_font.render(f"Musik: {int(current_settings['music_volume']*100)}%", True, BLACK)
                text_music_rect = text_music_surf.get_rect(midright=(slider_x - 20, slider_music_rect.centery))
                screen.blit(text_music_surf, text_music_rect)
                pygame.draw.rect(screen, GRAY, slider_music_rect, border_radius=5) # Slider Hintergrund
                handle_music_x = slider_music_rect.left + int(slider_music_rect.width * current_settings['music_volume'])
                handle_music_rect = pygame.Rect(0, 0, SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT)
                handle_music_rect.center = (handle_music_x, slider_music_rect.centery)
                pygame.draw.rect(screen, BLUE, handle_music_rect, border_radius=3) # Slider Griff

                # Slider für SFX Lautstärke (Platzhalter-Logik)
                slider_sfx_y = slider_start_y + slider_spacing
                slider_sfx_rect = pygame.Rect(slider_x, slider_sfx_y, slider_width, SLIDER_HEIGHT)
                text_sfx_surf = options_item_font.render(f"Effekte: {int(current_settings['sfx_volume']*100)}%", True, BLACK)
                text_sfx_rect = text_sfx_surf.get_rect(midright=(slider_x - 20, slider_sfx_rect.centery))
                screen.blit(text_sfx_surf, text_sfx_rect)
                pygame.draw.rect(screen, GRAY, slider_sfx_rect, border_radius=5)
                handle_sfx_x = slider_sfx_rect.left + int(slider_sfx_rect.width * current_settings['sfx_volume'])
                handle_sfx_rect = pygame.Rect(0, 0, SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT)
                handle_sfx_rect.center = (handle_sfx_x, slider_sfx_rect.centery)
                pygame.draw.rect(screen, BLUE, handle_sfx_rect, border_radius=3)

                # Slider für Master Lautstärke (Platzhalter-Logik)
                slider_master_y = slider_start_y + 2 * slider_spacing
                slider_master_rect = pygame.Rect(slider_x, slider_master_y, slider_width, SLIDER_HEIGHT)
                text_master_surf = options_item_font.render(f"Gesamt: {int(current_settings['master_volume']*100)}%", True, BLACK)
                text_master_rect = text_master_surf.get_rect(midright=(slider_x - 20, slider_master_rect.centery))
                screen.blit(text_master_surf, text_master_rect)
                pygame.draw.rect(screen, GRAY, slider_master_rect, border_radius=5)
                handle_master_x = slider_master_rect.left + int(slider_master_rect.width * current_settings['master_volume'])
                handle_master_rect = pygame.Rect(0, 0, SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT)
                handle_master_rect.center = (handle_master_x, slider_master_rect.centery)
                pygame.draw.rect(screen, BLUE, handle_master_rect, border_radius=3)

                # Zurück-Button
                back_button_width = int(SCREEN_WIDTH * OPTIONS_BACK_BUTTON_WIDTH_PERCENT)
                back_button_height = int(SCREEN_HEIGHT * OPTIONS_BACK_BUTTON_HEIGHT_PERCENT)
                back_button_x = (SCREEN_WIDTH - back_button_width) // 2
                back_button_y = SCREEN_HEIGHT * 0.85
                options_back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
                back_button_color = GRAY if not options_back_button_rect.collidepoint(mouse_pos) else DARK_GRAY
                pygame.draw.rect(screen, back_button_color, options_back_button_rect, border_radius=8)
                pygame.draw.rect(screen, BLACK, options_back_button_rect, 2, border_radius=8)
                back_text_surf = options_back_button_font.render("Zurück & Speichern", True, BLACK)
                back_text_rect = back_text_surf.get_rect(center=options_back_button_rect.center)
                screen.blit(back_text_surf, back_text_rect)

            except Exception as e_render_options:
                print(f"FEHLER beim Rendern des Optionsbildschirms: {e_render_options}")
                # Fallback: Einfache Fehlermeldung anzeigen
                if status_font:
                    error_surf = status_font.render("Fehler beim Laden der Optionen!", True, RED)
                    screen.blit(error_surf, (20, 20))

        else:
             # Fallback, wenn Schriften nicht geladen werden konnten
             if status_font:
                 error_surf = status_font.render("Fehler: Options-Schriftarten nicht geladen!", True, RED)
                 screen.blit(error_surf, (20, 20))
             # Minimaler Zurück-Button ohne Text
             back_button_width = int(SCREEN_WIDTH * OPTIONS_BACK_BUTTON_WIDTH_PERCENT)
             back_button_height = int(SCREEN_HEIGHT * OPTIONS_BACK_BUTTON_HEIGHT_PERCENT)
             back_button_x = (SCREEN_WIDTH - back_button_width) // 2
             back_button_y = SCREEN_HEIGHT * 0.85
             options_back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
             back_button_color = GRAY if not options_back_button_rect.collidepoint(mouse_pos) else DARK_GRAY
             pygame.draw.rect(screen, back_button_color, options_back_button_rect, border_radius=8)
             pygame.draw.rect(screen, BLACK, options_back_button_rect, 2, border_radius=8)


    # === ZIPWEED MINISPIEL AUSFÜHREN ===
    elif current_screen_state == "zipweed_game":
        try:
            # WICHTIG: Minispiel muss den Screen übernehmen und bei Beendigung
            # einen Wert zurückgeben (oder None/False), damit wir zurückwechseln können.
            # Die Funktion sollte idealerweise selbst die Events verarbeiten.
            print(f"DEBUG: Rufe zipWeedGame.run_zip_weed_game mit screen, weed={weed}, grips={grips}, sorte='{sorte}' auf")
            result_tuple = zipWeedGame.run_zip_weed_game(screen, weed, grips, sorte, current_settings)

            # Verarbeitung des Ergebnisses NACH Rückkehr vom Minispiel
            if result_tuple is not None: # Minispiel wurde normal beendet
                try:
                    remaining_weed, remaining_grips, packed_count, returned_sorte = result_tuple
                    print(f"DEBUG: ZipWeed Ergebnis: Weed={remaining_weed}, Grips={remaining_grips}, Packed={packed_count}, Sorte='{returned_sorte}'")
                    weed = remaining_weed
                    grips = remaining_grips
                    packed_weed_total += packed_count
                    # sorte = returned_sorte # Optional
                    print(f"DEBUG: Inventar aktualisiert: Weed={weed}, Grips={grips}, Gesamt Verpackt={packed_weed_total}")
                except (TypeError, ValueError) as e_unpack_zw:
                    print(f"FEHLER: Rückgabewert von ZipWeed falsch: {e_unpack_zw}")
                    print(f">>> Erhalten: {result_tuple}. Erwartet: (weed, grips, packed, sorte)")
            else:
                # Funktion gab None zurück (z.B. durch ESC im Minispiel?)
                print("WARNUNG: ZipWeed hat kein Ergebnis (None) zurückgegeben!")

            print("INFO: Zurück im Hauptmenü nach ZipWeed.")
            current_screen_state = "main_menu" # Zurück zum Menü

        except AttributeError as e_attr_zw:
            print(f"FEHLER (AttributeError ZipWeed): {e_attr_zw}")
            print(">>> Funktion 'run_zip_weed_game' nicht gefunden.")
            traceback.print_exc()
            current_screen_state = "main_menu" # Zurück zum Menü bei Fehler
        except TypeError as e_type_zw:
            print(f"FEHLER (TypeError ZipWeed): {e_type_zw}")
            print(">>> Funktion mit falschen Argumenten aufgerufen?")
            traceback.print_exc()
            current_screen_state = "main_menu" # Zurück zum Menü
        except Exception as e_game_zw:
            print(f"FEHLER während ZipWeed Ausführung: {e_game_zw}")
            traceback.print_exc()
            current_screen_state = "main_menu" # Zurück zum Menü

    # === COCKCRACK MINISPIEL AUSFÜHREN ===
    elif current_screen_state == "cockcrack_game":
        try:
            print(f"DEBUG: Rufe cockCrackGame.run_cock_crack_game mit screen, pills={pills}, liquid={liquid}, Crack={Crack}, liquidName='{liquidName}', pillsName='{pillsName}' auf")
            function_to_call_cc = cockCrackGame.run_cock_crack_game

            if callable(function_to_call_cc):
                result_cc = function_to_call_cc(screen, pills, liquid, Crack, liquidName, pillsName)

                if result_cc is not None:
                    try:
                        remaining_pills_cc, remaining_liquid_cc, new_crack_total_cc = result_cc
                        print(f"DEBUG: CockCrack Ergebnis: Pills={remaining_pills_cc}, Liquid={remaining_liquid_cc}, Crack={new_crack_total_cc}")
                        pills = remaining_pills_cc
                        liquid = remaining_liquid_cc
                        Crack = new_crack_total_cc
                        print(f"DEBUG: Inventar aktualisiert: Pills={pills}, Liquid={liquid}, Crack={Crack}")
                    except (TypeError, ValueError) as e_unpack_cc:
                        print(f"FEHLER: Rückgabewert von CockCrack falsch: {e_unpack_cc}")
                        print(f">>> Erhalten: {result_cc}. Erwartet: (pills, liquid, crack)")
                else:
                    print("WARNUNG: CockCrack hat kein Ergebnis (None) zurückgegeben!")

                print("INFO: Zurück im Hauptmenü nach CockCrack.")
                current_screen_state = "main_menu" # Zurück zum Menü
            else:
                print(f"FEHLER: 'run_cock_crack_game' ist nicht aufrufbar!")
                current_screen_state = "main_menu" # Zurück zum Menü

        except AttributeError as e_attr_cc:
             print(f"FEHLER (AttributeError CockCrack): {e_attr_cc}")
             print(f">>> Funktion 'run_cock_crack_game' nicht gefunden.")
             traceback.print_exc()
             current_screen_state = "main_menu"
        except TypeError as e_type_cc:
             print(f"FEHLER (TypeError CockCrack): {e_type_cc}")
             print(">>> Funktion mit falschen Argumenten aufgerufen?")
             traceback.print_exc()
             current_screen_state = "main_menu"
        except Exception as e_game_cc:
             print(f"FEHLER während CockCrack Ausführung: {e_game_cc}")
             traceback.print_exc()
             current_screen_state = "main_menu"

    # --- Bildschirm aktualisieren ---
    pygame.display.flip()

    # --- Framerate begrenzen ---
    clock.tick(60)

# --- Aufräumen nach der Hauptschleife ---

# Letztes Speichern der Einstellungen (falls Änderungen im Optionsmenü nicht gespeichert wurden)
# Normalerweise sollte das beim Verlassen der Optionen geschehen sein.
# save_settings(settings_file_path, current_settings) # Überflüssig, wenn Speichern bei "Zurück" erfolgt.

if mixer_initialized and music_playing:
    try:
        pygame.mixer.music.stop()
        print("INFO: Musik gestoppt.")
    except pygame.error as e_stop_music:
        print(f"WARNUNG: Fehler beim Stoppen der Musik: {e_stop_music}")

print("INFO: Hauptmenü wird beendet. Pygame wird heruntergefahren.")
pygame.quit()
sys.exit()