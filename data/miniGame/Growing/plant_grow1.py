# -*- coding: utf-8 -*-
# pygame_minigame_earth_filler_v6_fixed_indent2.py - Mit korrekter Formatierung ALLER Blöcke
import pygame
import sys
import os
import traceback
import time
import random
import math

# --- Android Immersive Mode & Platform Detection ---
is_android = False
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    print("DEBUG (EarthFiller): Pyjnius importiert.")
    Build = autoclass('android.os.Build$VERSION')
    sdk_int = Build.SDK_INT
    if sdk_int > 0:
        is_android = True
        print(f"DEBUG (EarthFiller): Android erkannt (SDK: {sdk_int}).")
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
            print("DEBUG (EarthFiller): Runnable Immersive gestartet.")
    else:
        print("INFO (EarthFiller): Nicht Android (SDK <= 0).")
        is_android = False
except ImportError:
    print("INFO (EarthFiller): Pyjnius nicht gefunden. Nehme an, es ist nicht Android.")
    is_android = False
except Exception as e:
    print(f"FEHLER oder Info (EarthFiller): Immersive Mode fehlgeschlagen oder nicht Android: {e}")
    is_android = False
# --- Ende Android ---


# --- Farben ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
GREEN = (0, 255, 0)
LIGHT_GREEN = (144, 238, 144)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
SKY_BLUE = (135, 206, 235) # Fallback Hintergrund

# --- Dateinamen für Assets ---
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
sound_effect_1_filename = "pop.wav"
BACKGROUND_IMAGE_FILENAME = "grow_plant_background1.png" # Passe dies ggf. an!
DISPENSER_BOTTOM_PNG = "dispenser_bottom.png" # Beispielname: 200x175
DISPENSER_TOP_PNG = "dispenser_top.png"       # Beispielname: 200x25

# --- Spielkonstanten ---
SWIPE_TARGET_PERCENT = 0.80
PARTICLE_SPEED = 150
PARTICLE_SIZE = 5
TILT_SPEED = 120    # Grad pro Sekunde Drehgeschwindigkeit
PARTICLE_FILL_PERCENT = 0.02 # 2% Füllung pro Partikel
SPAWN_ANGLE_THRESHOLD = 95 # Winkel (absolut), ab dem Partikel fallen
SPAWN_RATE_WHEN_TIPPED = 20 # Partikel pro Sekunde, wenn über Threshold gekippt
DISPENSER_TOP_PADDING = 80 # Abstand vom Dispenser zum Zurück-Button (oder oberem Rand)
LID_FALL_SPEED = 250 # Pixel pro Sekunde
LID_FADE_DURATION = 1.5 # Sekunden bis zur vollen Transparenz

# --- Skalierungs-Referenzen ---
REFERENCE_SCREEN_HEIGHT = 1080.0
DISPENSER_REF_WIDTH = 200.0
DISPENSER_REF_BOTTOM_H = 175.0
DISPENSER_REF_TOP_H = 25.0
DISPENSER_REF_TOTAL_HEIGHT = DISPENSER_REF_BOTTOM_H + DISPENSER_REF_TOP_H # = 200.0
SWIPE_BAR_REF_HEIGHT = 25.0


# --- Klasse für Erdpartikel ---
class EarthParticle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(int(self.x), int(self.y), PARTICLE_SIZE, PARTICLE_SIZE)

    def update(self, dt, screen_height):
        self.y += PARTICLE_SPEED * dt
        self.rect.top = int(self.y)
        return self.y < screen_height # True wenn noch im Bild

    def draw(self, screen):
        pygame.draw.rect(screen, BROWN, self.rect)


