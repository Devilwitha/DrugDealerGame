# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os
import traceback
import time
import random

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
small_red_circle_filename = "small_red_circle.png"
green_circle_image_filename = "tafelgan.png" # Wird als grüne Kreise verwendet

# --- Hauptfunktion des Spiels (V4 mit PNGs - Modifiziert für Rückgabe) ---
def run_cock_crack_game(screen_surface, start_pills, start_liquid, start_crack, liquid_id, pills_id):
    """ Führt das CockCrack Minispiel Teil 2 aus.
        Gibt 1 zurück, wenn ein Punkt erzielt wurde, sonst 0. """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x, screen_center_y = screen_width // 2, screen_height // 2
    print(f"DEBUG (cockCrack V4): Nutze Screen-Größe: {actual_screen_size}")

    print(f"DEBUG (cockCrack V4): Starte Minispiel 2 zum Erzielen eines Punktes.")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung (obwohl hier nicht direkt genutzt) ---
    mixer_ok = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (cockCrack V4): Mixer initialisiert.")
            mixer_ok = True
        except pygame.error as e:
            print(f"WARNUNG (cockCrack V4): Mixer fehlgeschlagen: {e}")
    else:
        print("DEBUG (cockCrack V4): Mixer war bereits initialisiert.")
        mixer_ok = True

    # --- KORRIGIERTES PFAD-SETUP (Version 2 - Sollte Windows & Android können) ---
    try:
        # __file__ ist der Pfad zur aktuellen Datei (cockCrackpart2.py)
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Fallback, falls __file__ nicht verfügbar ist
        script_dir_game = os.path.abspath(".")

    # Gehe die erwartete Anzahl Ebenen nach oben zum Projekt-/App-Root-Verzeichnis
    # *** ANPASSEN, FALLS DEINE STRUKTUR ANDERS IST! ***
    # Wenn cockCrackpart2.py in ProjektRoot/data/miniGame/cockCrack/ liegt (3 Ebenen tief):
    project_root_folder = os.path.join(script_dir_game, "..", "..", "..")
    # Wenn cockCrackpart2.py in ProjektRoot/miniGame/cockCrack/ liegt (2 Ebenen tief):
    # project_root_folder = os.path.join(script_dir_game, "..", "..")

    # Definiere die Pfade zu den Asset-Ordnern *relativ zum Projekt-Root*
    # unter Berücksichtigung des 'data'-Ordners!
    data_subfolder = "data"
    image_folder_rel = os.path.join(data_subfolder, "bilder")
    # Sound-Ordner definieren, auch wenn hier nicht direkt verwendet (für Konsistenz)
    sound_folder_rel = os.path.join(data_subfolder, "sounds")

    # Konstruiere die finalen, (quasi-)absoluten Pfade zu den Asset-Ordnern
    image_folder_abs = os.path.join(project_root_folder, image_folder_rel)
    sound_folder_abs = os.path.join(project_root_folder, sound_folder_rel) # Definiert für Vollständigkeit

    # Normalisiere den Pfad, um ".." etc. aufzulösen (optional, aber sauberer)
    image_folder_abs = os.path.normpath(image_folder_abs)
    sound_folder_abs = os.path.normpath(sound_folder_abs)

    print(f"DEBUG (cockCrack V4): Script Dir: {script_dir_game}")
    print(f"DEBUG (cockCrack V4): Projekt Root (vermutet): {project_root_folder}")
    print(f"DEBUG (cockCrack V4): Image folder (abs): {image_folder_abs}, Sound folder (abs): {sound_folder_abs}")
    # --- ENDE KORRIGIERTES PFAD-SETUP ---


    # --- Android Immersive Mode & Platform Detection ---
    # (Code bleibt unverändert)
    is_android = False
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        print("DEBUG (cockCrack V4): Pyjnius importiert.") # V4 statt zipWeed
        Build = autoclass('android.os.Build$VERSION')
        sdk_int = Build.SDK_INT
        if sdk_int > 0:
            is_android = True
            print(f"DEBUG (cockCrack V4): Android erkannt (SDK: {sdk_int}).")
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
            print("DEBUG (cockCrack V4): Runnable Immersive gestartet.")
    except ImportError:
        print("INFO (cockCrack V4): Pyjnius nicht gefunden. Nehme an, es ist nicht Android.")
        is_android = False
    except Exception as e:
        print(f"FEHLER oder Info (cockCrack V4): Immersive Mode fehlgeschlagen oder nicht Android: {e}")
        is_android = False


    # --- Spiel Elemente Setup ---
    big_circle_radius = int(min(screen_width, screen_height) * 0.35)
    big_circle_center = (screen_center_x, screen_center_y)
    small_circle_radius = int(big_circle_radius * 0.1)
    small_circle_pos = list(big_circle_center)
    small_circle_last_pos = list(small_circle_pos)
    movement_percentage = 0.0
    DISTANCE_FOR_100_PERCENT = big_circle_radius * 10.0

    NUM_GREEN_CIRCLES = 4
    green_circle_initial_radius = int(small_circle_radius * 1.5)
    green_circle_positions = []
    offset_factor = 0.6
    offset_dist = int(big_circle_radius * offset_factor)
    if offset_dist + green_circle_initial_radius > big_circle_radius:
        offset_dist = big_circle_radius - green_circle_initial_radius - 5
        print(f"WARNUNG: Grüne Kreise neu positioniert, um Überlappung zu vermeiden (offset={offset_dist})")
    green_circle_positions.append((big_circle_center[0], big_circle_center[1] - offset_dist)) # Oben
    green_circle_positions.append((big_circle_center[0], big_circle_center[1] + offset_dist)) # Unten
    green_circle_positions.append((big_circle_center[0] - offset_dist, big_circle_center[1])) # Links
    green_circle_positions.append((big_circle_center[0] + offset_dist, big_circle_center[1])) # Rechts

    # --- Laden und Skalieren der Bilder (verwenden jetzt *_abs Pfade) ---
    scaled_background_image = None
    use_background_image = False
    scaled_big_blue_circle_image = None
    use_big_blue_circle_image = False
    scaled_small_red_circle_image = None
    use_small_red_circle_image = False
    original_green_circle_image = None
    use_green_circle_image = False

    # Hintergrund
    background_path = os.path.join(image_folder_abs, background_image_filename) # Verwende abs Path
    try:
        loaded_bg = pygame.image.load(background_path).convert()
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG: Hintergrundbild '{background_image_filename}' geladen von '{background_path}'.")
    except Exception as e:
        print(f"WARNUNG: Hintergrundbild '{background_path}' laden/skalieren fehlgeschlagen: {e}.")
        use_background_image = False

    # Großer blauer Kreis
    blue_circle_path = os.path.join(image_folder_abs, big_blue_circle_filename) # Verwende abs Path
    try:
        loaded_blue = pygame.image.load(blue_circle_path).convert_alpha()
        blue_diameter = max(1, big_circle_radius * 2)
        scaled_big_blue_circle_image = pygame.transform.smoothscale(loaded_blue, (blue_diameter, blue_diameter))
        use_big_blue_circle_image = True
        print(f"DEBUG: Bild für großen blauen Kreis '{big_blue_circle_filename}' geladen von '{blue_circle_path}'.")
    except Exception as e:
        print(f"WARNUNG: Bild für blauen Kreis '{blue_circle_path}' laden/skalieren fehlgeschlagen: {e}.")
        use_big_blue_circle_image = False

    # Kleiner roter Kreis
    red_circle_path = os.path.join(image_folder_abs, small_red_circle_filename) # Verwende abs Path
    try:
        loaded_red = pygame.image.load(red_circle_path).convert_alpha()
        red_diameter = max(1, small_circle_radius * 2)
        scaled_small_red_circle_image = pygame.transform.smoothscale(loaded_red, (red_diameter, red_diameter))
        use_small_red_circle_image = True
        print(f"DEBUG: Bild für kleinen roten Kreis '{small_red_circle_filename}' geladen von '{red_circle_path}'.")
    except Exception as e:
        print(f"WARNUNG: Bild für roten Kreis '{red_circle_path}' laden/skalieren fehlgeschlagen: {e}.")
        use_small_red_circle_image = False

    # Grüner Kreis (nur Original laden)
    green_circle_path = os.path.join(image_folder_abs, green_circle_image_filename) # Verwende abs Path
    try:
        original_green_circle_image = pygame.image.load(green_circle_path).convert_alpha()
        use_green_circle_image = True
        print(f"DEBUG: Bild für grüne Kreise '{green_circle_image_filename}' geladen (Original) von '{green_circle_path}'.")
    except Exception as e:
        print(f"WARNUNG: Bild für grüne Kreise '{green_circle_path}' laden fehlgeschlagen: {e}.")
        use_green_circle_image = False
    # ----------------------------------------------------------

    # --- Schriftarten ---
    BASE_GAME_FONT_SIZE = 36
    game_font_size = max(12, int(screen_height * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try: font = pygame.font.SysFont("arial", game_font_size)
    except: font = pygame.font.Font(None, game_font_size)
    if not font: font = pygame.font.Font(None, 30); game_font_size = 30

    status_pos_x = max(10, int(screen_width * 0.02))
    status_pos_y = max(60, int(screen_height * 0.1)) # Position etwas nach unten

    # --- UI Elemente ---
    # (Code für Buttons etc. bleibt unverändert)
    # Zurück-Button
    BACK_BUTTON_WIDTH_PERCENT, BACK_BUTTON_HEIGHT_PERCENT, BASE_BACK_FONT_SIZE = 0.20, 0.08, 24
    back_button_width = int(screen_width * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(screen_height * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, 20, back_button_width, back_button_height)
    back_button_font = None; back_text_surface = None
    back_font_size = max(16, int(screen_height * (BASE_BACK_FONT_SIZE / FONT_SIZE_REF_H)))
    try:
        back_button_font = pygame.font.SysFont("arial", back_font_size)
        back_text_surface = back_button_font.render("Zurück", True, BLACK)
    except:
        try: back_button_font = pygame.font.Font(None, int(back_font_size*1.1)); back_text_surface = back_button_font.render("Zurück", True, BLACK)
        except: pass

    # --- Spielzustands-Variablen ---
    dragging_red_circle = False
    point_scored_in_this_run = 0 # Variable für Rückgabewert

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1)
        last_time = current_time
        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling ---
        # (Logik bleibt unverändert)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("WARNUNG (cockCrack V4): QUIT Event empfangen. Beende nur Minispiel-Loop.")
                running = False
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False
                        continue

                    dist_x = event.pos[0] - small_circle_pos[0]
                    dist_y = event.pos[1] - small_circle_pos[1]
                    click_radius_check = small_circle_radius
                    if use_small_red_circle_image and scaled_small_red_circle_image:
                        click_radius_check = scaled_small_red_circle_image.get_width() / 2.0
                    if math.hypot(dist_x, dist_y) <= click_radius_check:
                        dragging_red_circle = True
                        small_circle_last_pos = list(small_circle_pos)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if dragging_red_circle:
                        dragging_red_circle = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_red_circle:
                    potential_pos_x = event.pos[0]
                    potential_pos_y = event.pos[1]
                    vec_x = potential_pos_x - big_circle_center[0]
                    vec_y = potential_pos_y - big_circle_center[1]
                    dist_from_center = math.hypot(vec_x, vec_y)

                    red_radius_for_collision = small_circle_radius
                    if use_small_red_circle_image and scaled_small_red_circle_image:
                        red_radius_for_collision = scaled_small_red_circle_image.get_width() / 2.0

                    max_dist = big_circle_radius - red_radius_for_collision
                    final_pos_x = potential_pos_x
                    final_pos_y = potential_pos_y

                    if dist_from_center > max_dist:
                        if dist_from_center > 0:
                            scale = max_dist / dist_from_center
                            final_pos_x = big_circle_center[0] + vec_x * scale
                            final_pos_y = big_circle_center[1] + vec_y * scale
                        else:
                            final_pos_x = big_circle_center[0]
                            final_pos_y = big_circle_center[1]

                    small_circle_pos[0] = final_pos_x
                    small_circle_pos[1] = final_pos_y

                    moved_dist = math.hypot(small_circle_pos[0] - small_circle_last_pos[0],
                                             small_circle_pos[1] - small_circle_last_pos[1])

                    if moved_dist > 0 and DISTANCE_FOR_100_PERCENT > 0:
                        percentage_increase = (moved_dist / DISTANCE_FOR_100_PERCENT) * 100
                        movement_percentage += percentage_increase

                    if movement_percentage >= 100.0:
                        print("INFO (cockCrack V4): Punkt in Minispiel 2 erzielt!")
                        point_scored_in_this_run = 1
                        running = False
                        continue

                    small_circle_last_pos = list(small_circle_pos)

        # --- Spiel-Logik Update ---
        # (Logik bleibt unverändert)
        scale_factor = max(0.0, 1.0 - (min(movement_percentage, 100.0) / 100.0))
        current_green_radius = int(green_circle_initial_radius * scale_factor)

        # --- Zeichnen ---
        # (Logik bleibt unverändert)
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        else:
            screen.fill(WHITE)

        if use_big_blue_circle_image and scaled_big_blue_circle_image:
            img_rect_blue = scaled_big_blue_circle_image.get_rect(center=big_circle_center)
            screen.blit(scaled_big_blue_circle_image, img_rect_blue)
        else:
            pygame.draw.circle(screen, BLUE, big_circle_center, big_circle_radius, 5)

        if current_green_radius > 0:
            for position in green_circle_positions:
                if use_green_circle_image and original_green_circle_image:
                    try:
                        current_diameter = max(1, current_green_radius * 2)
                        # Skaliere das Originalbild bei Bedarf (effizienter wäre pre-scaling)
                        scaled_green_image = pygame.transform.smoothscale(original_green_circle_image, (current_diameter, current_diameter))
                        img_rect_green = scaled_green_image.get_rect(center=position)
                        screen.blit(scaled_green_image, img_rect_green)
                    except Exception as e_scale:
                        # Fallback bei Skalierungsfehler
                        pygame.draw.circle(screen, GREEN, position, current_green_radius)
                else:
                    pygame.draw.circle(screen, GREEN, position, current_green_radius)

        small_circle_draw_pos = (int(small_circle_pos[0]), int(small_circle_pos[1]))
        if use_small_red_circle_image and scaled_small_red_circle_image:
            img_rect_red = scaled_small_red_circle_image.get_rect(center=small_circle_draw_pos)
            screen.blit(scaled_small_red_circle_image, img_rect_red)
        else:
            pygame.draw.circle(screen, RED, small_circle_draw_pos, small_circle_radius)

        if font:
            percent_text_surf = font.render(f"Fortschritt: {min(movement_percentage, 100.0):.0f}%", True, GREEN)
            percent_text_rect = percent_text_surf.get_rect(topleft=(status_pos_x, status_pos_y))
            screen.blit(percent_text_surf, percent_text_rect)

        if back_button_rect:
            btn_color = GRAY
            if back_button_rect.collidepoint(mouse_pos): btn_color = DARK_GRAY
            pygame.draw.rect(screen, btn_color, back_button_rect)
            pygame.draw.rect(screen, BLACK, back_button_rect, 2)
            if back_text_surface and back_button_font:
                text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                screen.blit(back_text_surface, text_rect)

        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print(f"INFO (cockCrack V4): Minispiel-Schleife beendet. Rückgabewert: {point_scored_in_this_run}")

    # Gebe zurück, ob ein Punkt erzielt wurde
    return point_scored_in_this_run # WICHTIG: Gib den neuen Wert zurück

# --- Ende der run_cock_crack_game Funktion ---

# --- Standalone Code ---
if __name__ == "__main__":
    print("INFO: cockCrackPart2.py wird eigenständig ausgeführt (V4 mit PNGs).")
    print("      Stellt sicher, dass die Pfadlogik (Anzahl '..') korrekt ist und Assets unter 'data/...' liegen.")
    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("CockCrack Minispiel Teil 2 (Standalone - V4)")

    try:
        start_pills_sa, start_liquid_sa, start_crack_sa = 0, 0, 0
        liquid_name_sa, pills_name_sa = "", ""
        print(f"\n--- Starte Standalone CockCrack Teil 2 (V4) ---\n")

        result_sa = run_cock_crack_game(
            standalone_screen, start_pills_sa, start_liquid_sa, start_crack_sa, liquid_name_sa, pills_name_sa
        )

        print(f"\n--- Standalone CockCrack Teil 2 (V4) Beendet. Ergebnis (0=Abbruch, 1=Punkt): {result_sa} ---")
        print("--------------------------------------------------------------------------------\n")

    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---