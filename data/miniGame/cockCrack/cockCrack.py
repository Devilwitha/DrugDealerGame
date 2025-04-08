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
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
TARGET_DRAW_COLOR = BLUE
LIQUID_COLOR = (100, 150, 255, 200) # Hellblau, leicht transparent (RGBA)
CONTAINER_COLOR = BLACK # Fallback-Farbe für Container-Rand
POUR_PROGRESS_COLOR = (50, 50, 50)
PARTICLE_COLOR = (100, 150, 255, 180) # Etwas transparenter für Partikel (RGBA)
TARGET_FILL_COLOR = (60, 100, 220, 180) # Etwas dunkleres Blau für Füllstandsanzeige (RGBA)

# --- Partikel Klasse ---
class Particle:
    def __init__(self, x, y, dx, dy, radius, color, lifetime):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = radius
        self.color = color
        self.lifetime = lifetime # Sekunden
        self.initial_lifetime = lifetime

    def update(self, dt, gravity_y):
        self.dy += gravity_y * dt
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.lifetime -= dt
        return self.lifetime > 0 # True, solange Partikel leben soll

    def draw(self, surface):
        # Zeichnet den Partikel
        try:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        except (TypeError, ValueError): # Falls Farbformat Probleme macht
            pygame.draw.circle(surface, self.color[:3], (int(self.x), int(self.y)), self.radius)

