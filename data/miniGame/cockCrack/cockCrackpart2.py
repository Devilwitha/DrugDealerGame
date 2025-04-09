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
RED = (255, 0, 0)   # Fallback Farbe Rot
BLUE = (0, 0, 255)  # Fallback Farbe Blau
GREEN = (0, 255, 0) # Fallback Farbe Grün
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)

# --- NEU: Dateinamen für Bilder ---
background_image_filename = "laborTable.png"
big_blue_circle_filename = "glassTopDown.png"
small_red_circle_filename = "small_red_circle.png"
green_circle_image_filename = "tafelgan.png"

# --- Hauptfunktion des Spiels (V4 mit PNGs - Modifiziert für Rückgabe) ---
def run_cock_crack_game(screen_surface, start_pills, start_liquid, start_crack, liquid_id, pills_id):
    """ Führt das CockCrack Minispiel aus (V4 - PNG Support).
        Gibt 1 zurück, wenn ein Punkt erzielt wurde, sonst 0. """ # <- Docstring angepasst
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x, screen_center_y = screen_width // 2, screen_height // 2
    print(f"DEBUG (cockCrack V4): Nutze Screen-Größe: {actual_screen_size}")

    # Ignoriere start_pills, start_liquid, start_crack für diese spezielle Verwendung.
    # Wir geben nur zurück, ob *dieser Durchlauf* erfolgreich war.
    # current_crack wird hier nicht mehr hochgezählt.

    print(f"DEBUG (cockCrack V4): Starte Minispiel 2 zum Erzielen eines Punktes.")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung ---
    score_sound = None # Sound wird nur in Teil 1 abgespielt
    mixer_ok = False
    # (Mixer Init Code bleibt gleich)
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


    # --- Android Immersive Mode & Platform Detection ---
    # (Android Code bleibt gleich)
    is_android = False
    try:
        from jnius import autoclass
        Build = autoclass('android.os.Build$VERSION')
        is_android = Build.SDK_INT > 0
    except ImportError: pass
    except Exception as e_jnius: print(f"WARNUNG (cockCrack V4): jnius Import/Check fehlgeschlagen: {e_jnius}")
    if is_android:
        print("DEBUG (cockCrack V4): Android erkannt.")
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            View = autoclass('android.view.View')
            Window = autoclass('android.view.Window')
            WindowManager = autoclass('android.view.WindowManager$LayoutParams')
            try:
                PythonJavaClass = autoclass('org.jnius.PythonJavaClass')
                java_method = autoclass('org.jnius.jnius').java_method
            except:
                PythonJavaClass = autoclass('java.lang.Object')
                if hasattr(autoclass('org.python.core.Py'), 'PythonJavaClass'): PythonJavaClass = autoclass('org.python.core.Py').PythonJavaClass; java_method = autoclass('org.python.core.Py').java_method
                else: PythonJavaClass = autoclass('org.jnius.PythonJavaClass'); java_method = autoclass('org.jnius.jnius').java_method
            flags = (View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)
            class SetUiVisibilityRunnablePJC(PythonJavaClass):
                __javainterfaces__ = ['java/lang/Runnable']
                def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
                @java_method('()V')
                def run(self):
                    try: w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f); w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                    except Exception as e: print(f"FEHLER (Runnable): {e}"); traceback.print_exc()
            runnable = SetUiVisibilityRunnablePJC(activity, flags)
            if activity: activity.runOnUiThread(runnable); print("DEBUG (cockCrack V4): Immersive Mode sollte aktiv sein.")
        except Exception as e_immersive: print(f"FEHLER (cockCrack V4): Android Immersive Mode fehlgeschlagen: {e_immersive}"); is_android = False


    # --- Pfad-Setup für Assets ---
    # (Pfad Setup Code bleibt gleich)
    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    project_root = os.path.abspath(os.path.join(script_dir_game, "..", "..", ".."))
    data_folder = os.path.join(project_root, "data")
    sound_folder = os.path.join(data_folder, "sounds") # Obwohl Sound hier nicht verwendet wird
    image_folder = os.path.join(data_folder, "bilder")
    print(f"DEBUG (cockCrack V4): Sound folder: {sound_folder}, Image folder: {image_folder}")

    # --- Spiel Elemente Setup ---
    # (Element Setup Code bleibt gleich)
    big_circle_radius = int(min(screen_width, screen_height) * 0.35)
    big_circle_center = (screen_center_x, screen_center_y)
    small_circle_radius = int(big_circle_radius * 0.1)
    small_circle_pos = list(big_circle_center)
    small_circle_last_pos = list(small_circle_pos)
    movement_percentage = 0.0
    DISTANCE_FOR_100_PERCENT = big_circle_radius * 10.0 # Beispielwert, evtl. anpassen

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


    # --- Laden und Skalieren der Bilder ---
    # (Bild Ladecode bleibt gleich)
    scaled_background_image = None
    use_background_image = False
    scaled_big_blue_circle_image = None
    use_big_blue_circle_image = False
    scaled_small_red_circle_image = None
    use_small_red_circle_image = False
    original_green_circle_image = None # Nur Original speichern, Skalierung pro Frame
    use_green_circle_image = False

    # Hintergrund
    try:
        background_path = os.path.join(image_folder, background_image_filename)
        loaded_bg = pygame.image.load(background_path).convert() # convert() wenn keine Transparenz
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG: Hintergrundbild '{background_image_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Hintergrundbild laden/skalieren fehlgeschlagen: {e}. Nutze weiße Füllung.")
        use_background_image = False

    # Großer blauer Kreis
    try:
        blue_circle_path = os.path.join(image_folder, big_blue_circle_filename)
        loaded_blue = pygame.image.load(blue_circle_path).convert_alpha()
        blue_diameter = max(1, big_circle_radius * 2)
        scaled_big_blue_circle_image = pygame.transform.smoothscale(loaded_blue, (blue_diameter, blue_diameter))
        use_big_blue_circle_image = True
        print(f"DEBUG: Bild für großen blauen Kreis '{big_blue_circle_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Bild für blauen Kreis laden/skalieren fehlgeschlagen: {e}. Nutze geometrischen Kreis.")
        use_big_blue_circle_image = False

    # Kleiner roter Kreis
    try:
        red_circle_path = os.path.join(image_folder, small_red_circle_filename)
        loaded_red = pygame.image.load(red_circle_path).convert_alpha()
        red_diameter = max(1, small_circle_radius * 2)
        scaled_small_red_circle_image = pygame.transform.smoothscale(loaded_red, (red_diameter, red_diameter))
        use_small_red_circle_image = True
        print(f"DEBUG: Bild für kleinen roten Kreis '{small_red_circle_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Bild für roten Kreis laden/skalieren fehlgeschlagen: {e}. Nutze geometrischen Kreis.")
        use_small_red_circle_image = False

    # Grüner Kreis (nur Original laden)
    try:
        green_circle_path = os.path.join(image_folder, green_circle_image_filename)
        original_green_circle_image = pygame.image.load(green_circle_path).convert_alpha()
        use_green_circle_image = True
        print(f"DEBUG: Bild für grüne Kreise '{green_circle_image_filename}' geladen (Original).")
    except Exception as e:
        print(f"WARNUNG: Bild für grüne Kreise laden fehlgeschlagen: {e}. Nutze geometrische Kreise.")
        use_green_circle_image = False


    # --- Schriftarten ---
    # (Schriftart Code bleibt gleich)
    BASE_GAME_FONT_SIZE = 36
    game_font_size = max(12, int(screen_height * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try: font = pygame.font.SysFont("arial", game_font_size)
    except: font = pygame.font.Font(None, game_font_size)
    if not font: font = pygame.font.Font(None, 30); game_font_size = 30

    status_pos_x = max(10, int(screen_width * 0.02))
    status_pos_y = max(60, int(screen_height * 0.1)) # Position etwas nach unten


    # --- Sounds laden ---
    # (Kein Sound-Laden hier nötig, da in Teil 1)

    # --- UI Elemente ---
    # Zurück-Button (unverändert)
    # (Button Code bleibt gleich)
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
    point_scored_in_this_run = 0 # NEU: Variable für Rückgabewert

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
        for event in pygame.event.get():
            # (Event Handling für QUIT, ESCAPE, MOUSEBUTTONDOWN, MOUSEBUTTONUP bleibt gleich)
            if event.type == pygame.QUIT:
                 print("WARNUNG (cockCrack V4): QUIT Event empfangen. Beende nur Minispiel-Loop.")
                 running = False
                 continue # Direkt zum nächsten Frame/Loop-Ende
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue # Direkt zum nächsten Frame/Loop-Ende
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    # Zurück Button
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False
                        continue # Direkt zum nächsten Frame/Loop-Ende

                    # Klick auf roten Kreis?
                    dist_x = event.pos[0] - small_circle_pos[0]
                    dist_y = event.pos[1] - small_circle_pos[1]
                    click_radius_check = small_circle_radius
                    if use_small_red_circle_image and scaled_small_red_circle_image:
                         click_radius_check = scaled_small_red_circle_image.get_width() / 2.0 # Float division
                    if math.hypot(dist_x, dist_y) <= click_radius_check:
                        dragging_red_circle = True
                        small_circle_last_pos = list(small_circle_pos) # Position merken

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: # Linksklick loslassen
                    if dragging_red_circle:
                        dragging_red_circle = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_red_circle:
                    # (Bewegungslogik bleibt gleich)
                    potential_pos_x = event.pos[0]
                    potential_pos_y = event.pos[1]
                    vec_x = potential_pos_x - big_circle_center[0]
                    vec_y = potential_pos_y - big_circle_center[1]
                    dist_from_center = math.hypot(vec_x, vec_y)

                    red_radius_for_collision = small_circle_radius
                    if use_small_red_circle_image and scaled_small_red_circle_image:
                        red_radius_for_collision = scaled_small_red_circle_image.get_width() / 2.0 # Float

                    max_dist = big_circle_radius - red_radius_for_collision
                    final_pos_x = potential_pos_x
                    final_pos_y = potential_pos_y

                    if dist_from_center > max_dist:
                        if dist_from_center > 0:
                            scale = max_dist / dist_from_center
                            final_pos_x = big_circle_center[0] + vec_x * scale
                            final_pos_y = big_circle_center[1] + vec_y * scale
                        else: # Genau im Zentrum, sollte nicht passieren bei dist > 0
                            final_pos_x = big_circle_center[0]
                            final_pos_y = big_circle_center[1]

                    small_circle_pos[0] = final_pos_x
                    small_circle_pos[1] = final_pos_y

                    # Bewegungsdistanz berechnen
                    moved_dist = math.hypot(small_circle_pos[0] - small_circle_last_pos[0],
                                            small_circle_pos[1] - small_circle_last_pos[1])

                    # Fortschritt erhöhen
                    if moved_dist > 0 and DISTANCE_FOR_100_PERCENT > 0:
                        percentage_increase = (moved_dist / DISTANCE_FOR_100_PERCENT) * 100
                        movement_percentage += percentage_increase

                    # Punkt erzielt?
                    if movement_percentage >= 100.0:
                        print("INFO (cockCrack V4): Punkt in Minispiel 2 erzielt!")
                        point_scored_in_this_run = 1 # NEU: Erfolg signalisieren
                        running = False # NEU: Minispiel beenden
                        # Sound wird in Teil 1 gespielt
                        # Reset von movement_percentage ist nicht mehr nötig, da wir beenden
                        # current_crack wird hier nicht mehr gezählt
                        # Direkt zum Loop-Ende springen
                        continue

                    # Letzte Position für nächste Distanzberechnung speichern
                    small_circle_last_pos = list(small_circle_pos)

        # --- Spiel-Logik Update (außerhalb Event-Loop) ---
        # (Grüne Kreise Skalierung bleibt gleich)
        scale_factor = max(0.0, 1.0 - (min(movement_percentage, 100.0) / 100.0))
        current_green_radius = int(green_circle_initial_radius * scale_factor)


        # --- Zeichnen ---
        # (Zeichenlogik bleibt unverändert)
        # Hintergrund
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        else:
            screen.fill(WHITE) # Fallback

        # Großer blauer Kreis
        if use_big_blue_circle_image and scaled_big_blue_circle_image:
            img_rect_blue = scaled_big_blue_circle_image.get_rect(center=big_circle_center)
            screen.blit(scaled_big_blue_circle_image, img_rect_blue)
        else:
            pygame.draw.circle(screen, BLUE, big_circle_center, big_circle_radius, 5) # Fallback

        # Grüne Kreise (VOR dem roten Kreis)
        if current_green_radius > 0:
            for position in green_circle_positions:
                if use_green_circle_image and original_green_circle_image:
                    try:
                        current_diameter = max(1, current_green_radius * 2)
                        scaled_green_image = pygame.transform.smoothscale(original_green_circle_image, (current_diameter, current_diameter))
                        img_rect_green = scaled_green_image.get_rect(center=position)
                        screen.blit(scaled_green_image, img_rect_green)
                    except Exception as e_scale:
                        #print(f"WARNUNG: Skalieren des grünen Kreises fehlgeschlagen: {e_scale}") # Weniger Spam
                        pygame.draw.circle(screen, GREEN, position, current_green_radius) # Geometrie Fallback bei Fehler
                else:
                    pygame.draw.circle(screen, GREEN, position, current_green_radius) # Geometrie Fallback

        # Kleiner roter Kreis (NACH den grünen)
        small_circle_draw_pos = (int(small_circle_pos[0]), int(small_circle_pos[1]))
        if use_small_red_circle_image and scaled_small_red_circle_image:
            img_rect_red = scaled_small_red_circle_image.get_rect(center=small_circle_draw_pos)
            screen.blit(scaled_small_red_circle_image, img_rect_red)
        else:
            pygame.draw.circle(screen, RED, small_circle_draw_pos, small_circle_radius) # Fallback

        # UI zeichnen (Texte)
        if font:
            # Crack-Anzeige hier nicht mehr relevant
            # crack_text_surf = font.render(f"Crack: {current_crack}", True, RED)
            # crack_text_rect = crack_text_surf.get_rect(topleft=(status_pos_x, status_pos_y))
            # screen.blit(crack_text_surf, crack_text_rect)

            # Nur Fortschritt anzeigen
            percent_text_surf = font.render(f"Fortschritt: {min(movement_percentage, 100.0):.0f}%", True, GREEN)
            # percent_text_rect = percent_text_surf.get_rect(topleft=(status_pos_x, crack_text_rect.bottom + 10))
            percent_text_rect = percent_text_surf.get_rect(topleft=(status_pos_x, status_pos_y)) # Startet jetzt oben
            screen.blit(percent_text_surf, percent_text_rect)

        # Zurück Button zeichnen
        # (Button Zeichencode bleibt gleich)
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

# --- Code für Standalone-Ausführung ---
if __name__ == "__main__":
    print("INFO: cockCrackPart2.py wird eigenständig ausgeführt (V4 mit PNGs).")
    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("CockCrack Minispiel (Standalone - V4)")

    try:
        # Für Standalone ist der Start-Crack egal, da er hier nicht gezählt wird.
        # Die anderen Werte sind auch irrelevant für die Logik hier.
        start_pills_sa = 0
        start_liquid_sa = 0
        start_crack_sa = 0
        liquid_name_sa = ""
        pills_name_sa = ""
        print(f"\n--- Starte Standalone CockCrack (V4) ---\n")

        # Rufe die Funktion auf, das Ergebnis ist hier nur für Debugging interessant
        result_sa = run_cock_crack_game(
            standalone_screen, start_pills_sa, start_liquid_sa, start_crack_sa, liquid_name_sa, pills_name_sa
        )

        # Das zurückgegebene Ergebnis (0 oder 1) wird normalerweise von cockCrack.py verarbeitet.
        print(f"\n--- Standalone CockCrack (V4) Beendet. Ergebnis (0=Abbruch, 1=Punkt): {result_sa} ---")
        print("--------------------------------------------------------------------------------\n")


    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---