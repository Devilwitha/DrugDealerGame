# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os
import traceback
import time
import random
from . import cockCrackpart2 # NEU: Importiere das zweite Skript

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
CONTAINER_COLOR = BLACK
POUR_PROGRESS_COLOR = (50, 50, 50)

# --- NEU: Dateiname für Hintergrundbild ---
background_image_filename = "laborTable.png" # !!! ANPASSEN !!!

# --- Partikel Klasse ---
class Particle:
    """ Repräsentiert ein einzelnes Flüssigkeitspartikel. """
    def __init__(self, x, y, dx, dy, radius, color, lifetime):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = radius
        self.color = color
        self.lifetime = lifetime # In Sekunden
        self.initial_lifetime = lifetime

    def update(self, dt, gravity_y):
        """ Bewegt das Partikel und reduziert seine Lebenszeit. """
        self.dy += gravity_y * dt
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.lifetime -= dt
        return self.lifetime > 0 # Gibt True zurück, solange Partikel lebt

    def draw(self, surface):
        """ Zeichnet das Partikel auf die angegebene Oberfläche. """
        try:
            # Versuche mit Alpha zu zeichnen, wenn Farbformat passt (RGBA)
            if len(self.color) == 4:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            else: # Sonst nur RGB
                pygame.draw.circle(surface, self.color[:3], (int(self.x), int(self.y)), self.radius)
        except (TypeError, ValueError): # Fallback bei ungültiger Farbe
            pygame.draw.circle(surface, (0, 0, 0), (int(self.x), int(self.y)), self.radius)