# --- Hauptfunktion des Spiels ---
def run_zip_weed_game(screen_surface):
    screen = screen_surface
    actual_screen_size = screen.get_size()
    print(f"DEBUG (zipWeed): Nutze Screen-Größe: {actual_screen_size}")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung ---
    score_sound = None
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (zipWeed): Mixer initialisiert.")
        except pygame.error as e:
            print(f"WARNUNG (zipWeed): Mixer konnte nicht initialisiert werden: {e}")
    else:
        print("DEBUG (zipWeed): Mixer war bereits initialisiert.")

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

    # --- Proportionale Berechnungen ---
    if actual_screen_size[1] > actual_screen_size[0]:
        CALC_WIDTH = actual_screen_size[1]
        CALC_HEIGHT = actual_screen_size[0]
    else:
        CALC_WIDTH = actual_screen_size[0]
        CALC_HEIGHT = actual_screen_size[1]

    # --- Ziel-Definition (Größe wieder Proportional) ---
    target_width = max(1, int(CALC_WIDTH * (150 / ref_w)))
    target_height = max(1, int(CALC_HEIGHT * (200 / ref_h)))
    target_padding_right = max(1, int(CALC_WIDTH * (50 / ref_w)))
    target_padding_bottom = max(1, int(CALC_HEIGHT * (100 / ref_h)))
    target_x = actual_screen_size[0] - target_width - target_padding_right
    target_y = actual_screen_size[1] - target_height - target_padding_bottom
    target_rect = pygame.Rect(target_x, target_y, target_width, target_height)
    print(f"DEBUG: Target Rect definiert (proportional): {target_rect}")

    # --- Pfad-Setup für Assets ---
    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    project_root = os.path.abspath(os.path.join(script_dir_game, "..", "..", ".."))
    data_folder = os.path.join(project_root, "data")
    image_folder = os.path.join(data_folder, "bilder")
    sound_folder = os.path.join(data_folder, "sounds")
    print(f"DEBUG: Image folder path: {image_folder}")

    # --- Assets Laden ---

    # Ziel-Bild Laden
    target_image = None
    use_target_image = False
    target_image_filename = "massbecher.png" # Oder grip.png
    target_image_path = os.path.join(image_folder, target_image_filename)
    try:
        original_target_image = pygame.image.load(target_image_path).convert_alpha()
        if target_rect and target_width > 0 and target_height > 0:
            try:
                target_image = pygame.transform.smoothscale(original_target_image, (target_width, target_height))
                use_target_image = True
            except Exception as e_scale:
                 print(f"WARNUNG: Skalieren von Ziel-Bild fehlgeschlagen: {e_scale}")
    except Exception as e:
        print(f"WARNUNG: Laden des Ziel-Bildes '{target_image_path}' fehlgeschlagen: {e}")


    # Kreise (ersetzt durch Bild)
    NUM_CIRCLES = 4
    circle_diameter = max(10, int(CALC_WIDTH * (40 / ref_w)))
    circle_radius = circle_diameter // 2
    circle_spacing = max(2, int(CALC_WIDTH * (8 / ref_w)))
    start_padding_left_circles = max(1, int(CALC_WIDTH * (50 / ref_w)))
    start_padding_top_circles = max(1, int(CALC_HEIGHT * (100 / ref_h)))
    start_positions_circles = []
    small_circles_rects = []
    for i in range(NUM_CIRCLES):
        start_x = start_padding_left_circles + i * (circle_diameter + circle_spacing)
        start_y = start_padding_top_circles
        start_positions_circles.append((start_x, start_y))
        small_circles_rects.append(pygame.Rect(start_x, start_y, circle_diameter, circle_diameter))
    circle_gravity_value = max(1, int(CALC_HEIGHT * (10 / ref_h)))

    circle_image_path = os.path.join(image_folder, "testpill.png")
    circle_image = None
    use_circle_image = False
    try:
        original_circle_image = pygame.image.load(circle_image_path).convert_alpha()
        if circle_diameter > 0:
            try:
                circle_image = pygame.transform.smoothscale(original_circle_image, (circle_diameter, circle_diameter))
                use_circle_image = True
            except Exception as e_scale:
                print(f"WARNUNG: Skalieren von Kreis-Bild fehlgeschlagen: {e_scale}")
    except Exception as e:
        print(f"WARNUNG: Kreis-Bild '{circle_image_path}' laden fehlgeschlagen: {e}")


    # Container (ersetzt durch Bild, mit Gravitation)
    container_width = max(20, int(CALC_WIDTH * (100 / ref_w)))
    container_height = max(60, int(CALC_HEIGHT * (120 / ref_h) * 2)) # Höhe bleibt doppelt
    container_start_x = max(10, int(CALC_WIDTH * (100 / ref_w)))
    container_start_y = actual_screen_size[1] - container_height - max(10, int(CALC_HEIGHT * (50 / ref_h)))
    container_rect = pygame.Rect(container_start_x, container_start_y, container_width, container_height)
    container_angle = 0.0
    TILT_SPEED = 90.0
    MAX_TILT_ANGLE = 85.0
    POUR_THRESHOLD_ANGLE = 40.0
    POUR_RATE = 0.5
    INITIAL_LIQUID_FRACTION = 0.8
    current_liquid_fraction = INITIAL_LIQUID_FRACTION
    total_liquid_poured_in_target = 0.0
    GOAL_FRACTION = 0.5
    container_falling = False # Zustand, ob der Container fallen SOLLTE

    container_image_path = os.path.join(image_folder, "glass.png")
    scaled_container_image = None
    use_container_image = False
    try:
        original_container_image = pygame.image.load(container_image_path).convert_alpha()
        if container_width > 0 and container_height > 0:
            try:
                scaled_container_image = pygame.transform.smoothscale(original_container_image, (container_width, container_height))
                use_container_image = True
            except Exception as e_scale:
                print(f"WARNUNG: Skalieren von Container-Bild fehlgeschlagen: {e_scale}")
    except Exception as e:
        print(f"WARNUNG: Container-Bild '{container_image_path}' laden fehlgeschlagen: {e}")

    # Partikel System
    active_particles = []
    PARTICLE_LIFETIME = 0.8
    PARTICLE_RADIUS = 3
    PARTICLES_PER_SECOND = 150
    PARTICLE_INITIAL_VELOCITY_Y = 50
    PARTICLE_SPREAD = 40
    PARTICLE_GRAVITY = 400.0

    # --- Schriftart (Formatierung geprüft) ---
    BASE_GAME_FONT_SIZE = 36
    game_font_size = max(12, int(CALC_HEIGHT * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try:
        font = pygame.font.SysFont("arial", game_font_size)
    except pygame.error:
        print(f"WARNUNG: SysFont 'arial' (size {game_font_size}) nicht gefunden, nutze Fallback.")
        try:
            font = pygame.font.Font(None, game_font_size)
        except Exception as e_font_fallback:
            print(f"WARNUNG: Fallback-Font fehlgeschlagen: {e_font_fallback}")
            font = None
    if not font:
        print("WARNUNG: Konnte keine Spiel-Schriftart laden! Nutze absoluten Fallback.")
        font = pygame.font.Font(None, 30)
        game_font_size = 30

    BASE_INFO_FONT_SIZE = 18
    info_font_size = max(10, int(CALC_HEIGHT * (BASE_INFO_FONT_SIZE / FONT_SIZE_REF_H)))
    info_font = None
    try:
        info_font = pygame.font.SysFont("arial", info_font_size)
    except pygame.error:
        print(f"WARNUNG: SysFont 'arial' (size {info_font_size}) für Info nicht gefunden, nutze Fallback.")
        try:
            info_font = pygame.font.Font(None, info_font_size)
        except Exception as e_info_font_fallback:
            print(f"WARNUNG: Fallback-Info-Font fehlgeschlagen: {e_info_font_fallback}")
            info_font = None
    if not info_font:
        print("WARNUNG: Konnte keine Info-Schriftart laden! Nutze absoluten Fallback.")
        info_font = pygame.font.Font(None, 20)
        info_font_size = 20

    score_pos_x = max(1, int(actual_screen_size[0] * (10 / ref_w)))
    score_pos_y = max(1, int(actual_screen_size[1] * (10 / ref_h)))
    progress_pos_x = score_pos_x
    progress_pos_y = score_pos_y + max(12, game_font_size) + 5

    # Sounds laden
    sound_filename_score = "bagFinish.wav"
    sound_path_score = os.path.join(sound_folder, sound_filename_score)
    try:
        if pygame.mixer.get_init():
            score_sound = pygame.mixer.Sound(sound_path_score)
            score_sound.set_volume(0.9)
    except Exception as e:
        print(f"WARNUNG (zipWeed): Laden Score-Sound fehlgeschlagen: {e}")

    # --- UI Elemente ---

    # Zurück Button
    BACK_BUTTON_WIDTH_PERCENT = 0.20
    BACK_BUTTON_HEIGHT_PERCENT = 0.08
    BASE_BACK_FONT_SIZE = 24
    back_button_width = int(actual_screen_size[0] * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(actual_screen_size[1] * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_x = (actual_screen_size[0] - back_button_width) // 2
    back_button_y = 20
    back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
    back_button_font_size = max(16, int(actual_screen_size[1] * (BASE_BACK_FONT_SIZE / FONT_SIZE_REF_H)))
    back_button_font = None
    back_text_surface = None
    try:
        back_button_font = pygame.font.SysFont("arial", back_button_font_size)
        if back_button_font:
             back_text_surface = back_button_font.render("Zurück", True, BLACK)
    except Exception as e_backfont:
        print(f"WARNUNG: Konnte Font für Zurück-Button nicht laden: {e_backfont}")
        try:
            back_button_font = pygame.font.Font(None, int(back_button_font_size*1.1))
            if back_button_font:
                 back_text_surface = back_button_font.render("Zurück", True, BLACK)
        except Exception as e_fallback:
            print(f"WARNUNG: Fallback-Font für Zurück-Button auch fehlgeschlagen: {e_fallback}")
            pass

    # Touch Buttons (Layout geändert)
    touch_button_size = max(40, int(CALC_WIDTH * 0.1))
    button_margin_x = touch_button_size // 2
    button_margin_y_bottom = touch_button_size * 1.5
    button_gap = touch_button_size // 4

    # Rechter Tilt Button (>) - jetzt unten links
    tilt_right_button_rect = pygame.Rect(
        button_margin_x,
        actual_screen_size[1] - button_margin_y_bottom,
        touch_button_size, touch_button_size
    )
    # Linker Tilt Button (<) - jetzt darüber
    tilt_left_button_rect = pygame.Rect(
        button_margin_x,
        tilt_right_button_rect.top - touch_button_size - button_gap,
        touch_button_size, touch_button_size
    )

    # Text für Buttons
    touch_button_font = None
    left_arrow_surf = None
    right_arrow_surf = None
    left_arrow_rect = None
    right_arrow_rect = None
    try:
        touch_button_font = pygame.font.Font(None, touch_button_size // 2)
        if touch_button_font:
             left_arrow_surf = touch_button_font.render(" < ", True, BLACK)
             right_arrow_surf = touch_button_font.render(" > ", True, BLACK)
             if left_arrow_surf: left_arrow_rect = left_arrow_surf.get_rect(center=tilt_left_button_rect.center)
             if right_arrow_surf: right_arrow_rect = right_arrow_surf.get_rect(center=tilt_right_button_rect.center)
    except Exception as e_touchfont:
         print(f"WARNUNG: Font für Touch-Buttons konnte nicht geladen werden: {e_touchfont}")


    # --- Spielzustands-Variablen ---
    score = 0
    dragging_circle_index = -1
    circles_falling = [False] * NUM_CIRCLES
    dragging_container = False
    container_offset_x = 0
    container_offset_y = 0
    tilting_left = False
    tilting_right = False
    touch_tilting_left = False
    touch_tilting_right = False
    game_over_delay_timer = 0.0
    particle_emission_accumulator = 0.0

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        dt = min(dt, 0.1) # Limit dt

        try:
            mouse_pos = pygame.mouse.get_pos()
        except pygame.error:
            mouse_pos = (0, 0)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False; pygame.quit(); sys.exit()

            # Keyboard Events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_q: tilting_left = True
                if event.key == pygame.K_e: tilting_right = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_q: tilting_left = False
                if event.key == pygame.K_e: tilting_right = False

            # Mouse/Touch Events
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect and back_button_rect.collidepoint(event.pos): running = False; continue
                if tilt_left_button_rect.collidepoint(event.pos): touch_tilting_left = True; continue
                if tilt_right_button_rect.collidepoint(event.pos): touch_tilting_right = True; continue

                clicked_on_circle = False
                for i in range(NUM_CIRCLES - 1, -1, -1):
                    if small_circles_rects[i].collidepoint(event.pos):
                        dragging_circle_index = i; circles_falling[i] = False; dragging_container = False; clicked_on_circle = True;
                        offset_x = small_circles_rects[i].x - event.pos[0]; offset_y = small_circles_rects[i].y - event.pos[1]; break
                if not clicked_on_circle and container_rect.collidepoint(event.pos):
                    dragging_container = True; container_falling = False; dragging_circle_index = -1;
                    container_offset_x = container_rect.x - event.pos[0]; container_offset_y = container_rect.y - event.pos[1]

            if event.type == pygame.MOUSEBUTTONUP:
                 touch_tilting_left = False; touch_tilting_right = False

                 if dragging_circle_index != -1:
                     released_index = dragging_circle_index; dragging_circle_index = -1; is_supported = False
                     if small_circles_rects[released_index].bottom >= actual_screen_size[1]: is_supported = True
                     if target_rect and not is_supported:
                         is_horizontally_overlapping_circle = (small_circles_rects[released_index].right > target_rect.left and small_circles_rects[released_index].left < target_rect.right)
                         if is_horizontally_overlapping_circle and small_circles_rects[released_index].bottom >= target_rect.bottom: is_supported = True
                     should_fall = False
                     if not is_supported:
                         if target_rect:
                             if not target_rect.contains(small_circles_rects[released_index]) or \
                                small_circles_rects[released_index].bottom < target_rect.bottom: should_fall = True
                         else: should_fall = True
                     if should_fall: circles_falling[released_index] = True

                 elif dragging_container:
                     dragging_container = False; screen_height = actual_screen_size[1]
                     if container_rect.bottom < screen_height:
                         on_target_bottom = False
                         if target_rect:
                             is_horizontally_overlapping_cont = (container_rect.right > target_rect.left and container_rect.left < target_rect.right)
                             if is_horizontally_overlapping_cont and container_rect.bottom >= target_rect.bottom: on_target_bottom = True
                         if not on_target_bottom:
                             # !!! HIER WIRD container_falling GESETZT !!!
                             # Wir lassen dies zu, aber die Gravitation wird nur angewendet, wenn NICHT Android
                             container_falling = True


            if event.type == pygame.MOUSEMOTION:
                if dragging_circle_index != -1:
                    current_rect = small_circles_rects[dragging_circle_index]; old_pos = current_rect.topleft; potential_x = event.pos[0] + offset_x; potential_y = event.pos[1] + offset_y; final_x, final_y = potential_x, potential_y
                    final_x = max(0, min(final_x, actual_screen_size[0] - current_rect.width)); final_y = max(0, min(final_y, actual_screen_size[1] - current_rect.height)); potential_rect = pygame.Rect(final_x, final_y, current_rect.width, current_rect.height)
                    if target_rect and potential_rect.colliderect(target_rect):
                        was_outside = not target_rect.contains(current_rect); was_inside = target_rect.contains(current_rect); dx = final_x - old_pos[0]; dy = final_y - old_pos[1]
                        if was_outside:
                            if dx > 0 and current_rect.right <= target_rect.left and potential_rect.right > target_rect.left and potential_rect.bottom > target_rect.top: final_x = target_rect.left - current_rect.width
                            elif dx < 0 and current_rect.left >= target_rect.right and potential_rect.left < target_rect.right and potential_rect.bottom > target_rect.top: final_x = target_rect.right
                            elif dy < 0 and current_rect.top >= target_rect.bottom and potential_rect.top < target_rect.bottom: final_y = target_rect.bottom
                        elif was_inside:
                            if potential_rect.left < target_rect.left: final_x = target_rect.left
                            elif potential_rect.right > target_rect.right: final_x = target_rect.right - current_rect.width
                            elif potential_rect.bottom > target_rect.bottom: final_y = target_rect.bottom - current_rect.height
                    current_rect.topleft = (final_x, final_y)
                elif dragging_container:
                    potential_x = event.pos[0] + container_offset_x; potential_y = event.pos[1] + container_offset_y
                    final_x = max(0, min(potential_x, actual_screen_size[0] - container_rect.width)); final_y = max(0, min(potential_y, actual_screen_size[1] - container_rect.height)); container_rect.topleft = (final_x, final_y)

        # --- Spiel-Logik Update ---
        if game_over_delay_timer <= 0:

            # Container Kippen
            effective_tilt = 0
            if tilting_left or touch_tilting_left: effective_tilt -= 1
            if tilting_right or touch_tilting_right: effective_tilt += 1
            if effective_tilt != 0:
                container_angle -= effective_tilt * TILT_SPEED * dt
                container_angle = max(-MAX_TILT_ANGLE, min(MAX_TILT_ANGLE, container_angle))

            # Container Gießen & Partikel erzeugen
            if abs(container_angle) > POUR_THRESHOLD_ANGLE and current_liquid_fraction > 0:
                pour_amount = POUR_RATE * INITIAL_LIQUID_FRACTION * dt
                pour_amount = min(pour_amount, current_liquid_fraction)
                current_liquid_fraction -= pour_amount
                poured_this_frame_total = pour_amount

                # Spout-Position (fixiert an Ecken der Bounding Box)
                if container_angle > 0: # Kippt nach links
                    spout_x = container_rect.left + PARTICLE_RADIUS + 1
                    spout_y = container_rect.top + PARTICLE_RADIUS + 1
                else: # Kippt nach rechts oder 0
                    spout_x = container_rect.right - PARTICLE_RADIUS - 1
                    spout_y = container_rect.top + PARTICLE_RADIUS + 1

                # Prüfen ob ins Ziel gegossen wird (für Score)
                if target_rect.left < spout_x < target_rect.right and spout_y < target_rect.bottom :
                    total_liquid_poured_in_target += poured_this_frame_total
                    total_liquid_poured_in_target = min(total_liquid_poured_in_target, INITIAL_LIQUID_FRACTION)

                # Partikel erzeugen basierend auf Gießmenge
                particle_emission_this_frame = poured_this_frame_total * PARTICLES_PER_SECOND
                particle_emission_accumulator += particle_emission_this_frame
                num_particles_to_emit = int(particle_emission_accumulator)
                if num_particles_to_emit > 0:
                    particle_emission_accumulator -= num_particles_to_emit
                    for _ in range(num_particles_to_emit):
                        emit_x = spout_x + random.uniform(-PARTICLE_RADIUS, PARTICLE_RADIUS)
                        emit_y = spout_y + random.uniform(-PARTICLE_RADIUS, PARTICLE_RADIUS)
                        rad_angle = math.radians(container_angle)
                        vel_angle_factor = math.sin(rad_angle)
                        initial_dx = random.uniform(-PARTICLE_SPREAD, PARTICLE_SPREAD) - vel_angle_factor * 30
                        initial_dy = PARTICLE_INITIAL_VELOCITY_Y + random.uniform(0, 20)
                        p = Particle(emit_x, emit_y, initial_dx, initial_dy, PARTICLE_RADIUS, PARTICLE_COLOR, PARTICLE_LIFETIME)
                        active_particles.append(p)

            # Physik für Container (Gravitation)
            # >>> HIER IST DIE ÄNDERUNG: Gravitation nur wenn NICHT Android <<<
            if container_falling and not dragging_container and not is_android:
                potential_cont_rect = container_rect.move(0, circle_gravity_value)
                screen_height = actual_screen_size[1]
                cont_stopped_falling = False
                # Prüfen, ob Boden erreicht
                if potential_cont_rect.bottom >= screen_height:
                    container_rect.bottom = screen_height
                    container_falling = False # Stoppt das Fallen
                    cont_stopped_falling = True
                # Prüfen, ob Zielboden erreicht
                elif target_rect:
                    is_horizontally_overlapping_cont = (potential_cont_rect.right > target_rect.left and
                                                          potential_cont_rect.left < target_rect.right)
                    # Nur stoppen, wenn vorher drüber und jetzt drunter/drauf
                    if is_horizontally_overlapping_cont and \
                       container_rect.bottom <= target_rect.bottom and \
                       potential_cont_rect.bottom > target_rect.bottom:
                            container_rect.bottom = target_rect.bottom
                            container_falling = False # Stoppt das Fallen
                            cont_stopped_falling = True
                # Wenn nicht gestoppt, weiter fallen lassen
                if not cont_stopped_falling:
                    container_rect.move_ip(0, circle_gravity_value)
            # --- Ende der Gravitations-Änderung für Container ---

            # Physik für Kreise (Gravitation) - Bleibt unverändert
            for i in range(NUM_CIRCLES):
                if circles_falling[i] and dragging_circle_index != i:
                    current_rect = small_circles_rects[i]
                    potential_rect = current_rect.move(0, circle_gravity_value)
                    screen_height = actual_screen_size[1]
                    stopped_falling = False
                    if potential_rect.bottom >= screen_height:
                        current_rect.bottom = screen_height
                        circles_falling[i] = False
                        stopped_falling = True
                    elif target_rect:
                        is_horizontally_overlapping_circle = (potential_rect.right > target_rect.left and
                                                                potential_rect.left < target_rect.right)
                        if is_horizontally_overlapping_circle and \
                           current_rect.bottom <= target_rect.bottom and \
                           potential_rect.bottom > target_rect.bottom:
                                current_rect.bottom = target_rect.bottom
                                circles_falling[i] = False
                                stopped_falling = True
                    if not stopped_falling:
                        current_rect.move_ip(0, circle_gravity_value)

            # Partikel Update & Cleanup
            particles_alive = []
            for p in active_particles:
                if p.update(dt, PARTICLE_GRAVITY): # Aktualisiere Partikel
                    # Partikel verschwindet im Zielboden oder Screenboden
                    if target_rect and p.y > target_rect.bottom and target_rect.left < p.x < target_rect.right:
                        p.lifetime = 0
                    elif p.y > actual_screen_size[1] - p.radius:
                            p.lifetime = 0
                    # Nur "lebende" Partikel behalten
                    if p.lifetime > 0:
                        particles_alive.append(p)
            active_particles = particles_alive # Ersetze alte Liste

        # --- Win Condition & Reset ---
        if game_over_delay_timer > 0: # Im Reset-Delay
            game_over_delay_timer -= dt
            if game_over_delay_timer <= 0: # Delay vorbei -> Reset
                # Reset Container
                container_angle = 0.0
                current_liquid_fraction = INITIAL_LIQUID_FRACTION
                total_liquid_poured_in_target = 0.0
                container_rect.topleft = (container_start_x, container_start_y)
                container_falling = False # Auch hier zurücksetzen
                # Reset Controls
                tilting_left = tilting_right = touch_tilting_left = touch_tilting_right = False
                dragging_container = False
                # Reset Partikel & Kreise
                active_particles = []
                dragging_circle_index = -1
                for i in range(NUM_CIRCLES):
                    small_circles_rects[i].topleft = start_positions_circles[i]
                    circles_falling[i] = False
        else: # Prüfe, ob gewonnen wurde (wenn kein Delay aktiv)
            liquid_condition_met = total_liquid_poured_in_target >= INITIAL_LIQUID_FRACTION * GOAL_FRACTION
            all_circles_in_target_and_static = False
            if target_rect:
                all_circles_in_target_and_static = all(
                    target_rect.contains(cr) and not circles_falling[idx]
                    for idx, cr in enumerate(small_circles_rects)
                )
            if liquid_condition_met and all_circles_in_target_and_static:
                print("INFO: Ziel erreicht (Flüssigkeit UND Kreise)!")
                score += 1
                game_over_delay_timer = 1.0 # Starte 1 Sekunde Delay
                if score_sound:
                    score_sound.play()

        # --- Zeichnen ---
        screen.fill(WHITE)

        # Ziel zeichnen (Bild oder Fallback)
        if target_rect:
            if use_target_image and target_image:
                screen.blit(target_image, target_rect.topleft)
            else: # Fallback: Linien zeichnen
                pygame.draw.line(screen, TARGET_DRAW_COLOR, target_rect.bottomleft, target_rect.topleft, 3)
                pygame.draw.line(screen, TARGET_DRAW_COLOR, target_rect.bottomright, target_rect.topright, 3)
                pygame.draw.line(screen, TARGET_DRAW_COLOR, target_rect.bottomleft, target_rect.bottomright, 3)

            # NEU: Visuellen Füllstand im Ziel zeichnen (über dem Hintergrund)
            target_fill_goal = INITIAL_LIQUID_FRACTION * GOAL_FRACTION
            if target_fill_goal > 0: # Division durch Null verhindern
                target_fill_ratio = total_liquid_poured_in_target / target_fill_goal
                target_fill_ratio = max(0.0, min(1.0, target_fill_ratio)) # Clamp 0-1
                fill_height = int(target_rect.height * target_fill_ratio)
                if fill_height > 0:
                    fill_rect = pygame.Rect(
                        target_rect.x,
                        target_rect.bottom - fill_height,
                        target_rect.width,
                        fill_height
                    )
                    # Zeichne mit Alpha für Transparenz
                    fill_surface = pygame.Surface(fill_rect.size, pygame.SRCALPHA)
                    fill_surface.fill(TARGET_FILL_COLOR)
                    screen.blit(fill_surface, fill_rect.topleft)


        # Container zeichnen (Bild mit Flüssigkeit drüber ODER Fallback)
        if use_container_image and scaled_container_image:
            # 1. Rotiertes Glas zeichnen
            rotated_container_image = pygame.transform.rotate(scaled_container_image, container_angle)
            rotated_rect = rotated_container_image.get_rect(center=container_rect.center)
            screen.blit(rotated_container_image, rotated_rect)
            # 2. Flüssigkeit als rotiertes Rechteck DARÜBER zeichnen
            liquid_height = container_height * current_liquid_fraction
            if liquid_height > 1:
                liquid_only_surface = pygame.Surface((container_width, container_height), pygame.SRCALPHA)
                liquid_only_surface.fill((0,0,0,0))
                pygame.draw.rect(liquid_only_surface, LIQUID_COLOR, (0, container_height - liquid_height, container_width, liquid_height))
                rotated_liquid = pygame.transform.rotate(liquid_only_surface, container_angle)
                rotated_liquid_rect = rotated_liquid.get_rect(center=container_rect.center)
                screen.blit(rotated_liquid, rotated_liquid_rect)
        else: # Fallback Container: Umriss + Flüssigkeit (ebenfalls rotiert)
             pygame.draw.rect(screen, CONTAINER_COLOR, container_rect, 2)
             liquid_height = container_height * current_liquid_fraction
             if liquid_height > 1:
                 liquid_only_surface = pygame.Surface((container_width, container_height), pygame.SRCALPHA)
                 liquid_only_surface.fill((0,0,0,0))
                 pygame.draw.rect(liquid_only_surface, LIQUID_COLOR, (0, container_height - liquid_height, container_width, liquid_height))
                 rotated_liquid = pygame.transform.rotate(liquid_only_surface, container_angle)
                 rotated_liquid_rect = rotated_liquid.get_rect(center=container_rect.center)
                 screen.blit(rotated_liquid, rotated_liquid_rect)

        # Partikel zeichnen
        for p in active_particles:
            p.draw(screen)

        # Kreise/Pillen zeichnen (Bild oder Fallback)
        for circle_rect in small_circles_rects:
             if use_circle_image and circle_image:
                 screen.blit(circle_image, circle_rect.topleft)
             else: # Fallback: Rote Kreise zeichnen
                 pygame.draw.circle(screen, RED, circle_rect.center, circle_radius)

        # UI zeichnen (Score, Fortschritt, Buttons)
        if font:
            score_text = font.render(f"Punkte: {score}", True, BLACK)
            screen.blit(score_text, (score_pos_x, score_pos_y))
        if info_font:
             progress_percent = (total_liquid_poured_in_target / (INITIAL_LIQUID_FRACTION * GOAL_FRACTION)) * 100 if INITIAL_LIQUID_FRACTION > 0 and GOAL_FRACTION > 0 else 0
             progress_percent = min(progress_percent, 100)
             progress_text = info_font.render(f"Ziel Füllung: {progress_percent:.0f}%", True, POUR_PROGRESS_COLOR)
             screen.blit(progress_text, (progress_pos_x, progress_pos_y))
        # Touch Buttons (Layout geändert)
        pygame.draw.rect(screen, GRAY if not touch_tilting_left else DARK_GRAY, tilt_left_button_rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, tilt_left_button_rect, 2, border_radius=5)
        if left_arrow_surf and left_arrow_rect : screen.blit(left_arrow_surf, left_arrow_rect)
        pygame.draw.rect(screen, GRAY if not touch_tilting_right else DARK_GRAY, tilt_right_button_rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, tilt_right_button_rect, 2, border_radius=5)
        if right_arrow_surf and right_arrow_rect: screen.blit(right_arrow_surf, right_arrow_rect)
        # Zurück Button
        if back_button_rect:
             back_button_color = GRAY
             try:
                 if back_button_rect.collidepoint(mouse_pos): back_button_color = DARK_GRAY
             except pygame.error: pass
             pygame.draw.rect(screen, back_button_color, back_button_rect)
             pygame.draw.rect(screen, BLACK, back_button_rect, 2)
             if back_text_surface and back_button_font:
                 screen.blit(back_text_surface, back_text_surface.get_rect(center=back_button_rect.center))

        # Bildschirm aktualisieren
        pygame.display.flip()

    # --- Ende der Spiel-Schleife ---
    print("INFO (zipWeed): Minispiel-Schleife beendet.")

# --- Ende der run_zip_weed_game Funktion ---

# --- Code für Standalone-Ausführung ---
if __name__ == "__main__":
    print("INFO: cockCrack.py wird eigenständig ausgeführt.")
    pygame.init()
    # Mixer explizit vorab initialisieren
    try:
         if not pygame.mixer.get_init():
             pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    except pygame.error as e:
         print(f"WARNUNG (Standalone Init): Mixer konnte nicht initialisiert werden: {e}")

    # Bildschirm erstellen
    try:
        _info = pygame.display.Info()
        _sw = _info.current_w
        _sh = _info.current_h
    except Exception:
        _sw = 800
        _sh = 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("CockCrack Minispiel (Standalone)")

    # Spiel starten
    try:
        run_zip_weed_game(standalone_screen) # Hauptfunktion aufrufen
    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}")
        traceback.print_exc() # Gibt den vollen Traceback aus
    finally:
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---