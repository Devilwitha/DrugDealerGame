# -*- coding: utf-8 -*-
# pygame_minigame_collect_circles_v3_png_final_format.py - Finale Formatierung
import pygame
import sys
import os
import traceback
import time
import random
import math

# --- Android Immersive Mode & Platform Detection --- ## KORREKTE FORMATIERUNG ##
is_android = False
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    print("DEBUG: Pyjnius importiert.")
    Build = autoclass('android.os.Build$VERSION')
    sdk_int = Build.SDK_INT
    if sdk_int > 0:
        is_android = True
        print(f"DEBUG: Android erkannt (SDK: {sdk_int}).")
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
            print("DEBUG: Runnable Immersive gestartet.")
    else:
        print("INFO: Nicht Android (SDK <= 0).")
        is_android = False
except ImportError:
    print("INFO: Pyjnius nicht gefunden. Nehme an, es ist nicht Android.")
    is_android = False
except Exception as e:
    print(f"FEHLER oder Info: Immersive Mode fehlgeschlagen oder nicht Android: {e}")
    is_android = False
# --- Ende Android ---

# --- Farben ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
BROWN = (139, 69, 19)
GREEN = (0, 180, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
YELLOW = (200, 200, 0)

# --- Dateinamen für Assets ---
sound_fall_filename = "bloop.wav"
sound_click_filename = "click.wav"
sound_lock_filename = "lock.wav"
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
LARGE_RECT_PNG = "buttom_samen.png"
SMALL_SQUARE_PNG = "top_samen.png"
LARGE_CIRCLE_BG_PNG = "topf.png"
BROWN_CIRCLE_PNG = "seed.png"
RED_CIRCLE_PNG = "topf2.png"

# --- Spielkonstanten ---
BOX_FALL_SPEED = 400
RED_CIRCLE_ORBIT_FACTOR = 0.6

# --- Spielzustände ---
STATE_FALLING_BOX = 1
STATE_DRAG_BROWN_CIRCLE = 2
STATE_COLLECT_RED_CIRCLES = 3
STATE_FINISHED = 4

# --- Skalierungs-Referenzen ---
REFERENCE_SCREEN_HEIGHT = 1080.0
LARGE_RECT_REF_W = 200.0
LARGE_RECT_REF_H = 400.0
SMALL_SQUARE_REF_W = 200.0
SMALL_SQUARE_REF_H = 200.0
LARGE_CIRCLE_REF_DIAMETER = min(1920, 1080) * 0.6
LARGE_CIRCLE_REF_RADIUS = LARGE_CIRCLE_REF_DIAMETER / 2.0
GREEN_TARGET_REF_RADIUS = LARGE_CIRCLE_REF_RADIUS * 0.15
BROWN_CIRCLE_REF_DIAMETER = LARGE_CIRCLE_REF_RADIUS * 0.16
RED_CIRCLE_REF_DIAMETER = LARGE_CIRCLE_REF_RADIUS * 0.14
BACK_BUTTON_REF_WIDTH = 160.0
BACK_BUTTON_REF_HEIGHT = 40.0
BASE_INFO_FONT_SIZE_REF = 48
BASE_BUTTON_FONT_SIZE_REF = 20

# --- Hilfsfunktionen ---
def distance_sq(p1, p2):
    """Berechnet das Quadrat der Distanz zwischen zwei Punkten (x,y Tupel)."""
    # Stellt sicher, dass p1 und p2 Listen oder Tupel sind und Indizes haben
    if isinstance(p1, (list, tuple)) and isinstance(p2, (list, tuple)) and len(p1) >= 2 and len(p2) >= 2:
        return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2
    else:
        # Gibt einen großen Wert zurück oder löst einen Fehler aus, wenn die Eingabe ungültig ist
        print(f"WARNUNG: Ungültige Eingabe für distance_sq: p1={p1}, p2={p2}")
        return float('inf')


def is_point_in_circle(point, circle_center, circle_radius):
    """Prüft, ob ein Punkt in einem Kreis liegt."""
    # Stellt sicher, dass circle_radius numerisch ist
    if not isinstance(circle_radius, (int, float)) or circle_radius < 0:
        print(f"WARNUNG: Ungültiger Radius für is_point_in_circle: {circle_radius}")
        return False
    # Verwendet distance_sq zur Prüfung
    dist_sq_val = distance_sq(point, circle_center)
    # Überprüft, ob dist_sq_val ein gültiger Wert ist (nicht unendlich)
    if dist_sq_val == float('inf'):
        return False
    return dist_sq_val <= circle_radius**2


# --- Lade- und Skalierungsfunktion ---
def load_and_scale_image(folder_path, filename, target_width, target_height, fallback_color=None):
    """ Lädt ein Bild, skaliert es und gibt das Surface zurück.
        Erstellt ein Fallback-Surface, wenn das Laden fehlschlägt. """
    try:
        # Stellt sicher, dass Dimensionen gültig sind
        if target_width <= 0 or target_height <= 0:
            raise ValueError(f"Ungültige Zieldimensionen: {target_width}x{target_height}")
        img_path = os.path.join(folder_path, filename)
        original_image = pygame.image.load(img_path).convert_alpha()
        scaled_image = pygame.transform.smoothscale(original_image, (target_width, target_height))
        print(f"DEBUG: Bild '{filename}' geladen und skaliert auf {target_width}x{target_height}.")
        return scaled_image
    except Exception as e:
        print(f"WARNUNG: Bild '{filename}' laden/skalieren fehlgeschlagen: {e}")
        if fallback_color and target_width > 0 and target_height > 0:
            print(f"INFO: Erstelle Fallback-Surface für '{filename}' in Farbe {fallback_color}.")
            fallback_surf = pygame.Surface((target_width, target_height))
            fallback_surf.fill(fallback_color)
            pygame.draw.rect(fallback_surf, BLACK, fallback_surf.get_rect(), 1)
            return fallback_surf
        else:
            return None

# --- Hauptfunktion des Minispiels ---
def run_collect_circles_minigame(screen_surface):
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    print(f"DEBUG: Nutze Screen-Größe: {actual_screen_size}")

    game_state = STATE_FALLING_BOX
    running = True

    # --- Mixer & Pfade ---
    sound_fall = None; sound_click = None; sound_lock = None; mixer_ok = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            mixer_ok = True
            print("DEBUG: Mixer initialisiert.")
        except pygame.error as e:
            print(f"WARNUNG: Mixer fehlgeschlagen: {e}")
    else:
        mixer_ok = True
        print("DEBUG: Mixer war bereits initialisiert.")

    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    project_root_folder = os.path.abspath(os.path.join(script_dir_game, "..", "..", "..")) # Pfad anpassen!
    sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, "data", "sounds"))
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, "data", "bilder"))
    print(f"DEBUG: Image folder (abs): {image_folder_abs}")
    print(f"DEBUG: Sound folder (abs): {sound_folder_abs}")

    # --- Sounds laden ---
    if mixer_ok:
        try: sound_fall = pygame.mixer.Sound(os.path.join(sound_folder_abs, sound_fall_filename)); sound_fall.set_volume(0.7)
        except Exception as e: print(f"WARNUNG: Sound '{sound_fall_filename}' laden fehlgeschlagen: {e}")
        try: sound_click = pygame.mixer.Sound(os.path.join(sound_folder_abs, sound_click_filename)); sound_click.set_volume(0.6)
        except Exception as e: print(f"WARNUNG: Sound '{sound_click_filename}' laden fehlgeschlagen: {e}")
        try: sound_lock = pygame.mixer.Sound(os.path.join(sound_folder_abs, sound_lock_filename)); sound_lock.set_volume(0.8)
        except Exception as e: print(f"WARNUNG: Sound '{sound_lock_filename}' laden fehlgeschlagen: {e}")

    # --- Skalierungsfaktor berechnen ---
    scale_factor = screen_height / REFERENCE_SCREEN_HEIGHT

    # --- Fonts laden (skaliert) ---
    info_font = None; button_font = None
    try:
        info_font_size = max(12, int(BASE_INFO_FONT_SIZE_REF * scale_factor))
        try:
            info_font = pygame.font.SysFont("arial", info_font_size)
        except Exception:
            info_font = pygame.font.Font(None, info_font_size)
    except Exception as e:
        print(f"WARNUNG: Info-Schriftart: {e}")
    if not info_font: info_font = pygame.font.Font(None, 48) # Fallback

    try:
        button_font_size = max(12, int(BASE_BUTTON_FONT_SIZE_REF * scale_factor))
        try:
            button_font = pygame.font.SysFont("arial", button_font_size)
        except Exception:
            button_font = pygame.font.Font(None, button_font_size)
    except Exception as e:
        print(f"WARNUNG: Button-Schriftart: {e}")
    if not button_font: button_font = pygame.font.Font(None, 20) # Fallback

    # --- Skalierte Dimensionen berechnen ---
    scaled_large_rect_w = max(50, int(LARGE_RECT_REF_W * scale_factor))
    scaled_large_rect_h = max(100, int(LARGE_RECT_REF_H * scale_factor))
    scaled_small_square_w = scaled_large_rect_w # Gleiche Breite
    scaled_small_square_h = max(50, int(SMALL_SQUARE_REF_H * scale_factor))
    scaled_large_circle_diameter = max(100, int(LARGE_CIRCLE_REF_DIAMETER * scale_factor))
    scaled_large_circle_radius = scaled_large_circle_diameter // 2
    scaled_green_target_radius = max(10, int(GREEN_TARGET_REF_RADIUS * scale_factor))
    scaled_brown_circle_diameter = max(15, int(BROWN_CIRCLE_REF_DIAMETER * scale_factor))
    scaled_brown_circle_radius = scaled_brown_circle_diameter // 2
    scaled_red_circle_diameter = max(12, int(RED_CIRCLE_REF_DIAMETER * scale_factor))
    scaled_red_circle_radius = scaled_red_circle_diameter // 2
    scaled_back_button_w = max(50, int(BACK_BUTTON_REF_WIDTH * scale_factor))
    scaled_back_button_h = max(20, int(BACK_BUTTON_REF_HEIGHT * scale_factor))

    # --- Assets laden und skalieren ---
    scaled_large_rect_img = load_and_scale_image(image_folder_abs, LARGE_RECT_PNG, scaled_large_rect_w, scaled_large_rect_h, BLUE)
    scaled_small_square_img = load_and_scale_image(image_folder_abs, SMALL_SQUARE_PNG, scaled_small_square_w, scaled_small_square_h, YELLOW)
    scaled_large_circle_img = load_and_scale_image(image_folder_abs, LARGE_CIRCLE_BG_PNG, scaled_large_circle_diameter, scaled_large_circle_diameter, GRAY)
    scaled_brown_circle_img = load_and_scale_image(image_folder_abs, BROWN_CIRCLE_PNG, scaled_brown_circle_diameter, scaled_brown_circle_diameter, BROWN)
    scaled_red_circle_img = load_and_scale_image(image_folder_abs, RED_CIRCLE_PNG, scaled_red_circle_diameter, scaled_red_circle_diameter, RED)
    scaled_back_button_bg, scaled_back_button_hover, use_back_button_images = None, None, False
    try:
        back_bg_path = os.path.join(image_folder_abs, back_button_bg_filename)
        back_hover_path = os.path.join(image_folder_abs, back_button_hover_filename)
        img_bg_orig = pygame.image.load(back_bg_path).convert_alpha()
        img_hover_orig = pygame.image.load(back_hover_path).convert_alpha()
        scaled_back_button_bg = pygame.transform.smoothscale(img_bg_orig, (scaled_back_button_w, scaled_back_button_h))
        scaled_back_button_hover = pygame.transform.smoothscale(img_hover_orig, (scaled_back_button_w, scaled_back_button_h))
        use_back_button_images = True
        print(f"DEBUG: Zurück-Buttons geladen und skaliert.")
    except Exception as e:
        print(f"WARNUNG: Zurück-Buttons laden/skalieren fehlgeschlagen: {e}")
    # --- Ende Asset Loading ---

    # --- Spielobjekt-Daten erstellen und positionieren ---
    # Phase 1
    large_rect_obj = {}
    if scaled_large_rect_img:
        large_rect_obj = {
            'image': scaled_large_rect_img,
            'rect': scaled_large_rect_img.get_rect(midbottom=(screen_center_x, screen_height))
        }
    else: # Fallback falls Bild fehlt
        large_rect_obj = {'image': None, 'rect': pygame.Rect(screen_center_x - scaled_large_rect_w // 2, screen_height - scaled_large_rect_h, scaled_large_rect_w, scaled_large_rect_h)}

    small_square_obj = {}
    if scaled_small_square_img:
        start_rect = scaled_small_square_img.get_rect(bottomleft=large_rect_obj['rect'].topleft)
        small_square_obj = {
            'image': scaled_small_square_img,
            'rect': start_rect.copy(),
            'state': "idle",
            'y': float(start_rect.y)
        }
    else: # Fallback falls Bild fehlt
        start_y = large_rect_obj['rect'].top - scaled_small_square_h
        small_square_obj = {'image': None, 'rect': pygame.Rect(large_rect_obj['rect'].left, start_y, scaled_small_square_w, scaled_small_square_h), 'state': "idle", 'y': float(start_y)}

    # Phase 2
    large_circle_obj = {}
    if scaled_large_circle_img:
        large_circle_obj = {
            'image': scaled_large_circle_img,
            'rect': scaled_large_circle_img.get_rect(center=(screen_center_x, screen_center_y)),
            'center': (screen_center_x, screen_center_y),
            'radius': scaled_large_circle_radius
        }
    else: # Fallback
         large_circle_obj = {'image': None, 'rect': pygame.Rect(0,0,0,0), 'center': (screen_center_x, screen_center_y), 'radius': scaled_large_circle_radius}
         large_circle_obj['rect'] = pygame.Rect(screen_center_x - scaled_large_circle_radius, screen_center_y - scaled_large_circle_radius, scaled_large_circle_diameter, scaled_large_circle_diameter)


    green_target_data = {
        'center': (screen_center_x, screen_center_y),
        'radius': scaled_green_target_radius
    }

    brown_circle_start_x = large_circle_obj['rect'].left - scaled_brown_circle_diameter
    brown_circle_obj = {}
    if scaled_brown_circle_img:
        brown_circle_obj = {
            'image': scaled_brown_circle_img,
            'rect': scaled_brown_circle_img.get_rect(center=(int(brown_circle_start_x), screen_center_y)),
            'pos': [float(brown_circle_start_x), float(screen_center_y)],
            'radius': scaled_brown_circle_radius,
            'dragging': False,
            'locked': False
        }
    else: # Fallback
         brown_circle_obj = {'image': None, 'rect': pygame.Rect(0,0,scaled_brown_circle_diameter, scaled_brown_circle_diameter), 'pos': [float(brown_circle_start_x), float(screen_center_y)], 'radius': scaled_brown_circle_radius, 'dragging': False, 'locked': False}
         brown_circle_obj['rect'].center = (int(brown_circle_obj['pos'][0]), int(brown_circle_obj['pos'][1]))


    # Phase 3
    red_circles = []
    num_red_circles = 5
    red_circles_initialized = False
    collected_count = 0

    # Back Button Rect
    back_button_y = 10
    back_button_rect = pygame.Rect((screen_width - scaled_back_button_w) // 2, back_button_y, scaled_back_button_w, scaled_back_button_h)

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1)
        if dt <= 0: dt = 1/60.0
        last_time = current_time
        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False; game_state = "quit"; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False; game_state = "escape"; continue

            # Phase 1 Events
            if game_state == STATE_FALLING_BOX:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Kollisionsprüfung mit dem Rect des kleinen Quadrats
                    if small_square_obj and small_square_obj['state'] == "idle" and small_square_obj['rect'].collidepoint(event.pos):
                        small_square_obj['state'] = "falling"
                        if sound_fall: sound_fall.play()

            # Phase 2 Events
            elif game_state == STATE_DRAG_BROWN_CIRCLE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Kollisionsprüfung mit dem Rect des braunen Kreises
                    if brown_circle_obj and not brown_circle_obj['locked'] and brown_circle_obj['rect'].collidepoint(event.pos):
                        brown_circle_obj['dragging'] = True
                elif event.type == pygame.MOUSEMOTION:
                    if brown_circle_obj and brown_circle_obj['dragging']:
                        brown_circle_obj['pos'][0] = float(event.pos[0])
                        brown_circle_obj['pos'][1] = float(event.pos[1])
                        # Update rect center based on float pos
                        brown_circle_obj['rect'].center = (int(brown_circle_obj['pos'][0]), int(brown_circle_obj['pos'][1]))
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if brown_circle_obj and brown_circle_obj['dragging']:
                        brown_circle_obj['dragging'] = False
                        # Kollision mit logischem grünen Radius prüfen
                        dist_sq = distance_sq(brown_circle_obj['pos'], green_target_data['center'])
                        if dist_sq <= green_target_data['radius']**2:
                            brown_circle_obj['locked'] = True
                            # Position im Zentrum fixieren (sowohl float als auch rect)
                            brown_circle_obj['pos'][0] = float(green_target_data['center'][0])
                            brown_circle_obj['pos'][1] = float(green_target_data['center'][1])
                            brown_circle_obj['rect'].center = green_target_data['center']
                            if sound_lock: sound_lock.play()
                            game_state = STATE_COLLECT_RED_CIRCLES
                            print("DEBUG: Brown circle locked, starting Phase 3")

            # Phase 3 Events
            elif game_state == STATE_COLLECT_RED_CIRCLES:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i in range(len(red_circles) - 1, -1, -1):
                        circle = red_circles[i]
                        # Kollision mit dem Rect des roten Kreises
                        if not circle['collected'] and circle['rect'].collidepoint(event.pos):
                            circle['collected'] = True
                            collected_count += 1
                            if sound_click: sound_click.play()
                            # Verschiebe zum Ziel (logisch und rect)
                            circle['pos'][0] = float(green_target_data['center'][0] + random.randint(-green_target_data['radius']//3, green_target_data['radius']//3))
                            circle['pos'][1] = float(green_target_data['center'][1] + random.randint(-green_target_data['radius']//3, green_target_data['radius']//3))
                            circle['rect'].center = (int(circle['pos'][0]), int(circle['pos'][1]))
                            print(f"DEBUG: Red circle collected ({collected_count}/{len(red_circles)})")
                            break

            # Back Button Event
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                 if back_button_rect and back_button_rect.collidepoint(event.pos):
                     running = False; game_state = "back_button"; continue

        # --- Spiel-Logik Update ---
        if game_state == STATE_FALLING_BOX:
            if small_square_obj and small_square_obj['state'] == "falling":
                small_square_obj['y'] += BOX_FALL_SPEED * dt
                small_square_obj['rect'].y = int(small_square_obj['y'])
                if small_square_obj['rect'].top > screen_height:
                    small_square_obj['state'] = "gone"
                    game_state = STATE_DRAG_BROWN_CIRCLE
                    print("DEBUG: Box gone, starting Phase 2")

        elif game_state == STATE_COLLECT_RED_CIRCLES:
            if not red_circles_initialized:
                orbit_radius = large_circle_obj['radius'] * RED_CIRCLE_ORBIT_FACTOR
                angle_step = 360 / num_red_circles
                # Verwende das skalierte Bild der roten Kreise
                red_img_to_use = scaled_red_circle_img
                if red_img_to_use: # Nur initialisieren, wenn Bild vorhanden
                    for i in range(num_red_circles):
                        angle = math.radians(i * angle_step + 15)
                        x = float(green_target_data['center'][0] + orbit_radius * math.cos(angle))
                        y = float(green_target_data['center'][1] + orbit_radius * math.sin(angle))
                        red_rect = red_img_to_use.get_rect(center=(int(x), int(y)))
                        red_circles.append({'image': red_img_to_use, 'rect': red_rect, 'pos': [x, y], 'collected': False})
                    red_circles_initialized = True
                    print(f"DEBUG: Initialized {len(red_circles)} red circles")
                else:
                    print("WARNUNG: Rotes Kreis-Bild fehlt, Phase 3 kann nicht starten.")
                    # Ggf. Fehlerzustand oder Abbruch hier
                    game_state = STATE_FINISHED # Oder anderer Fehlerstatus
                    running = False

            # Prüfen, ob alle Kreise gesammelt sind (nur wenn initialisiert)
            if red_circles_initialized and collected_count >= len(red_circles):
                game_state = STATE_FINISHED
                print("DEBUG: All red circles collected, game finished!")

        # --- ZEICHNEN ---
        screen.fill(WHITE)

        # Phase 1 Zeichnen
        if game_state == STATE_FALLING_BOX:
            if large_rect_obj['image']:
                screen.blit(large_rect_obj['image'], large_rect_obj['rect'].topleft)
            else: # Fallback zeichnen
                pygame.draw.rect(screen, BLUE, large_rect_obj['rect'])
            if small_square_obj and small_square_obj['state'] != "gone":
                if small_square_obj['image']:
                    screen.blit(small_square_obj['image'], small_square_obj['rect'].topleft)
                else: # Fallback zeichnen
                    pygame.draw.rect(screen, YELLOW, small_square_obj['rect'])

        # Phase 2 & 3 Zeichnen
        elif game_state >= STATE_DRAG_BROWN_CIRCLE:
            # Großer Kreis
            if large_circle_obj['image']:
                screen.blit(large_circle_obj['image'], large_circle_obj['rect'].topleft)
            else: # Fallback zeichnen
                pygame.draw.circle(screen, GRAY, large_circle_obj['center'], large_circle_obj['radius'], 5)
                pygame.draw.circle(screen, GREEN, green_target_data['center'], green_target_data['radius']) # Grünes Ziel separat

            # Brauner Kreis
            if brown_circle_obj and brown_circle_obj['image']:
                 screen.blit(brown_circle_obj['image'], brown_circle_obj['rect'].topleft)
            elif brown_circle_obj: # Fallback zeichnen
                 pygame.draw.circle(screen, BROWN, brown_circle_obj['rect'].center, brown_circle_obj['radius'])

            # Rote Kreise (nur in Phase 3)
            if game_state == STATE_COLLECT_RED_CIRCLES:
                for circle in red_circles:
                     if circle['image']:
                         screen.blit(circle['image'], circle['rect'].topleft)
                     # Kein Fallback hier, da sie verschwinden sollen

        # Spielende Zeichnen
        elif game_state == STATE_FINISHED:
             try:
                 finished_text = info_font.render("Geschafft!", True, BLACK, GRAY)
                 finished_rect = finished_text.get_rect(center=(screen_center_x, screen_center_y))
                 screen.blit(finished_text, finished_rect)
             except Exception as e: print(f"Fehler beim Rendern des 'Fertig'-Textes: {e}")

        # Back Button Zeichnen
        if back_button_rect:
            is_hovering = back_button_rect.collidepoint(mouse_pos)
            if use_back_button_images:
                current_back_img = scaled_back_button_hover if is_hovering else scaled_back_button_bg
                if current_back_img:
                    screen.blit(current_back_img, back_button_rect.topleft)
                else:
                    btn_color = DARK_GRAY if is_hovering else GRAY
                    pygame.draw.rect(screen, btn_color, back_button_rect)
                    pygame.draw.rect(screen, BLACK, back_button_rect, 2)
            else:
                btn_color = DARK_GRAY if is_hovering else GRAY
                pygame.draw.rect(screen, btn_color, back_button_rect)
                pygame.draw.rect(screen, BLACK, back_button_rect, 2)

            if (not use_back_button_images or not scaled_back_button_bg) and button_font:
                 try:
                    back_text_surf = button_font.render("Zurück", True, BLACK)
                    back_text_rect = back_text_surf.get_rect(center=back_button_rect.center)
                    screen.blit(back_text_surf, back_text_rect)
                 except Exception as e:
                     print(f"FEHLER beim Rendern des Button-Textes: {e}")

        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print(f"INFO: Minispiel-Schleife beendet. Endzustand: {game_state}")
    return game_state == STATE_FINISHED

# --- Standalone Code ---
if __name__ == "__main__":
    print("INFO: pygame_minigame_collect_circles_v3_png_final_format.py wird eigenständig ausgeführt.")
    pygame.init()
    try: pygame.font.init()
    except Exception as e: print(f"FEHLER bei pygame.font.init(): {e}")
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.RESIZABLE)
    pygame.display.set_caption("Pygame Collect Circles PNG Final Format (Standalone Test)")

    print(f"\n--- Starte Collect Circles PNG Scaled Standalone ---\n")
    try:
        ziel_erreicht = run_collect_circles_minigame(standalone_screen)
        print(f"\n--- Standalone Beendet. Ergebnis: ---")
        print(f"  Spiel erfolgreich beendet: {ziel_erreicht}")
        print("-------------------------------------\n")
    except Exception as e_main:
        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"FEHLER im Standalone-Modus:")
        print(f"{e_main}")
        print(f"-------------------------------------")
        traceback.print_exc()
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    finally:
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---