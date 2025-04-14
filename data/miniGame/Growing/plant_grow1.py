# plant_grow1.py (Angepasst für Rückgabewert/Exit Code & Neu formatiert)
# -*- coding: utf-8 -*-
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
    print("INFO (EarthFiller): Pyjnius nicht gefunden.")
    is_android = False
except Exception as e:
    print(f"FEHLER (EarthFiller): Immersive Mode: {e}")
    is_android = False
# --- Ende Android ---

# --- Farben ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150); BROWN = (139, 69, 19); DARK_BROWN = (101, 67, 33)
GREEN = (0, 255, 0); LIGHT_GREEN = (144, 238, 144); RED = (255, 0, 0)
BLUE = (0, 0, 255); SKY_BLUE = (135, 206, 235)

# --- Dateinamen für Assets ---
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
sound_effect_1_filename = "pop.wav"
BACKGROUND_IMAGE_FILENAME = "grow_plant_background1.png"
DISPENSER_BOTTOM_PNG = "dispenser_bottom.png"
DISPENSER_TOP_PNG = "dispenser_top.png"

# --- Spielkonstanten ---
SWIPE_TARGET_PERCENT = 0.80; PARTICLE_SPEED = 150; PARTICLE_SIZE = 5
TILT_SPEED = 120; PARTICLE_FILL_PERCENT = 0.02; SPAWN_ANGLE_THRESHOLD = 95
SPAWN_RATE_WHEN_TIPPED = 20; DISPENSER_TOP_PADDING = 80
LID_FALL_SPEED = 250; LID_FADE_DURATION = 1.5

# --- Skalierungs-Referenzen ---
REFERENCE_SCREEN_HEIGHT = 1080.0; DISPENSER_REF_WIDTH = 200.0
DISPENSER_REF_BOTTOM_H = 175.0; DISPENSER_REF_TOP_H = 25.0
DISPENSER_REF_TOTAL_HEIGHT = DISPENSER_REF_BOTTOM_H + DISPENSER_REF_TOP_H
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
        self.y = screen_height * 0.65
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

