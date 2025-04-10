# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os
import traceback
import time
import random

# --- KORREKTER IMPORT FÜR TEIL 3 (Robustere Methode) ---
cockCrackpart3Game = None
cockCrackpart3_imported = False
try:
    # 1. Versuche relativen Import (für Paketstruktur)
    # Der Punkt '.' bedeutet: Suche im selben Verzeichnis wie diese Datei (cockCrackpart2.py)
    # Achte auf die korrekte Groß-/Kleinschreibung des Dateinamens 'cockCrackpart3.py'
    from . import cockCrackpart3 as ccp3_rel
    cockCrackpart3Game = ccp3_rel
    cockCrackpart3_imported = True
    print("DEBUG (cockCrack V4 Korr): Modul cockCrackpart3 relativ importiert.")
except ImportError:
    print("INFO (cockCrack V4 Korr): Relativer Import von cockCrackpart3 fehlgeschlagen. Versuche absoluten Import...")
    try:
        # 2. Fallback: Versuche absoluten Import (für Standalone oder flachere Struktur)
        import cockCrackpart3 as ccp3_abs # Stelle sicher, dass cockCrackpart3.py im Python-Pfad ist oder im selben Ordner
        cockCrackpart3Game = ccp3_abs
        cockCrackpart3_imported = True
        print("DEBUG (cockCrack V4 Korr): Modul cockCrackpart3 absolut importiert.")
    except ImportError as e_import_abs:
        print(f"FEHLER: Konnte cockCrackpart3 weder relativ noch absolut importieren: {e_import_abs}")
        print(">>> Stelle sicher, dass 'cockCrackpart3.py' im selben Ordner wie dieses Skript liegt ODER im Python-Pfad.")
        # cockCrackpart3Game bleibt None, cockCrackpart3_imported bleibt False
# --- Ende Import Korrektur ---


# --- Konstanten und Farben ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)  # Fallback Farbe Rot
BLUE = (0, 0, 255) # Fallback Farbe Blau
GREEN = (0, 255, 0) # Fallback Farbe Grün
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)

# --- Dateinamen für Bilder ---
background_image_filename = "laborTable.png"
big_blue_circle_filename = "glassTopDown.png"
small_red_circle_filename = "small_red_circle.png" # Stelle sicher, dass diese Datei existiert!
green_circle_image_filename = "tafelgan.png" # Wird als grüne Kreise verwendet