# --- Klasse für den unteren Behälter ---
class BottomContainer:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width * 0.6
        self.height = screen_height * 0.3
        self.x = (screen_width - self.width) / 2
        self.y = screen_height * 0.65 # Untere Hälfte
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.border_thickness = 5
        self.fill_level = 0.0 # 0.0 bis 1.0

    def add_fill(self, amount=1):
        self.fill_level = min(1.0, self.fill_level + PARTICLE_FILL_PERCENT * amount)

    def draw(self, screen):
        pygame.draw.rect(screen, DARK_BROWN, self.rect, self.border_thickness)
        if self.fill_level > 0:
            inner_height = self.height - 2 * self.border_thickness
            fill_height_visual = max(0, inner_height * self.fill_level)
            inner_width = self.width - 2 * self.border_thickness
            fill_rect = pygame.Rect(
                self.x + self.border_thickness,
                self.y + self.border_thickness + (inner_height - fill_height_visual),
                inner_width,
                fill_height_visual
            )
            if fill_rect.width > 0 and fill_rect.height > 0:
                 pygame.draw.rect(screen, BROWN, fill_rect)


# --- Klasse für den Erd-Spender (jetzt aus 2 PNGs) ---
class EarthDispenser:
    def __init__(self, screen_width, screen_height, bottom_img, top_img):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.original_bottom_image = bottom_img
        self.original_top_image = top_img

        scale_factor = screen_height / REFERENCE_SCREEN_HEIGHT
        self.scaled_bottom_w = max(40, int(DISPENSER_REF_WIDTH * scale_factor))
        self.scaled_bottom_h = max(34, int(DISPENSER_REF_BOTTOM_H * scale_factor))
        self.scaled_top_w = self.scaled_bottom_w
        self.scaled_top_h = max(6, int(DISPENSER_REF_TOP_H * scale_factor))
        self.total_height = self.scaled_bottom_h + self.scaled_top_h
        print(f"DEBUG: Dispenser Scaled Size: Bottom {self.scaled_bottom_w}x{self.scaled_bottom_h}, Top {self.scaled_top_w}x{self.scaled_top_h}")

        self.scaled_bottom_image = None
        self.scaled_top_image = None
        fallback_bottom_surf = None
        fallback_top_surf = None

        try:
            if self.original_bottom_image:
                self.scaled_bottom_image = pygame.transform.smoothscale(self.original_bottom_image, (self.scaled_bottom_w, self.scaled_bottom_h))
            else: raise ValueError("Bottom image is None")
        except Exception as e:
            print(f"WARNUNG: Konnte Dispenser-Unterteil nicht skalieren: {e}. Erstelle Fallback-Rechteck.")
            fallback_bottom_surf = pygame.Surface((self.scaled_bottom_w, self.scaled_bottom_h))
            fallback_bottom_surf.fill(DARK_BROWN)
            pygame.draw.rect(fallback_bottom_surf, BLACK, fallback_bottom_surf.get_rect(), 2)
            self.scaled_bottom_image = fallback_bottom_surf

        try:
            if self.original_top_image:
                self.scaled_top_image = pygame.transform.smoothscale(self.original_top_image, (self.scaled_top_w, self.scaled_top_h))
            else: raise ValueError("Top image is None")
        except Exception as e:
            print(f"WARNUNG: Konnte Dispenser-Oberteil nicht skalieren: {e}. Erstelle Fallback-Rechteck.")
            fallback_top_surf = pygame.Surface((self.scaled_top_w, self.scaled_top_h))
            fallback_top_surf.fill(DARK_GRAY)
            pygame.draw.rect(fallback_top_surf, BLACK, fallback_top_surf.get_rect(), 2)
            self.scaled_top_image = fallback_top_surf

        self.x = screen_width / 2
        self.y = self.total_height / 2

        self.angle = 0.0
        self.target_angle = 0.0

        self.state = "locked"
        self.swipe_progress = 0.0
        self.is_dragging = False
        self.drag_offset_x = 0

        self.base_surf = self.scaled_bottom_image
        self.rotated_surf = self.base_surf
        self.rotated_rect = self.rotated_surf.get_rect(center=(int(self.x), int(self.y)))

        self.lid_state = "attached"
        self.lid_rect = self.scaled_top_image.get_rect()
        self.lid_y = 0.0
        self.lid_original_x = 0.0
        self.lid_alpha = 255.0
        self.lid_fall_start_time = 0.0

        self.swipe_bar_height = max(10, int(SWIPE_BAR_REF_HEIGHT * scale_factor))
        self.swipe_bar_width = self.scaled_top_w * 0.8
        self.swipe_bar_rect = pygame.Rect(0, 0, self.swipe_bar_width, self.swipe_bar_height)
        self.update_swipe_bar_pos()

        self.particle_spawn_timer = 0.0
        self._last_angle = self.angle

    def set_initial_position(self, top_y_limit, padding):
        desired_top_of_lid = top_y_limit + padding
        self.y = desired_top_of_lid + self.total_height / 2

        bottom_center_y = self.y + self.scaled_top_h / 2
        self.rotated_rect.center = (int(self.x), int(bottom_center_y))

        self.lid_rect.centerx = int(self.x)
        self.lid_rect.bottom = self.rotated_rect.top
        self.lid_y = float(self.lid_rect.y)

        self.update_swipe_bar_pos()
        print(f"DEBUG: Dispenser initial Y (center) set to {self.y}, Bottom Top at {self.rotated_rect.top}, Lid Top at {self.lid_rect.top}")

    # create_base_surface nicht mehr benötigt

    def update_swipe_bar_pos(self):
         if hasattr(self, 'lid_rect') and self.lid_state == "attached":
             self.swipe_bar_rect.centerx = self.lid_rect.centerx
             self.swipe_bar_rect.bottom = self.lid_rect.top - 5
         elif hasattr(self, 'rotated_rect'):
              self.swipe_bar_rect.centerx = self.rotated_rect.centerx
              self.swipe_bar_rect.bottom = self.rotated_rect.top - 5

    def handle_event(self, event):
        if self.state == "locked":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.swipe_bar_rect.collidepoint(event.pos):
                    self.state = "swiping"
                    self.swipe_start_x = event.pos[0]
                    self.swipe_current_x = event.pos[0]
        elif self.state == "swiping":
            if event.type == pygame.MOUSEMOTION:
                 if pygame.mouse.get_pressed()[0]:
                    self.swipe_current_x = event.pos[0]
                    swipe_distance = self.swipe_current_x - self.swipe_start_x
                    self.swipe_progress = max(0.0, min(1.0, swipe_distance / (self.swipe_bar_rect.width * SWIPE_TARGET_PERCENT)))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.swipe_progress >= 1.0:
                    if self.lid_state == "attached":
                        self.lid_state = "falling"
                        self.lid_fall_start_time = time.time()
                        self.lid_original_x = self.lid_rect.centerx
                        print("DEBUG: Lid falling!")
                    self.state = "open"
                else:
                    self.state = "locked"
                    self.swipe_progress = 0.0
        elif self.state == "open":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                 if self.rotated_rect.collidepoint(event.pos):
                     self.is_dragging = True
                     self.drag_offset_x = self.x - event.pos[0]
            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging and pygame.mouse.get_pressed()[0]:
                    self.x = event.pos[0] + self.drag_offset_x
                    half_rotated_width = self.rotated_rect.width / 2
                    self.x = max(half_rotated_width, min(self.screen_width - half_rotated_width, self.x))
                    self.rotated_rect.centerx = int(self.x)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_dragging:
                    self.is_dragging = False

    def update(self, dt):
        angle_diff = self.target_angle - self.angle
        if abs(angle_diff) > 0.5:
            change = TILT_SPEED * dt
            change_sign = 1 if angle_diff > 0 else -1
            change *= change_sign
            if abs(change) >= abs(angle_diff): self.angle = self.target_angle
            else: self.angle += change

        if abs(self.angle - self._last_angle) > 0.1:
            old_center = self.rotated_rect.center
            self.rotated_surf = pygame.transform.rotate(self.base_surf, self.angle)
            self.rotated_rect = self.rotated_surf.get_rect(center=old_center)
            self.x, self.y = old_center
            self._last_angle = self.angle

        if self.lid_state == "falling":
            elapsed_time = time.time() - self.lid_fall_start_time
            self.lid_y += LID_FALL_SPEED * dt
            if elapsed_time < LID_FADE_DURATION:
                self.lid_alpha = max(0.0, 255.0 * (1.0 - (elapsed_time / LID_FADE_DURATION)))
            else:
                self.lid_alpha = 0.0
                self.lid_state = "faded"
                print("DEBUG: Lid faded.")

        particles_to_spawn = []
        current_abs_angle = abs(self.angle)
        normalized_angle_abs = current_abs_angle % 360
        is_tipped_over = normalized_angle_abs > SPAWN_ANGLE_THRESHOLD and normalized_angle_abs < (360 - SPAWN_ANGLE_THRESHOLD)

        if self.state == "open" and self.lid_state != "attached" and is_tipped_over:
            self.particle_spawn_timer += dt * SPAWN_RATE_WHEN_TIPPED
            while self.particle_spawn_timer >= 1.0:
                self.particle_spawn_timer -= 1.0
                bottom_center_rel_x = 0
                bottom_center_rel_y = self.scaled_bottom_h / 2.0
                rad_angle = math.radians(-self.angle)
                cos_a = math.cos(rad_angle); sin_a = math.sin(rad_angle)
                spawn_rel_x = bottom_center_rel_x * cos_a - bottom_center_rel_y * sin_a
                spawn_rel_y = bottom_center_rel_x * sin_a + bottom_center_rel_y * cos_a
                spawn_x = self.rotated_rect.centerx + spawn_rel_x
                spawn_y = self.rotated_rect.centery + spawn_rel_y
                px = spawn_x + random.uniform(-self.scaled_bottom_w / 4, self.scaled_bottom_w / 4)
                py = spawn_y + random.uniform(-5, 5)
                particles_to_spawn.append(EarthParticle(px, py))
                if len(particles_to_spawn) > 10: break

        if not is_tipped_over: self.particle_spawn_timer = 0.0
        return particles_to_spawn

    def draw(self, screen):
        if hasattr(self, 'rotated_surf') and hasattr(self, 'rotated_rect'):
            screen.blit(self.rotated_surf, self.rotated_rect.topleft)
        else:
            print("WARNUNG: Rotiertes Surface/Rect (Boden) nicht vorhanden zum Zeichnen!")

        if self.lid_state == "attached":
            if self.scaled_top_image:
                lid_draw_rect = self.scaled_top_image.get_rect()
                lid_draw_rect.centerx = self.rotated_rect.centerx
                lid_draw_rect.bottom = self.rotated_rect.top
                screen.blit(self.scaled_top_image, lid_draw_rect.topleft)
        elif self.lid_state == "falling":
            if self.scaled_top_image and self.lid_alpha > 0:
                temp_lid_surf = self.scaled_top_image.copy()
                temp_lid_surf.set_alpha(int(self.lid_alpha))
                lid_draw_rect = temp_lid_surf.get_rect(centerx=int(self.lid_original_x), y=int(self.lid_y))
                screen.blit(temp_lid_surf, lid_draw_rect.topleft)

        if self.state == "locked" or self.state == "swiping":
             pygame.draw.rect(screen, GRAY, self.swipe_bar_rect)
             progress_width = self.swipe_bar_rect.width * self.swipe_progress
             progress_rect = pygame.Rect(self.swipe_bar_rect.left, self.swipe_bar_rect.top, progress_width, self.swipe_bar_rect.height)
             pygame.draw.rect(screen, LIGHT_GREEN, progress_rect)
             target_x = self.swipe_bar_rect.left + self.swipe_bar_rect.width * SWIPE_TARGET_PERCENT
             pygame.draw.line(screen, GREEN, (target_x, self.swipe_bar_rect.top), (target_x, self.swipe_bar_rect.bottom), 2)
             pygame.draw.rect(screen, BLACK, self.swipe_bar_rect, 1)