# --- Klasse für den Erd-Spender ---
class EarthDispenser:
    def __init__(self, screen_width, screen_height, bottom_img, top_img):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original_bottom_image = bottom_img
        self.original_top_image = top_img

        # Skalierung berechnen
        scale_factor = screen_height / REFERENCE_SCREEN_HEIGHT
        self.scaled_bottom_w = max(40, int(DISPENSER_REF_WIDTH * scale_factor))
        self.scaled_bottom_h = max(34, int(DISPENSER_REF_BOTTOM_H * scale_factor))
        self.scaled_top_w = self.scaled_bottom_w
        self.scaled_top_h = max(6, int(DISPENSER_REF_TOP_H * scale_factor))
        self.total_height = self.scaled_bottom_h + self.scaled_top_h
        print(f"DEBUG: Dispenser Scaled: Bot {self.scaled_bottom_w}x{self.scaled_bottom_h}, Top {self.scaled_top_w}x{self.scaled_top_h}")

        # Bilder skalieren oder Fallback erstellen
        self.scaled_bottom_image = None; self.scaled_top_image = None
        try:
            if self.original_bottom_image: self.scaled_bottom_image = pygame.transform.smoothscale(self.original_bottom_image, (self.scaled_bottom_w, self.scaled_bottom_h))
            else: raise ValueError("Bottom image None")
        except Exception as e:
            print(f"WARNUNG: Dispenser Unten Skalierung: {e}")
            fb_bot = pygame.Surface((self.scaled_bottom_w, self.scaled_bottom_h)); fb_bot.fill(DARK_BROWN); pygame.draw.rect(fb_bot, BLACK, fb_bot.get_rect(), 2); self.scaled_bottom_image = fb_bot
        try:
            if self.original_top_image: self.scaled_top_image = pygame.transform.smoothscale(self.original_top_image, (self.scaled_top_w, self.scaled_top_h))
            else: raise ValueError("Top image None")
        except Exception as e:
            print(f"WARNUNG: Dispenser Oben Skalierung: {e}")
            fb_top = pygame.Surface((self.scaled_top_w, self.scaled_top_h)); fb_top.fill(DARK_GRAY); pygame.draw.rect(fb_top, BLACK, fb_top.get_rect(), 2); self.scaled_top_image = fb_top

        # Position und Zustand
        self.x = screen_width / 2.0
        self.y = self.total_height / 2.0 # Startposition oben, wird später angepasst
        self.angle = 0.0
        self.target_angle = 0.0
        self.state = "locked" # locked, swiping, open
        self.swipe_progress = 0.0
        self.is_dragging = False
        self.drag_offset_x = 0

        # Surfaces und Rects
        self.base_surf = self.scaled_bottom_image
        self.rotated_surf = self.base_surf
        self.rotated_rect = self.rotated_surf.get_rect(center=(int(self.x), int(self.y)))
        self._last_angle = self.angle # Für Optimierung

        # Deckel Zustand
        self.lid_state = "attached" # attached, falling, faded
        self.lid_rect = self.scaled_top_image.get_rect()
        self.lid_y = 0.0
        self.lid_original_x = 0.0
        self.lid_alpha = 255.0
        self.lid_fall_start_time = 0.0

        # Swipe Bar
        self.swipe_bar_height = max(10, int(SWIPE_BAR_REF_HEIGHT * scale_factor))
        self.swipe_bar_width = self.scaled_top_w * 0.8
        self.swipe_bar_rect = pygame.Rect(0, 0, self.swipe_bar_width, self.swipe_bar_height)
        self.update_swipe_bar_pos()

        # Partikel-Timer
        self.particle_spawn_timer = 0.0

    def set_initial_position(self, top_y_limit, padding):
        """Setzt die vertikale Startposition des Dispensers."""
        desired_top_of_lid = top_y_limit + padding
        # Passe den Mittelpunkt self.y an
        self.y = desired_top_of_lid + self.total_height / 2.0
        # Passe die Rects an den neuen Mittelpunkt an
        bottom_center_y = self.y + self.scaled_top_h / 2.0 # Mitte des Bodenteils
        self.rotated_rect.center = (int(self.x), int(bottom_center_y))
        self.lid_rect.centerx = int(self.x)
        self.lid_rect.bottom = self.rotated_rect.top
        self.lid_y = float(self.lid_rect.y) # Y-Position für fallenden Deckel merken
        self.update_swipe_bar_pos() # Swipe Bar Position aktualisieren
        print(f"DEBUG: Dispenser Y={self.y}, Bottom Top={self.rotated_rect.top}, Lid Top={self.lid_rect.top}")

    def update_swipe_bar_pos(self):
        """Aktualisiert die Position der Swipe-Leiste basierend auf Deckel/Dispenser."""
        if hasattr(self, 'lid_rect') and self.lid_state == "attached":
             self.swipe_bar_rect.centerx = self.lid_rect.centerx
             self.swipe_bar_rect.bottom = self.lid_rect.top - 5
        elif hasattr(self, 'rotated_rect'): # Fallback, falls Deckel schon weg ist
             self.swipe_bar_rect.centerx = self.rotated_rect.centerx
             self.swipe_bar_rect.bottom = self.rotated_rect.top - 5

    def handle_event(self, event):
        """Verarbeitet Benutzer-Events für den Dispenser."""
        if self.state == "locked":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.swipe_bar_rect.collidepoint(event.pos):
                    self.state = "swiping"
                    self.swipe_start_x = event.pos[0]
                    self.swipe_current_x = event.pos[0]
        elif self.state == "swiping":
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]: # Linke Taste gedrückt?
                    self.swipe_current_x = event.pos[0]
                    swipe_distance = self.swipe_current_x - self.swipe_start_x
                    target_width = self.swipe_bar_rect.width * SWIPE_TARGET_PERCENT
                    if target_width > 0: # Division durch Null verhindern
                        self.swipe_progress = max(0.0, min(1.0, swipe_distance / target_width))
                    else:
                        self.swipe_progress = 1.0 if swipe_distance > 0 else 0.0
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.swipe_progress >= 1.0: # Erfolgreich geswiped?
                    if self.lid_state == "attached":
                        self.lid_state = "falling"
                        self.lid_fall_start_time = time.time()
                        self.lid_original_x = self.lid_rect.centerx
                        print("DEBUG: Lid falling!")
                    self.state = "open"
                else: # Swipe nicht weit genug
                    self.state = "locked"
                    self.swipe_progress = 0.0
        elif self.state == "open":
             if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                 # Prüfe Kollision mit rotiertem Rechteck des Bodens
                 if self.rotated_rect.collidepoint(event.pos):
                     self.is_dragging = True
                     # Offset berechnen, damit der Klickpunkt relativ zur Mitte bleibt
                     self.drag_offset_x = self.x - event.pos[0]
             elif event.type == pygame.MOUSEMOTION:
                 if self.is_dragging and pygame.mouse.get_pressed()[0]:
                     self.x = event.pos[0] + self.drag_offset_x
                     # Verhindern, dass Dispenser aus dem Bild gezogen wird
                     half_rotated_width = self.rotated_rect.width / 2.0
                     self.x = max(half_rotated_width, min(self.screen_width - half_rotated_width, self.x))
                     self.rotated_rect.centerx = int(self.x) # Nur X-Position aktualisieren
             elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                 if self.is_dragging:
                     self.is_dragging = False

    def update(self, dt):
        """Aktualisiert Winkel, Position und Partikel."""
        # Winkel anpassen
        angle_diff = self.target_angle - self.angle
        if abs(angle_diff) > 0.5: # Schwellwert für Bewegung
            change = TILT_SPEED * dt
            change_sign = 1 if angle_diff > 0 else -1
            change *= change_sign
            # Verhindern, dass über das Ziel hinaus rotiert wird
            if abs(change) >= abs(angle_diff):
                self.angle = self.target_angle
            else:
                self.angle += change

        # Nur rotieren, wenn Winkel sich geändert hat (Performance)
        if abs(self.angle - self._last_angle) > 0.1:
            old_center = self.rotated_rect.center
            self.rotated_surf = pygame.transform.rotate(self.base_surf, self.angle)
            self.rotated_rect = self.rotated_surf.get_rect(center=old_center)
            # Position (x, y) ist der *Pivot*-Punkt, nicht das Rect-Center
            self.x, self.y = old_center[0], old_center[1] - self.scaled_top_h / 2.0 # Korrektur für Pivot
            self._last_angle = self.angle

        # Deckel-Animation
        if self.lid_state == "falling":
            elapsed_time = time.time() - self.lid_fall_start_time
            self.lid_y += LID_FALL_SPEED * dt
            # Deckel ausblenden
            if elapsed_time < LID_FADE_DURATION:
                self.lid_alpha = max(0.0, 255.0 * (1.0 - (elapsed_time / LID_FADE_DURATION)))
            else:
                self.lid_alpha = 0.0
                self.lid_state = "faded"
                print("DEBUG: Lid faded.")

        # Partikel erzeugen, wenn gekippt
        particles_to_spawn = []
        current_abs_angle = abs(self.angle)
        # Winkel normalisieren für einfache Prüfung (z.B. 400 Grad -> 40 Grad)
        normalized_angle_abs = current_abs_angle % 360
        # Prüfen, ob Winkel im "gekippt"-Bereich liegt
        is_tipped_over = (normalized_angle_abs > SPAWN_ANGLE_THRESHOLD and
                          normalized_angle_abs < (360 - SPAWN_ANGLE_THRESHOLD))

        if self.state == "open" and self.lid_state != "attached" and is_tipped_over:
            self.particle_spawn_timer += dt * SPAWN_RATE_WHEN_TIPPED
            # Erzeuge Partikel basierend auf Timer und Rate
            while self.particle_spawn_timer >= 1.0:
                self.particle_spawn_timer -= 1.0
                # Berechne Spawn-Position am unteren Rand des rotierten Dispensers
                # (Komplexe Vektordrehung für genaue Position)
                bottom_center_rel_x = 0
                bottom_center_rel_y = self.scaled_bottom_h / 2.0 # Relativ zum Pivot
                rad_angle = math.radians(-self.angle) # Negativ, da Pygame im Uhrzeigersinn dreht
                cos_a = math.cos(rad_angle); sin_a = math.sin(rad_angle)
                # Rotierte relative Position
                spawn_rel_x = bottom_center_rel_x * cos_a - bottom_center_rel_y * sin_a
                spawn_rel_y = bottom_center_rel_x * sin_a + bottom_center_rel_y * cos_a
                # Absolute Position
                spawn_x = self.rotated_rect.centerx + spawn_rel_x
                spawn_y = self.rotated_rect.centery + spawn_rel_y
                # Kleine zufällige Abweichung
                px = spawn_x + random.uniform(-self.scaled_bottom_w / 4, self.scaled_bottom_w / 4)
                py = spawn_y + random.uniform(-5, 5)
                particles_to_spawn.append(EarthParticle(px, py))
                # Limit pro Frame, um Leistungsprobleme zu vermeiden
                if len(particles_to_spawn) > 10: break # Mehrere Partikel pro Frame möglich

        # Timer zurücksetzen, wenn nicht mehr gekippt
        if not is_tipped_over:
            self.particle_spawn_timer = 0.0

        return particles_to_spawn

    def draw(self, screen):
        """Zeichnet den Dispenser (Boden und Deckel) und die Swipe-Bar."""
        # Boden zeichnen
        if hasattr(self, 'rotated_surf') and hasattr(self, 'rotated_rect'):
            screen.blit(self.rotated_surf, self.rotated_rect.topleft)
        else: print("WARNUNG: Rotiertes Surface/Rect (Boden) fehlt!")

        # Deckel zeichnen (wenn sichtbar)
        if self.lid_state == "attached":
            if self.scaled_top_image:
                # Positioniere Deckel relativ zum rotierten Boden
                lid_draw_rect = self.scaled_top_image.get_rect()
                lid_draw_rect.centerx = self.rotated_rect.centerx
                lid_draw_rect.bottom = self.rotated_rect.top
                screen.blit(self.scaled_top_image, lid_draw_rect.topleft)
        elif self.lid_state == "falling":
            if self.scaled_top_image and self.lid_alpha > 0:
                # Kopie erstellen für Alpha-Änderung
                temp_lid_surf = self.scaled_top_image.copy()
                temp_lid_surf.set_alpha(int(self.lid_alpha))
                # Position basierend auf Fallbewegung
                lid_draw_rect = temp_lid_surf.get_rect(centerx=int(self.lid_original_x), y=int(self.lid_y))
                screen.blit(temp_lid_surf, lid_draw_rect.topleft)

        # Swipe Bar zeichnen (wenn nötig)
        if self.state == "locked" or self.state == "swiping":
             pygame.draw.rect(screen, GRAY, self.swipe_bar_rect) # Hintergrund
             # Fortschrittsbalken
             progress_width = self.swipe_bar_rect.width * self.swipe_progress
             progress_rect = pygame.Rect(self.swipe_bar_rect.left, self.swipe_bar_rect.top,
                                         progress_width, self.swipe_bar_rect.height)
             pygame.draw.rect(screen, LIGHT_GREEN, progress_rect)
             # Ziellinie
             target_x = self.swipe_bar_rect.left + self.swipe_bar_rect.width * SWIPE_TARGET_PERCENT
             pygame.draw.line(screen, GREEN, (target_x, self.swipe_bar_rect.top),
                              (target_x, self.swipe_bar_rect.bottom), 2)
             # Rand der Swipe-Bar
             pygame.draw.rect(screen, BLACK, self.swipe_bar_rect, 1)