# --- Hauptfunktion des Spiels (Mit Debug-Print für Fortschritt) ---
def run_cock_crack_game(screen_surface, start_pills, start_liquid, start_crack, liquid_id, pills_id):
    """ Führt das CockCrack Minispiel Teil 2 aus.
        Bei Erfolg (100%) wird cockCrackpart3 aufgerufen und 1 zurückgegeben.
        Bei Abbruch wird 0 zurückgegeben.
    """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x, screen_center_y = screen_width // 2, screen_height // 2
    print(f"DEBUG (cockCrack V4 Korr): Nutze Screen-Größe: {actual_screen_size}")
    print(f"DEBUG (cockCrack V4 Korr): Starte Minispiel 2. Erfolg führt zu Teil 3.")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung prüfen ---
    mixer_ok = bool(pygame.mixer.get_init())
    if not mixer_ok:
        print("WARNUNG (cockCrack V4 Korr): Mixer nicht initialisiert.")
    else:
        print("DEBUG (cockCrack V4 Korr): Mixer ist verfügbar.")

    # --- VEREINFACHTES/KORRIGIERTES PFAD-SETUP ---
    try:
        # Pfad zum Verzeichnis dieses Skripts
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Fallback, wenn __file__ nicht definiert ist
        script_dir_game = os.path.abspath(".")

    # Gehe zwei Ebenen hoch zum /data Ordner (Annahme: Dieses Skript ist in data/miniGame/cockCrack)
    data_folder_abs = os.path.normpath(os.path.join(script_dir_game, "..", ".."))

    # Definiere die Unterordner für Bilder und Sounds relativ zum /data Ordner
    image_folder_abs = os.path.join(data_folder_abs, "bilder")
    sound_folder_abs = os.path.join(data_folder_abs, "sounds") # Auch wenn hier nicht genutzt

    print(f"DEBUG (cockCrack V4 Korr): Script Dir: {script_dir_game}")
    print(f"DEBUG (cockCrack V4 Korr): Data folder (vermutet): {data_folder_abs}")
    print(f"DEBUG (cockCrack V4 Korr): Image folder (abs): {image_folder_abs}")
    # --- ENDE VEREINFACHTES PFAD-SETUP ---

    # --- Android Immersive Mode & Platform Detection ---
    is_android = False
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        print("DEBUG (cockCrack V4 Korr): Pyjnius importiert.")
        Build = autoclass('android.os.Build$VERSION')
        sdk_int = Build.SDK_INT
        if sdk_int > 0:
            is_android = True
            print(f"DEBUG (cockCrack V4 Korr): Android erkannt (SDK: {sdk_int}).")
        else:
             raise RuntimeError("Nicht Android") # Explizit Fehler werfen
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        assert activity is not None
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
            print("DEBUG (cockCrack V4 Korr): Runnable Immersive gestartet.")
    except ImportError:
        print("INFO (cockCrack V4 Korr): Pyjnius nicht gefunden. Nehme an, es ist nicht Android.")
        is_android = False
    except Exception as e:
        print(f"FEHLER oder Info (cockCrack V4 Korr): Immersive Mode fehlgeschlagen oder nicht Android: {e}")
        is_android = False


    # --- Spiel Elemente Setup ---
    big_circle_radius = int(min(screen_width, screen_height) * 0.35)
    big_circle_center = (screen_center_x, screen_center_y)
    small_circle_radius = int(big_circle_radius * 0.1)
    small_circle_pos = list(big_circle_center)
    small_circle_last_pos = list(small_circle_pos)
    movement_percentage = 0.0
    DISTANCE_FOR_100_PERCENT = big_circle_radius * 10.0 # Beispiel: 10x Radius bewegen für 100%

    NUM_GREEN_CIRCLES = 4
    green_circle_initial_radius = int(small_circle_radius * 1.5)
    green_circle_positions = []
    offset_factor = 0.6
    offset_dist = int(big_circle_radius * offset_factor)
    if offset_dist + green_circle_initial_radius > big_circle_radius:
        offset_dist = big_circle_radius - green_circle_initial_radius - 5 # Verhindert Überlappung mit Rand
        print(f"WARNUNG: Grüne Kreise neu positioniert (offset={offset_dist})")
    # Positionen der grünen Kreise
    green_circle_positions.append((big_circle_center[0], big_circle_center[1] - offset_dist)) # Oben
    green_circle_positions.append((big_circle_center[0], big_circle_center[1] + offset_dist)) # Unten
    green_circle_positions.append((big_circle_center[0] - offset_dist, big_circle_center[1])) # Links
    green_circle_positions.append((big_circle_center[0] + offset_dist, big_circle_center[1])) # Rechts


    # --- Laden und Skalieren der Bilder (Verwendet korrigierte Pfade) ---
    scaled_background_image = None
    use_background_image = False
    scaled_big_blue_circle_image = None
    use_big_blue_circle_image = False
    scaled_small_red_circle_image = None
    use_small_red_circle_image = False
    original_green_circle_image = None
    use_green_circle_image = False

    # Hintergrund
    background_path = os.path.join(image_folder_abs, background_image_filename)
    try:
        loaded_bg = pygame.image.load(background_path).convert()
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG: Hintergrund '{background_image_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Hintergrund '{background_path}' laden fehlgeschlagen: {e}.")

    # Großer blauer Kreis
    blue_circle_path = os.path.join(image_folder_abs, big_blue_circle_filename)
    try:
        loaded_blue = pygame.image.load(blue_circle_path).convert_alpha()
        blue_diameter = max(1, big_circle_radius * 2)
        scaled_big_blue_circle_image = pygame.transform.smoothscale(loaded_blue, (blue_diameter, blue_diameter))
        use_big_blue_circle_image = True
        print(f"DEBUG: Blauer Kreis '{big_blue_circle_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Blauer Kreis '{blue_circle_path}' laden fehlgeschlagen: {e}.")

    # Kleiner roter Kreis
    red_circle_path = os.path.join(image_folder_abs, small_red_circle_filename)
    try:
        loaded_red = pygame.image.load(red_circle_path).convert_alpha()
        red_diameter = max(1, small_circle_radius * 2)
        scaled_small_red_circle_image = pygame.transform.smoothscale(loaded_red, (red_diameter, red_diameter))
        use_small_red_circle_image = True
        print(f"DEBUG: Roter Kreis '{small_red_circle_filename}' geladen.")
    except Exception as e:
        # Beachte diese Warnung, wenn das Bild fehlt!
        print(f"WARNUNG: Roter Kreis '{red_circle_path}' laden fehlgeschlagen: {e}.")

    # Grüner Kreis (nur Original laden)
    green_circle_path = os.path.join(image_folder_abs, green_circle_image_filename)
    try:
        original_green_circle_image = pygame.image.load(green_circle_path).convert_alpha()
        use_green_circle_image = True
        print(f"DEBUG: Grüner Kreis '{green_circle_image_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Grüner Kreis '{green_circle_path}' laden fehlgeschlagen: {e}.")
    # ----------------------------------------------------------

    # --- Schriftarten ---
    BASE_GAME_FONT_SIZE = 36
    game_font_size = max(12, int(screen_height * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try:
        font = pygame.font.SysFont("arial", game_font_size)
    except:
        font = pygame.font.Font(None, game_font_size) # Fallback
    if not font:
        font = pygame.font.Font(None, 30) # Absoluter Fallback
        game_font_size = 30

    status_pos_x = max(10, int(screen_width * 0.02))
    status_pos_y = max(60, int(screen_height * 0.1)) # Position etwas nach unten

    # --- UI Elemente ---
    # Zurück-Button
    BACK_BUTTON_WIDTH_PERCENT, BACK_BUTTON_HEIGHT_PERCENT, BASE_BACK_FONT_SIZE = 0.20, 0.08, 24
    back_button_width = int(screen_width * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(screen_height * BACK_BUTTON_HEIGHT_PERCENT)
    # Position oben zentriert
    back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, 20, back_button_width, back_button_height)
    back_button_font = None
    back_text_surface = None
    back_font_size = max(16, int(screen_height * (BASE_BACK_FONT_SIZE / FONT_SIZE_REF_H)))
    try:
        back_button_font = pygame.font.SysFont("arial", back_font_size)
        back_text_surface = back_button_font.render("Zurück", True, BLACK)
    except:
        try:
            back_button_font = pygame.font.Font(None, int(back_font_size*1.1))
            back_text_surface = back_button_font.render("Zurück", True, BLACK)
        except:
            pass # Keine Schriftart, kein Text

    # --- Spielzustands-Variablen ---
    dragging_red_circle = False
    point_scored_in_this_run = 0 # Wird auf 1 gesetzt, wenn Teil 3 erfolgreich aufgerufen wurde

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        # Delta Time (dt) für Framerate-unabhängige Physik/Logik (optional hier)
        dt = min(current_time - last_time, 0.1) # Begrenzt dt auf max 0.1 Sek
        last_time = current_time
        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                point_scored_in_this_run = 0 # Kein Erfolg bei Quit
                # Schleife wird verlassen, finales return greift
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    point_scored_in_this_run = 0 # Kein Erfolg bei ESC
                    # Schleife wird verlassen, finales return greift
            if event.type == pygame.MOUSEBUTTONDOWN:
                 if event.button == 1: # Linksklick
                       # Zuerst den Zurück-Button prüfen
                       if back_button_rect and back_button_rect.collidepoint(event.pos):
                           running = False
                           point_scored_in_this_run = 0 # Kein Erfolg bei Zurück
                           # Schleife wird verlassen, finales return greift
                       # Nur wenn nicht der Zurück-Button geklickt wurde: Drag Start prüfen
                       else:
                           dist_x = event.pos[0] - small_circle_pos[0]
                           dist_y = event.pos[1] - small_circle_pos[1]
                           # Effektiven Klickradius bestimmen (Bild oder Fallback-Radius)
                           click_radius_check = small_circle_radius
                           if use_small_red_circle_image and scaled_small_red_circle_image:
                               click_radius_check = scaled_small_red_circle_image.get_width() / 2.0
                           # Prüfen, ob Klick innerhalb des roten Kreises war
                           if math.hypot(dist_x, dist_y) <= click_radius_check:
                               dragging_red_circle = True
                               small_circle_last_pos = list(small_circle_pos) # Position beim Klick merken

            if event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1: # Linksklick losgelassen
                       if dragging_red_circle:
                           dragging_red_circle = False # Ziehen beenden

            if event.type == pygame.MOUSEMOTION:
                if dragging_red_circle:
                    # --- Bewegung des roten Kreises und Fortschrittsberechnung ---
                    potential_pos_x = event.pos[0]
                    potential_pos_y = event.pos[1]
                    # Vektor vom Zentrum des großen Kreises zur Mausposition
                    vec_x = potential_pos_x - big_circle_center[0]
                    vec_y = potential_pos_y - big_circle_center[1]
                    dist_from_center = math.hypot(vec_x, vec_y)

                    # Radius des roten Kreises für Kollisionsprüfung
                    red_radius_for_collision = small_circle_radius
                    if use_small_red_circle_image and scaled_small_red_circle_image:
                        red_radius_for_collision = scaled_small_red_circle_image.get_width() / 2.0

                    # Maximale Distanz, die der *Mittelpunkt* des roten Kreises vom Zentrum haben darf
                    max_dist = big_circle_radius - red_radius_for_collision

                    final_pos_x = potential_pos_x
                    final_pos_y = potential_pos_y

                    # Wenn Maus außerhalb des erlaubten Bereichs ist, Position begrenzen
                    if dist_from_center > max_dist:
                        if dist_from_center > 0: # Verhindert Division durch Null
                            scale = max_dist / dist_from_center
                            final_pos_x = big_circle_center[0] + vec_x * scale
                            final_pos_y = big_circle_center[1] + vec_y * scale
                        else: # Genau im Zentrum (sollte selten passieren)
                            final_pos_x = big_circle_center[0]
                            final_pos_y = big_circle_center[1]

                    # Neue Position setzen
                    small_circle_pos[0] = final_pos_x
                    small_circle_pos[1] = final_pos_y

                    # Bewegte Distanz seit letztem Frame berechnen
                    moved_dist = math.hypot(small_circle_pos[0] - small_circle_last_pos[0],
                                             small_circle_pos[1] - small_circle_last_pos[1])

                    # Fortschritt erhöhen
                    if moved_dist > 0 and DISTANCE_FOR_100_PERCENT > 0:
                        percentage_increase = (moved_dist / DISTANCE_FOR_100_PERCENT) * 100
                        movement_percentage += percentage_increase
                        # Debug-Ausgabe für Fortschritt
                        # print(f"DEBUG: Bewegung erkannt, Fortschritt: {movement_percentage:.2f}%") # Optional: kann viel Output erzeugen

                    # --- ERFOLGSBEDINGUNG & AUFRUF VON TEIL 3 ---
                    if movement_percentage >= 100.0:
                        print("INFO (cockCrack V4 Korr): Teil 2 erfolgreich (100% erreicht).")
                        if cockCrackpart3_imported and cockCrackpart3Game:
                            try:
                                print("INFO (cockCrack V4 Korr): Rufe Funktion in cockCrackpart3 auf...")
                                # KORREKTUR: Korrekten Funktionsnamen verwenden
                                cockCrackpart3Game.run_cock_crack_game( # <- Name angepasst
                                    screen, start_pills, start_liquid, start_crack, liquid_id, pills_id
                                )
                                print("INFO (cockCrack V4 Korr): Aufruf von Teil 3 beendet.")
                                point_scored_in_this_run = 1 # Signalisiert Erfolg von Teil 2

                            except AttributeError:
                                 # KORREKTUR: Aussagekräftigere Fehlermeldung
                                 print("FEHLER: Funktion 'run_cock_crack_game' nicht in cockCrackpart3 gefunden (oder Modul nicht korrekt geladen)!")
                                 point_scored_in_this_run = 0 # Konnte Teil 3 nicht starten -> kein Erfolg
                            except Exception as e_part3:
                                print(f"FEHLER während des Aufrufs von cockCrackpart3: {e_part3}")
                                traceback.print_exc()
                                point_scored_in_this_run = 0 # Fehler -> kein Erfolg
                        else:
                            print("FEHLER: cockCrackpart3 Modul konnte nicht importiert werden! Kann nicht fortfahren.")
                            point_scored_in_this_run = 0 # Kein Import -> kein Erfolg

                        running = False # Beende die Schleife von Teil 2 in jedem Fall nach Erreichen der 100%
                        # WICHTIG: Kein return hier, das finale return am Ende wird verwendet

                    # Aktuelle Position für den nächsten Frame speichern
                    small_circle_last_pos = list(small_circle_pos)

        # --- Spiel-Logik Update (Grüne Kreise schrumpfen) ---
        # Skalierungsfaktor basierend auf Fortschritt (0% -> 1.0, 100% -> 0.0)
        scale_factor = max(0.0, 1.0 - (min(movement_percentage, 100.0) / 100.0))
        current_green_radius = int(green_circle_initial_radius * scale_factor)

        # --- Zeichnen ---
        # Hintergrund
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        else:
            screen.fill(WHITE) # Fallback

        # Großer Kreis (Rand oder Bild)
        if use_big_blue_circle_image and scaled_big_blue_circle_image:
            img_rect_blue = scaled_big_blue_circle_image.get_rect(center=big_circle_center)
            screen.blit(scaled_big_blue_circle_image, img_rect_blue)
        else:
            pygame.draw.circle(screen, BLUE, big_circle_center, big_circle_radius, 5) # Fallback Rand

        # Grüne Kreise (schrumpfend)
        if current_green_radius > 0: # Nur zeichnen, wenn Radius > 0
            for position in green_circle_positions:
                if use_green_circle_image and original_green_circle_image:
                    try:
                        current_diameter = max(1, current_green_radius * 2)
                        # Skaliere das Originalbild bei Bedarf neu
                        scaled_green_image = pygame.transform.smoothscale(original_green_circle_image, (current_diameter, current_diameter))
                        img_rect_green = scaled_green_image.get_rect(center=position)
                        screen.blit(scaled_green_image, img_rect_green)
                    except Exception as e_scale:
                        # Fallback bei Skalierungsfehler
                        pygame.draw.circle(screen, GREEN, position, current_green_radius)
                else:
                    # Fallback, wenn Bild nicht geladen wurde
                    pygame.draw.circle(screen, GREEN, position, current_green_radius)

        # Kleiner roter Kreis (beweglich)
        small_circle_draw_pos = (int(small_circle_pos[0]), int(small_circle_pos[1]))
        if use_small_red_circle_image and scaled_small_red_circle_image:
            img_rect_red = scaled_small_red_circle_image.get_rect(center=small_circle_draw_pos)
            screen.blit(scaled_small_red_circle_image, img_rect_red)
        else:
            pygame.draw.circle(screen, RED, small_circle_draw_pos, small_circle_radius) # Fallback

        # Fortschrittsanzeige (Text)
        if font:
            percent_text_surf = font.render(f"Fortschritt: {min(movement_percentage, 100.0):.0f}%", True, GREEN)
            percent_text_rect = percent_text_surf.get_rect(topleft=(status_pos_x, status_pos_y))
            screen.blit(percent_text_surf, percent_text_rect)

        # Zurück-Button
        if back_button_rect:
            btn_color = GRAY
            if back_button_rect.collidepoint(mouse_pos): btn_color = DARK_GRAY
            pygame.draw.rect(screen, btn_color, back_button_rect)     # Hintergrund
            pygame.draw.rect(screen, BLACK, back_button_rect, 2)      # Rand
            if back_text_surface and back_button_font:                 # Text (wenn Font geladen)
                text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                screen.blit(back_text_surface, text_rect)

        # Bildschirm aktualisieren
        pygame.display.flip()

        # Framerate begrenzen
        clock.tick(60)
        # --- Ende der while running Schleife ---

    # --- Ende der Spiel-Schleife ---
    # Gibt den finalen Wert von point_scored_in_this_run zurück (0 oder 1)
    print(f"INFO (cockCrack V4 Korr): Minispiel-Schleife beendet. Rückgabewert (0=Abbruch, 1=Erfolg/Teil3 Aufgerufen): {point_scored_in_this_run}")
    return point_scored_in_this_run

# --- Ende der run_cock_crack_game Funktion ---


# --- Standalone Code ---
if __name__ == "__main__":
    print("INFO: cockCrackpart2.py wird eigenständig ausgeführt (V4 Korr mit PNGs).")
    print("      Bei Erfolg (100%) wird versucht, cockCrackpart3 aufzurufen und 1 zurückgegeben.")

    pygame.init()
    # Mixer für Standalone initialisieren (optional, da Sounds hier nicht verwendet werden)
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    # Bildschirm für Standalone erstellen
    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600 # Fallback-Größe
    try:
        standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    except Exception as e_disp:
        print(f"FEHLER: Konnte Anzeigemodus nicht setzen: {e_disp}. Versuche ohne SCALED/RESIZABLE.")
        try:
            standalone_screen = pygame.display.set_mode((_sw, _sh))
        except Exception as e_disp_fb:
            print(f"FEHLER: Konnte Bildschirm nicht initialisieren: {e_disp_fb}")
            pygame.quit()
            sys.exit()

    pygame.display.set_caption("CockCrack Minispiel Teil 2 (Standalone - V4 Korr)")

    # Spiel ausführen im Standalone-Modus
    try:
        # Beispielwerte für den Start
        start_pills_sa, start_liquid_sa, start_crack_sa = 5, 5, 0
        liquid_name_sa, pills_name_sa = "Wasser", "Tafelgan" # Beispiel IDs/Namen
        print(f"\n--- Starte Standalone CockCrack Teil 2 (V4 Korr) mit Werten ---\n")

        # Hauptfunktion aufrufen
        result_sa = run_cock_crack_game(
            standalone_screen, start_pills_sa, start_liquid_sa, start_crack_sa, liquid_name_sa, pills_name_sa
        )

        # Ergebnis ausgeben
        print(f"\n--- Standalone CockCrack Teil 2 (V4 Korr) Beendet. Ergebnis: {result_sa} ---")
        if result_sa == 1:
            print("     -> Erfolg! 100% erreicht, Aufruf von Teil 3 wurde versucht/ausgeführt.")
        else: # result_sa == 0
            print("     -> Abbruch oder Fehler vor/während des Aufrufs von Teil 3.")
        print("--------------------------------------------------------------------------------\n")

    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}")
        traceback.print_exc()
    finally:
        # Pygame sauber beenden im Standalone-Modus
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---