# --- Hauptfunktion des Spiels ---
def run_cock_crack_game(screen_surface, start_pills, start_liquid, start_crack, liquid_id, pills_id):
    """ Führt das CockCrack Minispiel aus. """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    print(f"DEBUG (cockCrack): Nutze Screen-Größe: {actual_screen_size}")

    # Interne Statusvariablen initialisieren
    current_pills = start_pills
    current_liquid = start_liquid
    current_crack = start_crack
    liquid_name = liquid_id
    pills_name = pills_id
    print(f"DEBUG (cockCrack): Startwerte: Pills={current_pills} ('{pills_name}'), "
          f"Liquid={current_liquid} ('{liquid_name}'), Crack={current_crack}")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung ---
    score_sound = None
    no_resource_sound = None
    mixer_ok = False # Flag für erfolgreiche Mixer-Initialisierung
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (cockCrack): Mixer initialisiert.")
            mixer_ok = True
        except pygame.error as e:
            print(f"WARNUNG (cockCrack): Mixer fehlgeschlagen: {e}")
    else:
        print("DEBUG (cockCrack): Mixer war bereits initialisiert.")
        mixer_ok = True

    # --- Android Immersive Mode & Platform Detection ---
    is_android = False
    # ... (Code für Immersive Mode bleibt unverändert) ...
    try:
        from jnius import autoclass
        Build = autoclass('android.os.Build$VERSION')
        is_android = Build.SDK_INT > 0
    except ImportError: pass
    except Exception as e_jnius: print(f"WARNUNG (cockCrack): jnius Import/Check fehlgeschlagen: {e_jnius}")
    if is_android:
        print("DEBUG (cockCrack): Android erkannt.")
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
            if activity: activity.runOnUiThread(runnable); print("DEBUG (cockCrack): Immersive Mode sollte aktiv sein.")
        except Exception as e_immersive: print(f"FEHLER (cockCrack): Android Immersive Mode fehlgeschlagen: {e_immersive}"); is_android = False
    # --- Android Immersive Mode Ende ---


    # --- Proportionale Berechnungen ---
    if actual_screen_size[1] > actual_screen_size[0]: # Hochformat erkannt
        CALC_WIDTH, CALC_HEIGHT = actual_screen_size[1], actual_screen_size[0]
    else: # Querformat
        CALC_WIDTH, CALC_HEIGHT = actual_screen_size[0], actual_screen_size[1]

    target_width = max(1, int(CALC_WIDTH * (150 / ref_w)))
    target_height = max(1, int(CALC_HEIGHT * (200 / ref_h)))
    target_padding_right = max(1, int(CALC_WIDTH * (50 / ref_w)))
    target_padding_bottom = max(1, int(CALC_HEIGHT * (100 / ref_h)))
    target_x = actual_screen_size[0] - target_width - target_padding_right
    target_y = actual_screen_size[1] - target_height - target_padding_bottom
    target_rect = pygame.Rect(target_x, target_y, target_width, target_height)

    # --- Pfad-Setup für Assets ---
    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    project_root = os.path.abspath(os.path.join(script_dir_game, "..", "..", ".."))
    data_folder = os.path.join(project_root, "data")
    image_folder = os.path.join(data_folder, "bilder")
    sound_folder = os.path.join(data_folder, "sounds")
    print(f"DEBUG (cockCrack): Image folder: {image_folder}, Sound folder: {sound_folder}")

    # --- Dynamische Flüssigkeitsfarben ---
    # ... (Code für Flüssigkeitsfarben bleibt gleich) ...
    if liquid_name.lower() == "wasser":
        CURRENT_LIQUID_COLOR = (100, 150, 255, 200) # Hellblau RGBA
        CURRENT_PARTICLE_COLOR = (100, 150, 255, 180)
        CURRENT_TARGET_FILL_COLOR = (60, 100, 220, 180)
    else:
        print(f"WARNUNG: Unbekannter liquidName '{liquid_name}'. Nutze Standard (Hellblau).")
        CURRENT_LIQUID_COLOR = (100, 150, 255, 200)
        CURRENT_PARTICLE_COLOR = (100, 150, 255, 180)
        CURRENT_TARGET_FILL_COLOR = (60, 100, 220, 180)

    # --- Assets Laden ---

    # NEU: Hintergrundbild laden und skalieren
    scaled_background_image = None
    use_background_image = False
    try:
        background_path = os.path.join(image_folder, background_image_filename)
        # .convert() verwenden, wenn das Bild keine Transparenz hat (schneller)
        # .convert_alpha() verwenden, wenn Transparenz benötigt wird
        loaded_bg = pygame.image.load(background_path).convert()
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG: Hintergrundbild '{background_image_filename}' geladen und skaliert.")
    except Exception as e:
        print(f"WARNUNG: Hintergrundbild '{background_image_filename}' laden/skalieren fehlgeschlagen: {e}. Nutze weiße Füllung.")
        use_background_image = False

    # Ziel-Bild (Massbecher)
    target_image = None
    use_target_image = False
    target_image_filename = "massbecher.png"
    target_image_path = os.path.join(image_folder, target_image_filename)
    try:
        original_target_image = pygame.image.load(target_image_path).convert_alpha()
        if target_width > 0 and target_height > 0:
            target_image = pygame.transform.smoothscale(original_target_image, (target_width, target_height))
            use_target_image = True
    except Exception as e:
        print(f"WARNUNG: Ziel-Bild '{target_image_path}' laden fehlgeschlagen: {e}")

    # --- Pillen Setup ---
    NUM_CIRCLES = 4 # Wieviele Pillen-Slots angezeigt werden
    print(f"DEBUG (cockCrack): Zeichne Layout für {NUM_CIRCLES} Pillen.")
    circle_diameter = max(10, int(CALC_WIDTH * (40 / ref_w)))
    circle_radius = circle_diameter // 2
    circle_spacing = max(2, int(CALC_WIDTH * (8 / ref_w)))
    start_padding_left_circles = max(1, int(CALC_WIDTH * (50 / ref_w)))
    start_padding_top_circles = max(1, int(CALC_HEIGHT * (100 / ref_h)))
    start_positions_circles = []
    small_circles_rects = [] # Rects für Position und Kollision
    for i in range(NUM_CIRCLES):
        start_x = start_padding_left_circles + i * (circle_diameter + circle_spacing)
        start_y = start_padding_top_circles
        start_positions_circles.append((start_x, start_y))
        small_circles_rects.append(pygame.Rect(start_x, start_y, circle_diameter, circle_diameter))

    # Wie viele Pillen tatsächlich ins Ziel müssen, hängt vom Inventar ab (max. NUM_CIRCLES)
    pills_needed_for_score = min(NUM_CIRCLES, current_pills)
    print(f"DEBUG (cockCrack): Pillen benötigt für Punkt: {pills_needed_for_score} (Inventar: {current_pills})")

    circle_image = None
    use_circle_image = False
    # Pillenbild basierend auf pills_name auswählen
    if pills_name.lower() == "tafelgan": pill_image_filename = "tafelgan.png"
    else: pill_image_filename = "testpill.png" # Fallback
    if pills_name.lower() not in ["tafelgan", "testpill"]: # Warne bei unbekannten Namen, aber nutze Fallback
        print(f"WARNUNG: Unbekannter pillsName '{pills_name}'. Nutze '{pill_image_filename}'.")

    print(f"DEBUG (cockCrack): Versuche Pillen-Bild: '{pill_image_filename}'")
    circle_image_path = os.path.join(image_folder, pill_image_filename)
    try:
        original_circle_image = pygame.image.load(circle_image_path).convert_alpha()
        if circle_diameter > 0:
            circle_image = pygame.transform.smoothscale(original_circle_image, (circle_diameter, circle_diameter))
            use_circle_image = True
    except Exception as e:
        print(f"WARNUNG: Pillen-Bild '{circle_image_path}' laden fehlgeschlagen: {e}. Nutze rote Kreise.")

    circle_gravity_value = max(1, int(CALC_HEIGHT * (10 / ref_h))) # Fallgeschwindigkeit
    circles_falling = [False] * NUM_CIRCLES # Status für jede Pille

    # Container Setup
    container_width = max(20, int(CALC_WIDTH * (100 / ref_w)))
    container_height = max(60, int(CALC_HEIGHT * (120 / ref_h) * 2)) # Höhe angepasst für besseres Aussehen
    container_start_x = max(10, int(CALC_WIDTH * (100 / ref_w)))
    container_start_y = screen_height - container_height - max(10, int(CALC_HEIGHT * (50 / ref_h)))
    container_rect = pygame.Rect(container_start_x, container_start_y, container_width, container_height)
    container_angle = 0.0 # Kippwinkel
    TILT_SPEED, MAX_TILT_ANGLE, POUR_THRESHOLD_ANGLE = 90.0, 85.0, 40.0 # Kipp-Parameter
    POUR_RATE, INITIAL_LIQUID_FRACTION, GOAL_FRACTION = 0.5, 0.8, 0.5 # Gieß-Parameter
    current_liquid_fraction = INITIAL_LIQUID_FRACTION # Startfüllstand im Container (0.0 bis 1.0)
    total_liquid_poured_in_target = 0.0 # Wie viel im Ziel angekommen ist
    container_falling = False
    # Container Bild
    container_image_path = os.path.join(image_folder, "glass.png") # Bild für den Container
    scaled_container_image = None
    use_container_image = False
    try:
        original_container_image = pygame.image.load(container_image_path).convert_alpha()
        if container_width > 0 and container_height > 0:
            scaled_container_image = pygame.transform.smoothscale(original_container_image, (container_width, container_height))
            use_container_image = True
    except Exception as e:
        print(f"WARNUNG: Container-Bild '{container_image_path}' laden fehlgeschlagen: {e}")

    # Partikel System Setup
    active_particles = []
    PARTICLE_LIFETIME, PARTICLE_RADIUS, PARTICLES_PER_SECOND = 0.8, 3, 150
    PARTICLE_INITIAL_VELOCITY_Y, PARTICLE_SPREAD, PARTICLE_GRAVITY = 50, 40, 400.0

    # --- Schriftarten ---
    BASE_GAME_FONT_SIZE = 36
    game_font_size = max(12, int(screen_height * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try: font = pygame.font.SysFont("arial", game_font_size)
    except: font = pygame.font.Font(None, game_font_size)
    if not font: font = pygame.font.Font(None, 30); game_font_size = 30

    BASE_INFO_FONT_SIZE = 18
    info_font_size = max(10, int(screen_height * (BASE_INFO_FONT_SIZE / FONT_SIZE_REF_H)))
    info_font = None
    try: info_font = pygame.font.SysFont("arial", info_font_size)
    except: info_font = pygame.font.Font(None, info_font_size)
    if not info_font: info_font = pygame.font.Font(None, 20); info_font_size = 20

    status_pos_x = max(1, int(screen_width * (10 / ref_w)))
    status_pos_y = max(1, int(screen_height * (10 / ref_h)))
    progress_pos_y = status_pos_y + max(12, game_font_size) + 5
    resource_pos_y = progress_pos_y + max(10, info_font_size) + 5

    # --- Sounds laden ---
    sound_filename_score = "bagFinish.wav"
    sound_filename_no_resource = "error.wav"
    sound_path_score = os.path.join(sound_folder, sound_filename_score)
    sound_path_no_resource = os.path.join(sound_folder, sound_filename_no_resource)
    if mixer_ok: # Nur laden, wenn Mixer initialisiert wurde
        try:
            score_sound = pygame.mixer.Sound(sound_path_score); score_sound.set_volume(0.9)
        except Exception as e:
            print(f"WARNUNG: Score-Sound laden fehlgeschlagen: {e}")
            score_sound = None
        try:
            no_resource_sound = pygame.mixer.Sound(sound_path_no_resource); no_resource_sound.set_volume(0.7)
        except Exception as e:
            print(f"WARNUNG: NoResource-Sound laden fehlgeschlagen: {e}")
            no_resource_sound = None

    # --- UI Elemente ---
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

    # Touch-Buttons für Kippen
    touch_button_size = max(40, int(CALC_WIDTH * 0.1))
    tilt_right_button_rect = pygame.Rect(
        touch_button_size // 2, screen_height - touch_button_size * 1.5,
        touch_button_size, touch_button_size)
    tilt_left_button_rect = pygame.Rect(
        touch_button_size // 2, tilt_right_button_rect.top - touch_button_size - touch_button_size // 4,
        touch_button_size, touch_button_size)
    touch_button_font = None; left_arrow_surf, right_arrow_surf = None, None
    left_arrow_rect, right_arrow_rect = None, None
    try:
        touch_button_font = pygame.font.Font(None, touch_button_size // 2)
        left_arrow_surf = touch_button_font.render(" < ", True, BLACK)
        right_arrow_surf = touch_button_font.render(" > ", True, BLACK)
        left_arrow_rect = left_arrow_surf.get_rect(center=tilt_left_button_rect.center)
        right_arrow_rect = right_arrow_surf.get_rect(center=tilt_right_button_rect.center)
    except: pass

    # --- Spielzustands-Variablen (Interaktion) ---
    dragging_circle_index = -1 # Welche Pille wird gezogen (-1 = keine)
    dragging_container = False # Wird der Container gezogen?
    container_offset_x, container_offset_y = 0, 0 # Offset für Container-Drag
    offset_x, offset_y = 0, 0 # Offset für Pillen-Drag
    tilting_left, tilting_right = False, False # Status Tastatur-Kippen
    touch_tilting_left, touch_tilting_right = False, False # Status Touch-Kippen
    game_over_delay_timer = 0.0 # Verzögerung nach Erfolg/Misserfolg zum Reset
    particle_emission_accumulator = 0.0 # Für gleichmäßige Partikelemission

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1) # Delta Time, max 0.1s
        last_time = current_time

        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Nur den Loop beenden, nicht die ganze App
                print("WARNUNG (cockCrack): QUIT Event empfangen. Beende nur Minispiel-Loop.")
                running = False
                continue # Wichtig: Zum nächsten Schleifendurchlauf, um quit() zu vermeiden

            # Keyboard Events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue # Wichtig
                # Kippen nur mit Liquid möglich
                if current_liquid >= 1:
                    if event.key == pygame.K_q: tilting_left = True
                    if event.key == pygame.K_e: tilting_right = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_q: tilting_left = False
                if event.key == pygame.K_e: tilting_right = False

            # Mouse Button Down Events
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    # Zurück Button
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False; continue

                    touch_handled = False
                    # Touch Kippen (nur mit Liquid)
                    if is_android and current_liquid >= 1:
                        if tilt_left_button_rect.collidepoint(event.pos):
                            touch_tilting_left = True; touch_handled = True
                        if tilt_right_button_rect.collidepoint(event.pos):
                            touch_tilting_right = True; touch_handled = True
                    if touch_handled: continue # Wenn Touch-Button geklickt, nicht weiter prüfen

                    clicked_on_circle = False
                    # Pillen Klick (nur wenn Pillen vorhanden sind)
                    if current_pills >= 1:
                        # Prüfe von oben nach unten (visuell), damit die oberste Pille gewählt wird
                        for i in range(NUM_CIRCLES - 1, -1, -1):
                            if i < len(small_circles_rects) and small_circles_rects[i].collidepoint(event.pos):
                                dragging_circle_index = i
                                circles_falling[i] = False # Stoppe Fall, wenn gegriffen
                                dragging_container = False # Nur eines kann gezogen werden
                                clicked_on_circle = True
                                offset_x = small_circles_rects[i].x - event.pos[0]
                                offset_y = small_circles_rects[i].y - event.pos[1]
                                break # Nur eine Pille auf einmal ziehen

                    # Container Klick (nur wenn keine Pille geklickt wurde und Liquid vorhanden)
                    if not clicked_on_circle and current_liquid >= 1 and container_rect.collidepoint(event.pos):
                        dragging_container = True
                        container_falling = False # Stoppe Fall, wenn gegriffen
                        dragging_circle_index = -1 # Keine Pille ziehen
                        container_offset_x = container_rect.x - event.pos[0]
                        container_offset_y = container_rect.y - event.pos[1]

            # Mouse Button Up Events
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if is_android: # Touch-Kippen loslassen
                        touch_tilting_left = False
                        touch_tilting_right = False

                    # Pille loslassen -> Prüfen ob sie fallen soll
                    if dragging_circle_index != -1:
                        released_index = dragging_circle_index
                        dragging_circle_index = -1 # Nicht mehr ziehen
                        current_pill_rect = small_circles_rects[released_index]

                        # Ist die Pille abgestützt? (Boden oder Zielboden)
                        is_supported = False
                        if current_pill_rect.bottom >= screen_height: is_supported = True
                        # Prüfen, ob sie auf dem Boden des Ziels liegt
                        if target_rect and not is_supported:
                            # Horizontal innerhalb oder überlappend mit Ziel?
                            is_horz_overlap = (current_pill_rect.right > target_rect.left and
                                               current_pill_rect.left < target_rect.right)
                            # Ist der Boden der Pille auf oder unter dem Boden des Ziels?
                            is_on_target_bottom = (is_horz_overlap and
                                                   current_pill_rect.bottom >= target_rect.bottom)
                            if is_on_target_bottom: is_supported = True

                        # Soll fallen, wenn NICHT abgestützt UND NICHT (komplett) im Zielbereich ist
                        # Oder wenn es gar kein Ziel gibt
                        should_fall = False
                        if target_rect:
                             is_inside_target = target_rect.contains(current_pill_rect)
                             if not is_supported and not is_inside_target:
                                 should_fall = True
                        elif not is_supported: # Kein Ziel, fällt wenn nicht am Boden
                             should_fall = True

                        if should_fall: circles_falling[released_index] = True


                    # Container loslassen -> Prüfen ob er fallen soll (nur non-Android)
                    elif dragging_container:
                        dragging_container = False
                        # Auf Desktop: Container fällt, wenn losgelassen und nicht am Boden/auf Ziel
                        if not is_android and container_rect.bottom < screen_height:
                            on_target_top = False
                            # Ist er über dem Zielbereich?
                            if target_rect:
                                is_horz_overlap = (container_rect.right > target_rect.left and
                                                   container_rect.left < target_rect.right)
                                # Ist der Boden des Containers auf oder über der Oberkante des Ziels?
                                if is_horz_overlap and container_rect.bottom >= target_rect.top:
                                    on_target_top = True # Wird vom Ziel gestützt (vereinfacht)
                            # Fällt, wenn weder am Boden noch vom Ziel gestützt
                            container_falling = not on_target_top

            # Mouse Motion Events
            if event.type == pygame.MOUSEMOTION:
                # Pillen bewegen
                if dragging_circle_index != -1:
                    current_rect = small_circles_rects[dragging_circle_index]
                    potential_x = event.pos[0] + offset_x
                    potential_y = event.pos[1] + offset_y
                    # Begrenze auf Bildschirmränder
                    final_x = max(0, min(potential_x, screen_width - current_rect.width))
                    final_y = max(0, min(potential_y, screen_height - current_rect.height))
                    potential_rect = pygame.Rect(final_x, final_y, current_rect.width, current_rect.height)

                    # Kollisionsprüfung mit Ziel (nur wenn Ziel existiert)
                    if target_rect and potential_rect.colliderect(target_rect):
                        was_outside = not target_rect.contains(current_rect)
                        is_inside = target_rect.contains(potential_rect)

                        # Vereinfachte Kollisionslogik:
                        # Wenn man von außen versucht, hineinzuziehen, stoppe an den Kanten
                        # Wenn man innen ist, bleibe innerhalb.
                        # (Dies verhindert das "Hineinschieben" durch Wände)

                        # Wenn aktuell ganz drin, halte es drin
                        if target_rect.contains(current_rect):
                             if potential_rect.left < target_rect.left: final_x = target_rect.left
                             elif potential_rect.right > target_rect.right: final_x = target_rect.right - current_rect.width
                             if potential_rect.top < target_rect.top: final_y = target_rect.top
                             elif potential_rect.bottom > target_rect.bottom: final_y = target_rect.bottom - current_rect.height
                        # Wenn aktuell draußen, aber Kollision mit Ziel
                        elif was_outside:
                             # Kam von links? Stoppe links.
                             if current_rect.right <= target_rect.left and potential_rect.right > target_rect.left and potential_rect.bottom > target_rect.top :
                                 final_x = target_rect.left - current_rect.width
                             # Kam von rechts? Stoppe rechts.
                             elif current_rect.left >= target_rect.right and potential_rect.left < target_rect.right and potential_rect.bottom > target_rect.top:
                                 final_x = target_rect.right
                             # Kam von unten? Stoppe unten (theoretisch, eher selten)
                             # elif current_rect.top >= target_rect.bottom and potential_rect.top < target_rect.bottom:
                             #      final_y = target_rect.bottom
                             # Kam von oben? Stoppe oben (wichtiger)
                             elif current_rect.bottom <= target_rect.top and potential_rect.bottom > target_rect.top and potential_rect.right > target_rect.left and potential_rect.left < target_rect.right:
                                 final_y = target_rect.top - current_rect.height

                    current_rect.topleft = (final_x, final_y)

                # Container bewegen
                elif dragging_container:
                    potential_x = event.pos[0] + container_offset_x
                    potential_y = event.pos[1] + container_offset_y
                    # Begrenze auf Bildschirmränder
                    final_x = max(0, min(potential_x, screen_width - container_rect.width))
                    final_y = max(0, min(potential_y, screen_height - container_rect.height))
                    container_rect.topleft = (final_x, final_y)

        # --- Spiel-Logik Update ---
        if game_over_delay_timer <= 0: # Nur updaten, wenn kein Reset läuft
            # Container Kippen
            effective_tilt = 0
            if current_liquid >= 1: # Nur kippen, wenn Flüssigkeit da ist
                if tilting_left or touch_tilting_left: effective_tilt -= 1
                if tilting_right or touch_tilting_right: effective_tilt += 1
            if effective_tilt != 0:
                container_angle -= effective_tilt * TILT_SPEED * dt # Winkel ändern
                container_angle = max(-MAX_TILT_ANGLE, min(MAX_TILT_ANGLE, container_angle)) # Begrenzen

            # Container Gießen & Partikel
            can_pour = (abs(container_angle) > POUR_THRESHOLD_ANGLE and current_liquid_fraction > 0 and current_liquid >= 1)
            if can_pour:
                # Wieviel Flüssigkeit ausgießen
                pour_amount = min(POUR_RATE * INITIAL_LIQUID_FRACTION * dt, current_liquid_fraction)
                current_liquid_fraction -= pour_amount # Reduziere Füllstand im Container
                poured_this_frame_total = pour_amount

                # Wo kommen Partikel raus? (vereinfacht)
                spout_x = (container_rect.left + PARTICLE_RADIUS + 1 if container_angle > 0 # Gekippt nach rechts -> linke Kante
                           else container_rect.right - PARTICLE_RADIUS - 1) # Gekippt nach links -> rechte Kante
                spout_y = container_rect.top + PARTICLE_RADIUS + 1 # Oberkante

                # Prüfen, ob Ausguss über dem Ziel ist
                poured_into_target_area = False
                if target_rect:
                   poured_into_target_area = (target_rect.left < spout_x < target_rect.right and
                                              spout_y < target_rect.bottom) # Über dem Ziel (auch über dem Boden)

                if poured_into_target_area:
                    # Erhöhe Füllstand im Ziel, max. bis zum ursprünglichen Container-Inhalt
                    total_liquid_poured_in_target = min(total_liquid_poured_in_target + poured_this_frame_total, INITIAL_LIQUID_FRACTION)

                # Partikel erzeugen
                particle_emission_this_frame = poured_this_frame_total * PARTICLES_PER_SECOND
                particle_emission_accumulator += particle_emission_this_frame
                num_particles_to_emit = int(particle_emission_accumulator)
                if num_particles_to_emit > 0:
                    particle_emission_accumulator -= num_particles_to_emit # Rest für nächsten Frame behalten
                    for _ in range(num_particles_to_emit):
                        # Leichte Variation der Startposition
                        emit_x = spout_x + random.uniform(-PARTICLE_RADIUS, PARTICLE_RADIUS)
                        emit_y = spout_y + random.uniform(-PARTICLE_RADIUS, PARTICLE_RADIUS)
                        # Startgeschwindigkeit basierend auf Winkel und Zufall
                        rad_angle = math.radians(container_angle); vel_af = math.sin(rad_angle) # Einfluss des Winkels
                        init_dx = random.uniform(-PARTICLE_SPREAD, PARTICLE_SPREAD) - vel_af * 30 # Seitliche Streuung + Winkel-Drift
                        init_dy = PARTICLE_INITIAL_VELOCITY_Y + random.uniform(0, 20) # Grundgeschwindigkeit + Variation
                        active_particles.append(Particle(emit_x, emit_y, init_dx, init_dy, PARTICLE_RADIUS, CURRENT_PARTICLE_COLOR, PARTICLE_LIFETIME))

            # Physik für Container (Fall) - nur Desktop
            if container_falling and not dragging_container and not is_android:
                potential_cont_rect = container_rect.move(0, circle_gravity_value) # Wohin würde er fallen?
                stopped = False
                # Am Boden angekommen?
                if potential_cont_rect.bottom >= screen_height:
                    container_rect.bottom = screen_height; stopped = True
                # Auf Ziel gelandet?
                elif target_rect:
                    is_horz_overlap = (potential_cont_rect.right > target_rect.left and potential_cont_rect.left < target_rect.right)
                    # Prüfen, ob er die Oberkante des Ziels kreuzt
                    if is_horz_overlap and container_rect.bottom <= target_rect.top and potential_cont_rect.bottom > target_rect.top:
                        container_rect.bottom = target_rect.top; stopped = True
                # Wenn gestoppt, nicht weiter fallen lassen
                if stopped: container_falling = False
                else: container_rect.move_ip(0, circle_gravity_value) # Weiter fallen

            # Physik für Kreise (Fall)
            for i in range(NUM_CIRCLES):
                if circles_falling[i] and dragging_circle_index != i: # Nur wenn sie fallen soll und nicht gezogen wird
                    current_rect = small_circles_rects[i]
                    potential_rect = current_rect.move(0, circle_gravity_value) # Wohin würde sie fallen?
                    stopped_falling = False
                    # Am Boden angekommen?
                    if potential_rect.bottom >= screen_height:
                        current_rect.bottom = screen_height; stopped_falling = True
                    # Auf Zielboden gelandet?
                    elif target_rect:
                        is_horz_overlap = (potential_rect.right > target_rect.left and potential_rect.left < target_rect.right)
                        # Prüfen, ob sie den Boden des Ziels kreuzt
                        will_cross_target_bottom = (current_rect.bottom <= target_rect.bottom and potential_rect.bottom > target_rect.bottom)
                        if is_horz_overlap and will_cross_target_bottom:
                            current_rect.bottom = target_rect.bottom; stopped_falling = True
                    # Wenn gestoppt, nicht weiter fallen lassen
                    if stopped_falling: circles_falling[i] = False
                    else: current_rect.move_ip(0, circle_gravity_value) # Weiter fallen

            # Partikel Update & Cleanup
            # Update Position und Lebenszeit, entferne tote Partikel
            active_particles = [p for p in active_particles if p.update(dt, PARTICLE_GRAVITY)]
            # Entferne Partikel, die im Ziel unter den Boden fallen oder unter den Bildschirm fallen
            active_particles = [p for p in active_particles if not (
                                  (target_rect and p.y > target_rect.bottom and target_rect.left < p.x < target_rect.right) or
                                  (p.y > screen_height - p.radius) )]

        # --- Win Condition & Reset ---
        if game_over_delay_timer > 0: # Läuft der Reset-Timer?
            game_over_delay_timer -= dt
            if game_over_delay_timer <= 0: # Timer abgelaufen -> Reset durchführen
                # Reset Container
                container_angle = 0.0
                current_liquid_fraction = INITIAL_LIQUID_FRACTION # Wieder auffüllen
                total_liquid_poured_in_target = 0.0 # Ziel leeren
                container_rect.topleft = (container_start_x, container_start_y) # An Startposition
                container_falling = False
                tilting_left = tilting_right = touch_tilting_left = touch_tilting_right = False
                dragging_container = False
                # Reset Partikel
                active_particles = []
                # Reset Pillen
                dragging_circle_index = -1
                for i in range(NUM_CIRCLES):
                    if i < len(small_circles_rects):
                        small_circles_rects[i].topleft = start_positions_circles[i] # An Startposition
                    circles_falling[i] = False # Nicht fallend
                # Aktualisiere, wie viele Pillen für nächsten Score gebraucht werden
                pills_needed_for_score = min(NUM_CIRCLES, current_pills)
                print("DEBUG (cockCrack): Spiel zurückgesetzt nach Erfolg/Reset.")
        else: # Kein Reset-Timer aktiv -> Prüfe auf Gewinnbedingung
            # Bedingung 1: Genug Flüssigkeit im Ziel?
            target_fill_goal = INITIAL_LIQUID_FRACTION * GOAL_FRACTION
            liquid_condition_met = total_liquid_poured_in_target >= target_fill_goal

            # Bedingung 2: Alle *benötigten* Pillen im Ziel und nicht fallend?
            all_needed_circles_in_target_and_static = False
            if target_rect and pills_needed_for_score > 0:
                # Prüfe nur die ersten 'pills_needed_for_score' Slots
                needed_indices = range(pills_needed_for_score)
                all_needed_circles_in_target_and_static = all(
                    (idx < len(small_circles_rects) and target_rect.contains(small_circles_rects[idx]) and not circles_falling[idx])
                    for idx in needed_indices
                )
            elif pills_needed_for_score <= 0: # Wenn keine Pillen gebraucht werden (z.B. 0 im Inventar), ist die Bedingung erfüllt
                all_needed_circles_in_target_and_static = True

            # Wenn beide Bedingungen erfüllt sind:
            if liquid_condition_met and all_needed_circles_in_target_and_static:
                 # Prüfe, ob Ressourcen vorhanden sind (mindestens 1 Pille und 1 Einheit Flüssigkeit)
                if current_pills >= 1 and current_liquid >= 1:

                    # +++ START NEU (Aufruf von Teil 2) +++
                    print("INFO: Bedingungen erfüllt. Starte cockCrackPart2 Minispiel...")

                    # Optional: Kurze visuelle Überblendung oder Pause
                    # screen.fill(BLACK) # Beispiel: Schwarzblende
                    # pygame.display.flip()
                    # time.sleep(0.1)

                    # Rufe das zweite Minispiel auf und warte auf das Ergebnis (0 oder 1)
                    points_from_part2 = cockCrackpart2.run_cock_crack_game(
                        screen,
                        current_pills,    # Übergib aktuelle Werte, falls Teil 2 sie braucht
                        current_liquid,
                        0,                # Crack-Zähler für Teil 2 ist hier irrelevant
                        liquid_name,      # Namen übergeben
                        pills_name
                    )

                    print(f"DEBUG: cockCrackPart2 beendet. Ergebnis: {points_from_part2}")

                    if points_from_part2 > 0:
                        # Erfolg in Teil 2! Verbrauche Ressourcen und zähle Punkt in Teil 1
                        print("INFO: Punkt in cockCrackPart2 erzielt. Verbrauche Ressourcen.")
                        current_pills -= 1    # Eine Pille verbraucht
                        current_liquid -= 1   # Eine Einheit Flüssigkeit verbraucht
                        current_crack += points_from_part2 # Füge den erzielten Punkt hinzu (sollte 1 sein)

                        print(f"DEBUG: Neue Ressourcen: Pills={current_pills}, Liquid={current_liquid}, Crack={current_crack}")
                        if score_sound:
                            score_sound.play()
                        game_over_delay_timer = 1.0 # Starte Reset-Verzögerung in Teil 1
                    else:
                        # Teil 2 wurde ohne Punkt beendet (z.B. Zurück-Button)
                        print("INFO: cockCrackPart2 ohne Punkt beendet. Keine Ressourcen verbraucht.")
                        if no_resource_sound: no_resource_sound.play() # Sound für Abbruch/Fehler
                        # KEIN Reset-Timer hier, damit der Spieler es direkt nochmal versuchen kann
                        # oder die Positionen korrigieren kann.
                    # +++ ENDE NEU +++

                else: # Bedingungen erfüllt, aber keine Ressourcen mehr
                    print("INFO: Ziel erreicht, aber nicht genügend Pillen/Liquid!")
                    if no_resource_sound: no_resource_sound.play()
                    # Reset auslösen, damit man nicht im "gewonnen aber kein Score" Zustand bleibt?
                    game_over_delay_timer = 1.0 # Startet Reset, auch wenn keine Ressourcen da waren

        # --- Zeichnen ---
        # Hintergrund
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        else:
            screen.fill(WHITE) # Fallback weiß

        # Ziel zeichnen
        if target_rect:
            if use_target_image and target_image:
                # Zeichne zuerst den Füllstand (damit er hinter dem Bild ist)
                target_fill_goal = INITIAL_LIQUID_FRACTION * GOAL_FRACTION
                if target_fill_goal > 0 and total_liquid_poured_in_target > 0:
                    target_fill_ratio = min(1.0, total_liquid_poured_in_target / target_fill_goal)
                    # Füllhöhe relativ zur Zielhöhe
                    fill_height = int(target_rect.height * target_fill_ratio)
                    if fill_height > 0:
                        fill_rect = pygame.Rect(target_rect.x, target_rect.bottom - fill_height, target_rect.width, fill_height)
                        # Transparente Oberfläche für den Füllstand
                        fill_surface = pygame.Surface(fill_rect.size, pygame.SRCALPHA)
                        fill_surface.fill(CURRENT_TARGET_FILL_COLOR) # RGBA Farbe verwenden
                        screen.blit(fill_surface, fill_rect.topleft)

                # Zeichne das Zielbild über den Füllstand
                screen.blit(target_image, target_rect.topleft)
            else: # Fallback Linien für Ziel
                pygame.draw.line(screen, TARGET_DRAW_COLOR, target_rect.bottomleft, target_rect.topleft, 3)
                pygame.draw.line(screen, TARGET_DRAW_COLOR, target_rect.bottomright, target_rect.topright, 3)
                pygame.draw.line(screen, TARGET_DRAW_COLOR, target_rect.bottomleft, target_rect.bottomright, 3)
                 # Füllstand auch für Fallback zeichnen
                target_fill_goal = INITIAL_LIQUID_FRACTION * GOAL_FRACTION
                if target_fill_goal > 0 and total_liquid_poured_in_target > 0:
                    target_fill_ratio = min(1.0, total_liquid_poured_in_target / target_fill_goal)
                    fill_height = int(target_rect.height * target_fill_ratio)
                    if fill_height > 0:
                         fill_rect = pygame.Rect(target_rect.x+1, target_rect.bottom - fill_height, target_rect.width-2, fill_height) # Etwas schmaler
                         fill_surface = pygame.Surface(fill_rect.size, pygame.SRCALPHA)
                         fill_surface.fill(CURRENT_TARGET_FILL_COLOR)
                         screen.blit(fill_surface, fill_rect.topleft)


        # Container zeichnen (nur wenn Liquid vorhanden)
        if current_liquid >= 1:
            if use_container_image and scaled_container_image:
                # Original Bild rotieren
                rotated_img = pygame.transform.rotate(scaled_container_image, container_angle)
                # Neue Bounding Box nach Rotation berechnen, zentriert auf alter Position
                rot_rect = rotated_img.get_rect(center=container_rect.center)
                # Rotiertes Bild zeichnen
                screen.blit(rotated_img, rot_rect)

                # Flüssigkeit im Container (als separate rotierte Oberfläche)
                liquid_h_abs = container_height * current_liquid_fraction # Absolute Höhe
                if liquid_h_abs > 1: # Nur zeichnen, wenn Höhe sichtbar ist
                    # Erzeuge temporäre Oberfläche für die Flüssigkeit (Größe des Containers)
                    liquid_surf = pygame.Surface((container_width, container_height), pygame.SRCALPHA)
                    liquid_surf.fill((0,0,0,0)) # Komplett transparent machen
                    # Zeichne Rechteck für Flüssigkeit UNTEN in diese Oberfläche
                    pygame.draw.rect(liquid_surf, CURRENT_LIQUID_COLOR,
                                     (0, container_height - liquid_h_abs, container_width, liquid_h_abs))
                    # Rotiere die Flüssigkeits-Oberfläche um den gleichen Winkel
                    rotated_liq = pygame.transform.rotate(liquid_surf, container_angle)
                    # Zentriere die rotierte Flüssigkeit ebenfalls
                    rot_liq_rect = rotated_liq.get_rect(center=container_rect.center)
                    # Zeichne die rotierte Flüssigkeit
                    screen.blit(rotated_liq, rot_liq_rect)

            else: # Fallback Container (Rechteck)
                pygame.draw.rect(screen, CONTAINER_COLOR, container_rect, 2) # Nur Umriss
                # Flüssigkeit im Fallback-Container (nicht rotiert)
                liquid_h = container_rect.height * current_liquid_fraction
                if liquid_h > 1:
                    liq_rect = pygame.Rect(container_rect.left + 1, container_rect.bottom - liquid_h,
                                          container_rect.width - 2, liquid_h)
                    # Benutze RGB-Teil der Farbe, da SRCALPHA hier nicht direkt geht
                    pygame.draw.rect(screen, CURRENT_LIQUID_COLOR[:3], liq_rect)

        # Partikel zeichnen
        for p in active_particles:
            p.draw(screen)

        # Pillen zeichnen (nur wenn Pillen vorhanden)
        if current_pills >= 1:
            for i in range(NUM_CIRCLES):
                 # Zeichne nur die Slots, für die es auch Rects gibt
                if i < len(small_circles_rects):
                    current_rect = small_circles_rects[i]
                    if use_circle_image and circle_image:
                        screen.blit(circle_image, current_rect.topleft)
                    else: # Fallback roter Kreis
                        pygame.draw.circle(screen, RED, current_rect.center, circle_radius)

        # UI zeichnen (Texte)
        if font:
            crack_text = font.render(f"Crack: {current_crack}", True, RED)
            screen.blit(crack_text, (status_pos_x, status_pos_y))
        if info_font:
            # Fortschritt der Zielfüllung anzeigen
            target_fill_goal = INITIAL_LIQUID_FRACTION * GOAL_FRACTION
            prog_perc = (total_liquid_poured_in_target / target_fill_goal) * 100 if target_fill_goal > 0 else 0
            prog_text = info_font.render(f"Ziel Füllung: {min(prog_perc, 100):.0f}%", True, POUR_PROGRESS_COLOR)
            screen.blit(prog_text, (status_pos_x, progress_pos_y))
            # Ressourcen anzeigen
            pills_text = info_font.render(f"{pills_name}: {current_pills}", True, BLACK)
            liquid_text = info_font.render(f"{liquid_name}: {current_liquid}", True, BLACK)
            screen.blit(pills_text, (status_pos_x, resource_pos_y))
            screen.blit(liquid_text, (status_pos_x, resource_pos_y + info_font_size + 5))

        # Touch Buttons zeichnen (nur auf Android)
        if is_android:
            pygame.draw.rect(screen, GRAY if not touch_tilting_left else DARK_GRAY, tilt_left_button_rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, tilt_left_button_rect, 2, border_radius=5)
            if left_arrow_surf and left_arrow_rect: screen.blit(left_arrow_surf, left_arrow_rect)

            pygame.draw.rect(screen, GRAY if not touch_tilting_right else DARK_GRAY, tilt_right_button_rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, tilt_right_button_rect, 2, border_radius=5)
            if right_arrow_surf and right_arrow_rect: screen.blit(right_arrow_surf, right_arrow_rect)

        # Zurück Button zeichnen
        if back_button_rect:
            btn_color = GRAY
            # Hover-Effekt
            if back_button_rect.collidepoint(mouse_pos): btn_color = DARK_GRAY
            pygame.draw.rect(screen, btn_color, back_button_rect)
            pygame.draw.rect(screen, BLACK, back_button_rect, 2) # Rand
            # Text auf Button
            if back_text_surface and back_button_font:
                text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                screen.blit(back_text_surface, text_rect)

        pygame.display.flip() # Bildschirm aktualisieren
        clock.tick(60) # Framerate begrenzen

    # --- Ende der Spiel-Schleife ---
    print("INFO (cockCrack): Minispiel-Schleife beendet.")

    # Gebe die finalen Werte zurück an das Hauptspiel
    return current_pills, current_liquid, current_crack

# --- Ende der run_cock_crack_game Funktion ---

# --- Code für Standalone-Ausführung (Testzwecke) ---
if __name__ == "__main__":
    print("INFO: cockCrack.py wird eigenständig ausgeführt.")
    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    # Versuche, Bildschirmgröße zu ermitteln, sonst Standard
    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600
    # Erstelle Fenster (skalierbar/resizeable für Test)
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("CockCrack Minispiel (Standalone)")

    try:
        # Startwerte für den Standalone-Test
        start_pills_sa = 5
        start_liquid_sa = 3
        start_crack_sa = 0
        liquid_name_sa = "Wasser"
        pills_name_sa = "Tafelgan"
        print(f"\n--- Starte Standalone CockCrack mit: Pills={start_pills_sa}, Liquid={start_liquid_sa}, "
              f"Crack={start_crack_sa}, LiquidName='{liquid_name_sa}', PillsName='{pills_name_sa}' ---\n")

        # Rufe die Hauptfunktion auf
        result_sa = run_cock_crack_game(
            standalone_screen, start_pills_sa, start_liquid_sa, start_crack_sa, liquid_name_sa, pills_name_sa
        )

        # Gib das Ergebnis aus
        if result_sa:
            print(f"\n--- Standalone CockCrack Beendet. Ergebnis: ---")
            print(f"  Verbleibende Pillen: {result_sa[0]}")
            print(f"  Verbleibende Liquid: {result_sa[1]}")
            print(f"  Produziertes Crack:  {result_sa[2]}")
            print("-------------------------------------------\n")
        else:
            print("\n--- Standalone CockCrack Beendet. Kein Ergebnis zurückgegeben. ---\n")

    except Exception as e_main:
        print(f"\nFEHLER in Standalone Ausführung: {e_main}")
        traceback.print_exc() # Gib detaillierte Fehlermeldung aus
    finally:
        pygame.quit() # Pygame sauber beenden
        sys.exit() # Skript beenden
# --- Ende Standalone-Code ---