# --- Hauptfunktion des Minispiels ---
def run_minigame_earth_filler(screen_surface):
    """Führt das Minispiel aus und gibt True bei Erfolg, False bei Abbruch zurück."""
    screen = screen_surface
    screen_width, screen_height = screen.get_size()
    print(f"DEBUG (EarthFiller): Nutze Screen-Größe: {screen.get_size()}")
    game_result = False # Standard: Nicht erfolgreich

    # --- Mixer, Pfade, Fonts, Assets laden ---
    sound_effect_1 = None; mixer_ok = False
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(buffer=1024); mixer_ok=True; print("DEBUG: Mixer init.")
        except pygame.error as e: print(f"WARNUNG: Mixer fehlgeschlagen: {e}")
    else: mixer_ok = True; print("DEBUG: Mixer war init.")

    # Pfade bestimmen (relative Pfade können fehleranfällig sein)
    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    # Gehe 3 Ebenen hoch von data/miniGame/Growing -> Root
    project_root = os.path.abspath(os.path.join(script_dir_game, "..", "..", ".."))
    img_folder = os.path.normpath(os.path.join(project_root, "data", "bilder"))
    snd_folder = os.path.normpath(os.path.join(project_root, "data", "sounds"))
    print(f"DEBUG: Image folder: {img_folder}, Sound folder: {snd_folder}")

    sound_path_1 = os.path.join(snd_folder, sound_effect_1_filename)
    if mixer_ok:
        try: sound_effect_1 = pygame.mixer.Sound(sound_path_1); sound_effect_1.set_volume(0.5); print("DEBUG: Sound 1 geladen.")
        except Exception as e: print(f"WARNUNG: Sound 1 laden: {e}"); sound_effect_1 = None

    info_font = None; button_font = None
    try: # Fonts laden/skalieren
        sf=screen_height/REFERENCE_SCREEN_HEIGHT; ifs=max(12,int(24*sf)); bfs=max(12,int(20*sf))
        try: info_font=pygame.font.SysFont("arial",ifs)
        except: info_font=pygame.font.Font(None,ifs)
        try: button_font=pygame.font.SysFont("arial",bfs)
        except: button_font=pygame.font.Font(None,bfs)
    except Exception as e: print(f"WARNUNG: Font laden/skalieren: {e}"); info_font=pygame.font.Font(None,24); button_font=pygame.font.Font(None,20)
    if not info_font: info_font=pygame.font.Font(None,24)
    if not button_font: button_font=pygame.font.Font(None,20)

    # Assets laden
    scaled_back_bg=None; scaled_back_hover=None; use_back_img=False; back_rect=None
    try: sf_ui=screen_height/REFERENCE_SCREEN_HEIGHT; bw=max(50,int(160*sf_ui)); bh=max(20,int(40*sf_ui)); by=10; back_rect=pygame.Rect((screen_width-bw)//2,by,bw,bh); bg_p=os.path.join(img_folder,back_button_bg_filename); hov_p=os.path.join(img_folder,back_button_hover_filename); img_bg=pygame.image.load(bg_p).convert_alpha(); img_hov=pygame.image.load(hov_p).convert_alpha(); scaled_back_bg=pygame.transform.smoothscale(img_bg,back_rect.size); scaled_back_hover=pygame.transform.smoothscale(img_hov,back_rect.size); use_back_img=True; print("DEBUG: Back Buttons geladen.")
    except Exception as e: print(f"WARNUNG: Back Buttons: {e}"); back_rect=pygame.Rect(screen_width*.4,10,screen_width*.2,screen_height*.08) if not back_rect else back_rect

    scaled_bg_img=None; use_bg_img=False
    try: bg_path=os.path.join(img_folder,BACKGROUND_IMAGE_FILENAME); loaded=pygame.image.load(bg_path).convert(); scaled_bg_img=pygame.transform.smoothscale(loaded,screen.get_size()); use_bg_img=True; print("DEBUG: BG geladen.")
    except Exception as e: print(f"WARNUNG: BG laden: {e}.")

    orig_disp_bot=None; orig_disp_top=None
    try: bot_p=os.path.join(img_folder,DISPENSER_BOTTOM_PNG); orig_disp_bot=pygame.image.load(bot_p).convert_alpha(); print("DEBUG: Disp Bottom geladen.")
    except Exception as e: print(f"WARNUNG: Disp Bottom: {e}")
    try: top_p=os.path.join(img_folder,DISPENSER_TOP_PNG); orig_disp_top=pygame.image.load(top_p).convert_alpha(); print("DEBUG: Disp Top geladen.")
    except Exception as e: print(f"WARNUNG: Disp Top: {e}")

    # --- Spielobjekte Initialisieren ---
    dispenser = EarthDispenser(screen_width, screen_height, orig_disp_bot, orig_disp_top)
    bottom_container = BottomContainer(screen_width, screen_height)
    earth_particles = []
    if back_rect: dispenser.set_initial_position(back_rect.bottom, DISPENSER_TOP_PADDING)
    else: dispenser.set_initial_position(10, DISPENSER_TOP_PADDING)
    sf_ui=screen_height/REFERENCE_SCREEN_HEIGHT; tilt_s=max(40,int(80*sf_ui)); tilt_y=screen_height-tilt_s-10; left_tilt_rect=pygame.Rect(10,tilt_y,tilt_s,tilt_s); right_tilt_rect=pygame.Rect(screen_width-tilt_s-10,tilt_y,tilt_s,tilt_s); left_pressed=False; right_pressed=False

    clock = pygame.time.Clock(); last_time = time.time(); running = True

    # --- Spiel-Loop ---
    while running:
        current_time = time.time(); dt = min(current_time - last_time, 0.1)
        if dt <= 0: dt = 1/60.0
        last_time = current_time; mouse_pos = pygame.mouse.get_pos()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False; game_result = False; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False; game_result = False; continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect and back_rect.collidepoint(event.pos): running = False; game_result = False; continue
                if is_android and dispenser.state=="open":
                    if left_tilt_rect.collidepoint(event.pos): left_pressed=True
                    elif right_tilt_rect.collidepoint(event.pos): right_pressed=True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                 if is_android and dispenser.state=="open" and not pygame.mouse.get_pressed()[0]: left_pressed=False; right_pressed=False
            dispenser.handle_event(event)

        # Logik
        if not is_android and dispenser.state=="open":
            keys=pygame.key.get_pressed()
            if keys[pygame.K_q]: dispenser.target_angle+=TILT_SPEED*dt
            elif keys[pygame.K_e]: dispenser.target_angle-=TILT_SPEED*dt
        if is_android and dispenser.state=="open":
            if left_pressed: dispenser.target_angle+=TILT_SPEED*dt
            elif right_pressed: dispenser.target_angle-=TILT_SPEED*dt

        new_particles=dispenser.update(dt)
        if new_particles: earth_particles.extend(new_particles)
        remaining_particles=[]; landed=0
        for p in earth_particles:
            if p.update(dt,screen_height):
                if bottom_container.rect.colliderect(p.rect): landed+=1
                else: remaining_particles.append(p)
        earth_particles = remaining_particles
        if landed>0:
            bottom_container.add_fill(landed)
            if sound_effect_1 and random.random()<0.2: sound_effect_1.play()
        if bottom_container.fill_level>=1.0:
            running=False; game_result=True; print("INFO: Behälter voll!") # Erfolg!

        # Zeichnen
        screen.fill(SKY_BLUE)
        if use_bg_img and scaled_bg_img: screen.blit(scaled_bg_img, (0,0))
        bottom_container.draw(screen); dispenser.draw(screen)
        for p in earth_particles: p.draw(screen)
        # UI
        if is_android and dispenser.state=="open":
             pygame.draw.rect(screen,RED if left_pressed else DARK_GRAY,left_tilt_rect); pygame.draw.rect(screen,BLACK,left_tilt_rect,2); arr_l=[(left_tilt_rect.centerx-tilt_s*.2,left_tilt_rect.centery),(left_tilt_rect.centerx+tilt_s*.2,left_tilt_rect.top+tilt_s*.2),(left_tilt_rect.centerx+tilt_s*.2,left_tilt_rect.bottom-tilt_s*.2)]; pygame.draw.polygon(screen,WHITE,arr_l)
             pygame.draw.rect(screen,RED if right_pressed else DARK_GRAY,right_tilt_rect); pygame.draw.rect(screen,BLACK,right_tilt_rect,2); arr_r=[(right_tilt_rect.centerx+tilt_s*.2,right_tilt_rect.centery),(right_tilt_rect.centerx-tilt_s*.2,right_tilt_rect.top+tilt_s*.2),(right_tilt_rect.centerx-tilt_s*.2,right_tilt_rect.bottom-tilt_s*.2)]; pygame.draw.polygon(screen,WHITE,arr_r)
        if info_font:
            fill_p=int(bottom_container.fill_level*100); txt_y=(back_rect.bottom+10) if back_rect else 10
            try: fill_surf=info_font.render(f"Füllstand: {fill_p}%",True,BLACK); screen.blit(fill_surf,(10,txt_y))
            except Exception as e: print(f"FEHLER Info-Text: {e}")
        if game_result and info_font: # Zeige "Fertig" nur wenn erfolgreich
            try: fin_surf=info_font.render("Fertig!",True,GREEN,DARK_GRAY); fin_rect=fin_surf.get_rect(center=(screen_width/2,screen_height/2)); screen.blit(fin_surf,fin_rect)
            except Exception as e: print(f"FEHLER Fertig-Text: {e}")
        if back_rect: # Back Button
            hover=back_rect.collidepoint(mouse_pos); img=None
            if use_back_img: img=scaled_back_hover if hover else scaled_back_bg
            if img: screen.blit(img,back_rect.topleft)
            else: col=DARK_GRAY if hover else GRAY; pygame.draw.rect(screen,col,back_rect); pygame.draw.rect(screen,BLACK,back_rect,2)
            if (not use_back_img or not scaled_back_bg) and button_font:
                try: b_surf=button_font.render("Zurück",True,BLACK); b_rect=b_surf.get_rect(center=back_rect.center); screen.blit(b_surf,b_rect)
                except Exception as e: print(f"FEHLER Button-Text: {e}")

        pygame.display.flip()
        clock.tick(60)

    # Schleife beendet
    print(f"INFO (EarthFiller): Minispiel beendet. Erfolg: {game_result}")
    return game_result # Gibt True bei Erfolg, False bei Abbruch zurück

# --- Standalone Code ---
if __name__ == "__main__":
    print("INFO: plant_grow1.py wird eigenständig ausgeführt.")
    success = False
    try:
        pygame.init()
        try: pygame.font.init()
        except: print("FEHLER pygame.font.init()")
        if not pygame.mixer.get_init():
            try: pygame.mixer.init(buffer=1024)
            except: print("WARNUNG: Mixer fehlgeschlagen")
        try: _info=pygame.display.Info(); _sw,_sh=_info.current_w,_info.current_h
        except: _sw,_sh=800,600
        standalone_screen = pygame.display.set_mode((_sw,_sh), pygame.RESIZABLE)
        pygame.display.set_caption("Plant Grow Minigame (Standalone Test)")
        print("\n--- Starte Minispiel Standalone ---\n")
        success = run_minigame_earth_filler(standalone_screen) # Ergebnis speichern
    except Exception as e_main:
        print(f"\n!!! FEHLER im Standalone-Modus: {e_main} !!!\n"); traceback.print_exc()
    finally:
        print(f"\n--- Standalone Beendet. Erfolg: {success} ---")
        pygame.quit()
        sys.exit(0 if success else 1) # Exit Code 0 bei Erfolg, sonst 1