# --- Hauptfunktion des Minispiels ---
def run_minigame_earth_filler(screen_surface):
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    print(f"DEBUG (EarthFiller): Nutze Screen-Größe: {actual_screen_size}")

    game_state = "running"

    # --- Mixer Initialisierung ---
    sound_effect_1 = None
    mixer_ok = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            mixer_ok = True
            print("DEBUG (EarthFiller): Mixer initialisiert.")
        except pygame.error as e:
            print(f"WARNUNG (EarthFiller): Mixer fehlgeschlagen: {e}")
    else:
        mixer_ok = True
        print("DEBUG (EarthFiller): Mixer war bereits initialisiert.")

    # --- PFAD-SETUP ---
    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    project_root_folder = os.path.abspath(os.path.join(script_dir_game, "..", "..","..")) # ANPASSEN!
    data_subfolder = "data"
    image_folder_rel = os.path.join(data_subfolder, "bilder")
    sound_folder_rel = os.path.join(data_subfolder, "sounds")
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, image_folder_rel))
    sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, sound_folder_rel))
    print(f"DEBUG (EarthFiller): Script Dir: {script_dir_game}")
    print(f"DEBUG (EarthFiller): Project Root (vermutet): {project_root_folder}")
    print(f"DEBUG (EarthFiller): Image folder (abs): {image_folder_abs}")
    print(f"DEBUG (EarthFiller): Sound folder (abs): {sound_folder_abs}")

    # --- Sound laden ---
    sound_path_1 = os.path.join(sound_folder_abs, sound_effect_1_filename)
    if mixer_ok:
        try:
            sound_effect_1 = pygame.mixer.Sound(sound_path_1)
            sound_effect_1.set_volume(0.5)
            print(f"DEBUG (EarthFiller): Sound 1 '{sound_effect_1_filename}' geladen.")
        except Exception as e:
            print(f"WARNUNG (EarthFiller): Sound 1 '{sound_path_1}' laden fehlgeschlagen: {e}")
            sound_effect_1 = None

    # --- Schriftarten laden --- ## KORRIGIERTE EINRÜCKUNG ##
    info_font = None
    button_font = None
    try:
        scale_factor_font = screen_height / REFERENCE_SCREEN_HEIGHT
        BASE_INFO_FONT_SIZE_REF = 24
        info_font_size = max(12, int(BASE_INFO_FONT_SIZE_REF * scale_factor_font))
        try: # Innerer Try für SysFont
            info_font = pygame.font.SysFont("arial", info_font_size)
        except Exception: # Innerer Except (korrekt eingerückt)
            info_font = pygame.font.Font(None, info_font_size)
    except Exception as e: # Äußerer Except für Info Font
        print(f"WARNUNG: Info-Schriftart konnte nicht geladen/skaliert werden: {e}")
    if not info_font: # Fallback
        info_font = pygame.font.Font(None, 24)

    try:
        scale_factor_font = screen_height / REFERENCE_SCREEN_HEIGHT
        BASE_BUTTON_FONT_SIZE_REF = 20
        button_font_size = max(12, int(BASE_BUTTON_FONT_SIZE_REF * scale_factor_font))
        try: # Innerer Try für SysFont
            button_font = pygame.font.SysFont("arial", button_font_size)
        except Exception: # Innerer Except (korrekt eingerückt)
            button_font = pygame.font.Font(None, button_font_size)
    except Exception as e: # Äußerer Except für Button Font
        print(f"WARNUNG: Button-Schriftart konnte nicht geladen/skaliert werden: {e}")
    if not button_font: # Fallback
        button_font = pygame.font.Font(None, 20)
    # --- Ende Font Laden ---


    # --- Assets Laden (Back Button, Hintergrund, Dispenser-Teile) ---
    scaled_back_button_bg = None
    scaled_back_button_hover = None
    use_back_button_images = False
    back_button_rect = None
    try:
        scale_factor_ui = screen_height / REFERENCE_SCREEN_HEIGHT
        BACK_BUTTON_REF_WIDTH = 160.0
        BACK_BUTTON_REF_HEIGHT = 40.0
        back_button_width = max(50, int(BACK_BUTTON_REF_WIDTH * scale_factor_ui))
        back_button_height = max(20, int(BACK_BUTTON_REF_HEIGHT * scale_factor_ui))
        back_button_y = 10
        back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, back_button_y, back_button_width, back_button_height)
        back_bg_path = os.path.join(image_folder_abs, back_button_bg_filename)
        back_hover_path = os.path.join(image_folder_abs, back_button_hover_filename)
        img_bg = pygame.image.load(back_bg_path).convert_alpha()
        img_hover = pygame.image.load(back_hover_path).convert_alpha()
        scaled_back_button_bg = pygame.transform.smoothscale(img_bg, back_button_rect.size)
        scaled_back_button_hover = pygame.transform.smoothscale(img_hover, back_button_rect.size)
        use_back_button_images = True
        print(f"DEBUG (EarthFiller): Zurück-Buttons geladen und skaliert.")
    except Exception as e:
        print(f"WARNUNG (EarthFiller): Zurück-Buttons laden/skalieren fehlgeschlagen: {e}")
        if 'back_button_width' in locals():
             back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, back_button_y, back_button_width, back_button_height)
        else:
             back_button_rect = pygame.Rect(screen_width * 0.4, 10, screen_width * 0.2, screen_height * 0.08)

    scaled_background_image = None
    use_background_image = False
    try:
        background_path = os.path.join(image_folder_abs, BACKGROUND_IMAGE_FILENAME)
        loaded_bg = pygame.image.load(background_path).convert()
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG (EarthFiller): Hintergrundbild '{BACKGROUND_IMAGE_FILENAME}' geladen.")
    except Exception as e:
        print(f"WARNUNG (EarthFiller): Hintergrundbild '{background_path}' laden fehlgeschlagen: {e}.")

    original_dispenser_bottom = None
    original_dispenser_top = None
    try:
        bottom_path = os.path.join(image_folder_abs, DISPENSER_BOTTOM_PNG)
        original_dispenser_bottom = pygame.image.load(bottom_path).convert_alpha()
        print(f"DEBUG: Dispenser Bottom '{DISPENSER_BOTTOM_PNG}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Dispenser Bottom '{bottom_path}' laden fehlgeschlagen: {e}")
    try:
        top_path = os.path.join(image_folder_abs, DISPENSER_TOP_PNG)
        original_dispenser_top = pygame.image.load(top_path).convert_alpha()
        print(f"DEBUG: Dispenser Top '{DISPENSER_TOP_PNG}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Dispenser Top '{top_path}' laden fehlgeschlagen: {e}")
    # --- Ende Asset Loading ---

    # --- Spielobjekte Initialisieren ---
    dispenser = EarthDispenser(screen_width, screen_height, original_dispenser_bottom, original_dispenser_top)
    bottom_container = BottomContainer(screen_width, screen_height)
    earth_particles = []

    if back_button_rect:
        dispenser.set_initial_position(back_button_rect.bottom, DISPENSER_TOP_PADDING)
    else:
        dispenser.set_initial_position(10, DISPENSER_TOP_PADDING)

    # Android Buttons
    scale_factor_ui = screen_height / REFERENCE_SCREEN_HEIGHT
    TILT_BUTTON_REF_SIZE = 80.0
    tilt_button_size = max(40, int(TILT_BUTTON_REF_SIZE * scale_factor_ui))
    tilt_button_y = screen_height - tilt_button_size - 10
    left_tilt_button_rect = pygame.Rect(10, tilt_button_y, tilt_button_size, tilt_button_size)
    right_tilt_button_rect = pygame.Rect(screen_width - tilt_button_size - 10, tilt_button_y, tilt_button_size, tilt_button_size)
    left_tilt_pressed = False
    right_tilt_pressed = False

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1)
        if dt <= 0: dt = 1/60.0
        last_time = current_time
        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False; game_state = "quit"; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False; game_state = "escape"; continue
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False; game_state = "back_button"; continue
                    if is_android and dispenser.state == "open":
                        if left_tilt_button_rect.collidepoint(event.pos):
                            left_tilt_pressed = True
                        elif right_tilt_button_rect.collidepoint(event.pos):
                            right_tilt_pressed = True
            if event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1:
                     if is_android and dispenser.state == "open":
                         if not pygame.mouse.get_pressed()[0]:
                             left_tilt_pressed = False
                             right_tilt_pressed = False
            dispenser.handle_event(event)

        # --- Spiel-Logik Update ---
        if game_state == "running":
            if not is_android and dispenser.state == "open":
                keys = pygame.key.get_pressed()
                if keys[pygame.K_q]: dispenser.target_angle += TILT_SPEED * dt
                elif keys[pygame.K_e]: dispenser.target_angle -= TILT_SPEED * dt
            if is_android and dispenser.state == "open":
                if left_tilt_pressed: dispenser.target_angle += TILT_SPEED * dt
                elif right_tilt_pressed: dispenser.target_angle -= TILT_SPEED * dt

            new_particles = dispenser.update(dt)
            if new_particles: earth_particles.extend(new_particles)
            remaining_particles = []
            particles_landed_this_frame = 0
            for particle in earth_particles:
                if particle.update(dt, screen_height):
                    if bottom_container.rect.colliderect(particle.rect):
                        particles_landed_this_frame += 1
                    else:
                        remaining_particles.append(particle)
            earth_particles = remaining_particles
            if particles_landed_this_frame > 0:
                bottom_container.add_fill(particles_landed_this_frame)
                if sound_effect_1 and random.random() < 0.2:
                     sound_effect_1.play()
            if bottom_container.fill_level >= 1.0:
                game_state = "finished"
                print("INFO: Unterer Behälter ist voll!")

        # --- ZEICHNEN ---
        screen.fill(SKY_BLUE)
        bottom_container.draw(screen)
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        dispenser.draw(screen)
        for particle in earth_particles:
            particle.draw(screen)

        # UI Elemente
        if is_android and dispenser.state == "open":
             pygame.draw.rect(screen, RED if left_tilt_pressed else DARK_GRAY, left_tilt_button_rect)
             arrow_points_left = [(left_tilt_button_rect.centerx - tilt_button_size * 0.2, left_tilt_button_rect.centery), (left_tilt_button_rect.centerx + tilt_button_size * 0.2, left_tilt_button_rect.top + tilt_button_size * 0.2), (left_tilt_button_rect.centerx + tilt_button_size * 0.2, left_tilt_button_rect.bottom - tilt_button_size * 0.2),]
             pygame.draw.polygon(screen, WHITE, arrow_points_left)
             pygame.draw.rect(screen, BLACK, left_tilt_button_rect, 2)
             pygame.draw.rect(screen, RED if right_tilt_pressed else DARK_GRAY, right_tilt_button_rect)
             arrow_points_right = [(right_tilt_button_rect.centerx + tilt_button_size * 0.2, right_tilt_button_rect.centery), (right_tilt_button_rect.centerx - tilt_button_size * 0.2, right_tilt_button_rect.top + tilt_button_size * 0.2), (right_tilt_button_rect.centerx - tilt_button_size * 0.2, right_tilt_button_rect.bottom - tilt_button_size * 0.2),]
             pygame.draw.polygon(screen, WHITE, arrow_points_right)
             pygame.draw.rect(screen, BLACK, right_tilt_button_rect, 2)
        if info_font:
            fill_percent = int(bottom_container.fill_level * 100)
            text_y_start = (back_button_rect.bottom + 10) if back_button_rect else 10
            try:
                fill_text_surface = info_font.render(f"Füllstand: {fill_percent}%", True, BLACK)
                screen.blit(fill_text_surface, (10, text_y_start))
            except Exception as e:
                print(f"FEHLER beim Rendern des Info-Textes: {e}")
        if game_state == "finished" and info_font:
             try:
                finished_text_surface = info_font.render("Fertig!", True, GREEN, DARK_GRAY)
                finished_rect = finished_text_surface.get_rect(center=(screen_width / 2, screen_height / 2))
                screen.blit(finished_text_surface, finished_rect)
             except Exception as e:
                 print(f"FEHLER beim Rendern des 'Fertig'-Textes: {e}")
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
    print(f"INFO (EarthFiller): Minispiel-Schleife beendet. Endzustand: {game_state}")
    return game_state == "finished"

# --- Standalone Code (Zum Testen des Templates) ---
if __name__ == "__main__":
    print("INFO: pygame_minigame_earth_filler_v6_fixed_indent2.py wird eigenständig ausgeführt.")
    pygame.init()
    try: pygame.font.init()
    except Exception as e: print(f"FEHLER bei pygame.font.init(): {e}")
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.RESIZABLE)
    pygame.display.set_caption("Pygame Earth Filler v6 Fixed Indent (Standalone Test)")

    print(f"\n--- Starte Earth Filler v6 Standalone ---\n")
    try:
        ziel_erreicht = run_minigame_earth_filler(standalone_screen)
        print(f"\n--- Standalone Beendet. Ergebnis: ---")
        print(f"  Ziel erreicht (Behälter voll): {ziel_erreicht}")
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