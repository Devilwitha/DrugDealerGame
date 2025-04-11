# -*- coding: utf-8 -*-
# cockCrackpart4.py - V7 - Mit 2 Animationen (BG + Timer, Timer skaliert)
import pygame
import sys
import os
import traceback
import time
import random

try:
    import jnius
    print("Platform: Android")
except:
    print("Platform: Windows/Other")

# --- Konstanten und Farben ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
RED = (200, 0, 0)
TIMER_COLOR = BLACK

# --- Dateinamen für Assets ---
background_image_filename = "liquid_timer_background.png" # Layer 1
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
sound_effect_success_filename = "success.wav"
sound_effect_cocking_filename = "liquid_cocking.wav"

# --- Dateinamen für Hintergrund-Animations-Layer (Layer 2) ---
# !!! ERSETZE DIESE DATEINAMEN (4 Frames) !!!
bg_layer_animation_filenames = [
    "liquid_timer_bubble_frame1.png",
    "liquid_timer_bubble_frame2.png",
    "liquid_timer_bubble_frame3.png",
    "liquid_timer_bubble_frame4.png",
]

# --- Dateinamen für Timer-Animation (8 Frames) ---
# !!! ERSETZE DIESE DATEINAMEN (8 Frames) !!!
timer_animation_filenames = [
    "flame_anim_frame_1.png", # Original 700x700
    "flame_anim_frame_2.png",
    "flame_anim_frame_3.png",
    "flame_anim_frame_4.png",
    "flame_anim_frame_5.png",
    "flame_anim_frame_6.png",
    "flame_anim_frame_7.png",
    "flame_anim_frame_8.png",
]
# --- Ende Animations-Dateinamen ---

# --- NEU: Referenzgrößen für Timer-Animations-Skalierung ---
REF_SCREEN_WIDTH = 800.0
REF_SCREEN_HEIGHT = 600.0
# Gewünschte Größe der Animation auf dem Referenz-Bildschirm
TARGET_TIMER_ANIM_SIZE_REF = (250, 250)

# --- Hauptfunktion des Minispiels ---
def run_minigame_timer(screen_surface, start_resource1, start_resource2, start_score, id1, id2):
    """ Template für ein Pygame Minispiel mit Countdown-Timer und 2 Animationen (V7, Timer-Anim skaliert). """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    print(f"DEBUG (Timer Template V7): Nutze Screen-Größe: {actual_screen_size}")

    # --- NEU: Berechne die skalierte Größe für die Timer-Animation ---
    width_scale_factor = screen_width / REF_SCREEN_WIDTH
    height_scale_factor = screen_height / REF_SCREEN_HEIGHT
    # Wähle den kleineren Faktor, um das Seitenverhältnis beizubehalten und sicherzustellen, dass es passt
    # Optional: Wenn das Seitenverhältnis nicht quadratisch sein soll, beide Faktoren nutzen.
    # Hier nehmen wir an, das Ziel ist quadratisch, also den kleineren Faktor für beide Dimensionen
    scale_factor = min(width_scale_factor, height_scale_factor) # Behält Aspekt Ratio bei quadratischem Ziel
    # Oder, wenn die Skalierung unabhängig erfolgen soll:
    # scaled_timer_anim_width = int(TARGET_TIMER_ANIM_SIZE_REF[0] * width_scale_factor)
    # scaled_timer_anim_height = int(TARGET_TIMER_ANIM_SIZE_REF[1] * height_scale_factor)
    scaled_timer_anim_width = int(TARGET_TIMER_ANIM_SIZE_REF[0] * scale_factor) # Multipliziere Zielgröße mit Faktor
    scaled_timer_anim_height = int(TARGET_TIMER_ANIM_SIZE_REF[1] * scale_factor) # Multipliziere Zielgröße mit Faktor
    scaled_timer_anim_size = (max(1, scaled_timer_anim_width), max(1, scaled_timer_anim_height)) # Mindestens 1x1 Pixel
    print(f"DEBUG (Timer V7): Timer-Animation wird skaliert auf: {scaled_timer_anim_size}")
    # --- Ende Skalierungsberechnung ---

    # --- Interne Statusvariablen ---
    current_resource1 = start_resource1; current_resource2 = start_resource2; current_score = start_score
    identifier1 = id1; identifier2 = id2
    print(f"DEBUG (Timer V7): Startwerte: Pills={current_resource1}, Liquid={current_resource2}, Crack={current_score}")

    # Timer-Zustand
    timer_seconds = 300.0; timer_active = True; timer_finished_cooldown = 0.0; points_this_round = 0

    # --- Hintergrund-Animations-Zustand ---
    bg_layer_animation_frames = []; bg_layer_animation_index = 0; bg_layer_animation_timer = 0.0
    bg_layer_animation_frame_duration = 0.15

    # --- Timer-Animations-Zustand ---
    timer_animation_frames = []; timer_animation_index = 0; timer_animation_timer = 0.0
    timer_animation_frame_duration = 0.1

    # --- Referenz-Dimensionen für Fonts ---
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung ---
    success_sound = None; cockings_sound = None; mixer_ok = False
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024); print("DEBUG (Timer V7): Mixer initialisiert."); mixer_ok = True
        except pygame.error as e: print(f"WARNUNG (Timer V7): Mixer fehlgeschlagen: {e}")
    else: print("DEBUG (Timer V7): Mixer war bereits initialisiert."); mixer_ok = True

    # --- PFAD-SETUP ---
    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    project_root_folder = os.path.join(script_dir_game, "..", "..", "..") # Anpassen!
    data_subfolder = "data"; image_folder_rel = os.path.join(data_subfolder, "bilder"); sound_folder_rel = os.path.join(data_subfolder, "sounds")
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, image_folder_rel))
    sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, sound_folder_rel))
    print(f"DEBUG (Timer V7): Image folder (abs): {image_folder_abs}")
    print(f"DEBUG (Timer V7): Sound folder (abs): {sound_folder_abs}")
    # --- ENDE PFAD-SETUP ---

    # --- Android Immersive Mode ---
    is_android = False # Gekürzte Version für Lesbarkeit
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method; Build = autoclass('android.os.Build$VERSION'); sdk_int = Build.SDK_INT
        if sdk_int > 0: is_android = True; print(f"DEBUG (Timer V7): Android erkannt (SDK: {sdk_int})."); #... (Restlicher Immersive Code hier, nicht erneut abgedruckt)
        else: raise RuntimeError("Nicht Android")
    except ImportError: is_android = False; print("INFO (Timer V7): Pyjnius nicht gefunden.")
    except Exception as e: is_android = False; print(f"FEHLER (Timer V7) Android Immersive: {e}")

    # --- SPIEL ELEMENTE DEFINITIONEN ---
    BACK_BUTTON_WIDTH_PERCENT, BACK_BUTTON_HEIGHT_PERCENT, BASE_BACK_FONT_SIZE = 0.20, 0.08, 24
    back_button_width = int(screen_width * BACK_BUTTON_WIDTH_PERCENT); back_button_height = int(screen_height * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_y = 15; back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, back_button_y, back_button_width, back_button_height)
    status_pos_x = 20; status_pos_y = back_button_rect.bottom + 20

    # --- Assets Laden ---
    def load_and_scale(filename, size, alpha=True):
        path = os.path.join(image_folder_abs, filename)
        try:
            img = pygame.image.load(path); img = img.convert_alpha() if alpha else img.convert()
            scaled_img = pygame.transform.smoothscale(img, size)
            #print(f"DEBUG: Bild '{filename}' geladen/skaliert zu {size}.") # Weniger Output
            return scaled_img, True
        except Exception as e:
            if not os.path.exists(path): print(f"WARNUNG: Datei nicht gefunden: '{path}'")
            else: print(f"WARNUNG: Laden/Skalieren fehlgeschlagen: '{path}': {e}")
            return None, False

    # Layer 1: Statischer Hintergrund
    scaled_background_image, use_background_image = load_and_scale(background_image_filename, actual_screen_size, alpha=False)

    # Layer 2: Hintergrund-Animation laden
    for anim_file in bg_layer_animation_filenames:
        frame_img, success = load_and_scale(anim_file, actual_screen_size, alpha=True)
        if success: bg_layer_animation_frames.append(frame_img)
        else: print(f"FEHLER: BG-Anim Frame '{anim_file}' nicht ladbar!")
    use_bg_animation_layer = len(bg_layer_animation_frames) > 0
    if use_bg_animation_layer: print(f"DEBUG: {len(bg_layer_animation_frames)} BG-Anim Frames geladen.")

    # Timer-Animation laden (mit berechneter sklierter Größe)
    for anim_file in timer_animation_filenames:
        # Verwende die zuvor berechnete 'scaled_timer_anim_size'
        frame_img, success = load_and_scale(anim_file, scaled_timer_anim_size, alpha=True)
        if success: timer_animation_frames.append(frame_img)
        else: print(f"FEHLER: Timer-Anim Frame '{anim_file}' nicht ladbar!")
    use_timer_animation = len(timer_animation_frames) > 0
    if use_timer_animation: print(f"DEBUG: {len(timer_animation_frames)} Timer-Anim Frames geladen (skaliert).")


    # Andere UI-Elemente
    scaled_back_button_bg, use_back_button_images_bg = load_and_scale(back_button_bg_filename, back_button_rect.size)
    scaled_back_button_hover, use_back_button_images_hover = load_and_scale(back_button_hover_filename, back_button_rect.size)
    use_back_button_images = use_back_button_images_bg and use_back_button_images_hover

    # --- Schriftarten ---
    def load_font(base_size, sys_font_name="arial", bold=False):
        scaled_size = max(12, int(screen_height * (base_size / FONT_SIZE_REF_H)))
        try: font_obj = pygame.font.SysFont(sys_font_name, scaled_size, bold=bold); return font_obj, scaled_size
        except: pass
        try: 
            font_obj = pygame.font.Font(None, scaled_size);
            if font_obj and bold: font_obj.set_bold(True); return font_obj, scaled_size
        except: pass
        print(f"WARNUNG: Schrift (Basis {base_size}) nicht ladbar, Fallback."); fallback_font = pygame.font.Font(None, int(base_size * 0.8))
        if bold: fallback_font.set_bold(True); return fallback_font, int(base_size * 0.8)

    BASE_INFO_FONT_SIZE = 24; BASE_TIMER_FONT_SIZE = 60; BASE_BUTTON_FONT_SIZE = 20
    info_font, info_font_size = load_font(BASE_INFO_FONT_SIZE)
    timer_font, timer_font_size = load_font(BASE_TIMER_FONT_SIZE, bold=True)
    button_font, button_font_size = load_font(BASE_BUTTON_FONT_SIZE)

    # --- Sounds laden ---
    def load_sound(filename, volume=0.8):
        path = os.path.join(sound_folder_abs, filename)
        if mixer_ok and os.path.exists(path):
            try: sound_obj = pygame.mixer.Sound(path); sound_obj.set_volume(volume); return sound_obj
            except Exception as e: print(f"WARNUNG: Sound '{path}' laden fehlgeschlagen: {e}")
        #elif mixer_ok: print(f"INFO: Sounddatei '{path}' nicht gefunden.") # Weniger Output
        return None

    success_sound = load_sound(sound_effect_success_filename, 0.8)
    cockings_sound = load_sound(sound_effect_cocking_filename, 0.8)
    if cockings_sound: cockings_sound.play(loops=-1); print(f"DEBUG: Loop-Sound '{sound_effect_cocking_filename}' gestartet.")

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
            if event.type == pygame.QUIT: running = False; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False; continue
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button_rect and back_button_rect.collidepoint(event.pos): running = False; continue

        # --- Spiel-Logik Update ---
        # Timer
        if timer_active and timer_seconds > 0:
            timer_seconds -= dt
            if timer_seconds <= 0:
                timer_seconds = 0; points_this_round = 1
                if success_sound: success_sound.play()
                timer_active = False; timer_finished_cooldown = 1.5
        elif timer_finished_cooldown > 0:
            timer_finished_cooldown -= dt
            if timer_finished_cooldown <= 0: timer_seconds = 300.0; timer_active = True

        # Hintergrund-Animation aktualisieren
        if use_bg_animation_layer:
            bg_layer_animation_timer += dt
            if bg_layer_animation_timer >= bg_layer_animation_frame_duration:
                bg_layer_animation_timer -= bg_layer_animation_frame_duration
                bg_layer_animation_index = (bg_layer_animation_index + 1) % len(bg_layer_animation_frames)

        # Timer-Animation aktualisieren
        if use_timer_animation:
            timer_animation_timer += dt
            if timer_animation_timer >= timer_animation_frame_duration:
                timer_animation_timer -= timer_animation_frame_duration
                timer_animation_index = (timer_animation_index + 1) % len(timer_animation_frames)

        # --- Zeichnen (Angepasste Reihenfolge) ---
        # 1. Statischer Hintergrund
        if use_background_image and scaled_background_image: screen.blit(scaled_background_image, (0, 0))
        else: screen.fill(WHITE)

        # 2. Hintergrund-Animation (Layer 2)
        if use_bg_animation_layer:
            screen.blit(bg_layer_animation_frames[bg_layer_animation_index], (0, 0))

        # 3. Timer-Text
        timer_rect = None
        if timer_font:
            minutes = int(timer_seconds) // 60; seconds = int(timer_seconds) % 60; timer_text_str = f"{minutes:02d}:{seconds:02d}"
            timer_surf = timer_font.render(timer_text_str, True, TIMER_COLOR)
            padding_top_pixels = int(screen_height * 0.25); padding_right_pixels = int(screen_width * 0.23)
            timer_rect = timer_surf.get_rect(topright=(screen_width - padding_right_pixels, padding_top_pixels))
            screen.blit(timer_surf, timer_rect)

        # 4. Timer-Animation (unterhalb des Timers, skaliert)
        if use_timer_animation and timer_rect is not None:
            current_timer_anim_frame = timer_animation_frames[timer_animation_index]
            # HIER Position anpassen:
            timer_anim_padding_y = 10 # Vertikaler Abstand
            timer_anim_rect = current_timer_anim_frame.get_rect(
                midtop=(timer_rect.centerx, timer_rect.bottom + timer_anim_padding_y) # Zentriert unter Timer
            )
            screen.blit(current_timer_anim_frame, timer_anim_rect)

        # 5. Restliche UI-Elemente (Status, Button)
        if info_font:
            display_score = start_score + points_this_round; score_text = info_font.render(f"Punkte: {display_score}", True, BLACK)
            res1_text = info_font.render(f"{identifier1}: {current_resource1}", True, BLACK); res2_text = info_font.render(f"{identifier2}: {current_resource2}", True, BLACK)
            text_y = status_pos_y; screen.blit(score_text, (status_pos_x, text_y)); text_y += info_font_size + 5
            screen.blit(res1_text, (status_pos_x, text_y)); text_y += info_font_size + 5; screen.blit(res2_text, (status_pos_x, text_y))
        if back_button_rect:
            is_hovering = back_button_rect.collidepoint(mouse_pos)
            current_back_img = scaled_back_button_hover if is_hovering and use_back_button_images else scaled_back_button_bg
            if use_back_button_images and current_back_img: screen.blit(current_back_img, back_button_rect.topleft)
            elif not use_back_button_images: pygame.draw.rect(screen, DARK_GRAY if is_hovering else GRAY, back_button_rect); pygame.draw.rect(screen, BLACK, back_button_rect, 2)
            if button_font: back_text_surf = button_font.render("Zurück", True, BLACK); back_text_rect = back_text_surf.get_rect(center=back_button_rect.center); screen.blit(back_text_surf, back_text_rect)

        pygame.display.flip()
        clock.tick(60)
    # --- Ende der Spiel-Schleife ---

    print(f"INFO (Timer Template V7): Minispiel-Schleife beendet.")
    if cockings_sound: print("DEBUG (Timer V7): Stoppe Loop-Sound."); cockings_sound.stop()
    print(f"DEBUG (Timer Template V7): Gebe {points_this_round} Punkte zurück.")
    return points_this_round
# --- Ende der run_minigame_timer Funktion ---


# --- Standalone Code ---
if __name__ == "__main__":
    print("INFO: cockCrackpart4.py (Timer V7 mit 2 skal. Animationen) wird eigenständig ausgeführt.")
    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw, _sh = _info.current_w, _info.current_h
    except Exception: _sw, _sh = 800, 600; print(f"WARNUNG: Bildschirmgröße nicht erkannt, Fallback: {_sw}x{_sh}")
    else: print(f"DEBUG: Bildschirmgröße erkannt: {_sw}x{_sh}")

    standalone_screen = None
    try: standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE); print("DEBUG: Pygame Fenster erstellt.")
    except pygame.error as e_disp: print(f"FATAL: Konnte Fenster nicht erstellen: {e_disp}"); pygame.quit(); sys.exit()
    pygame.display.set_caption("Pygame Minispiel Timer Template V7 (Standalone)")

    start_res1_sa = 10; start_res2_sa = 5; start_score_sa = 0
    id1_sa = "PillsNachP3"; id2_sa = "LiquidNachP3"
    print(f"\n--- Starte Standalone mit: Res1={start_res1_sa}, Res2={start_res2_sa}, Score(Crack)={start_score_sa} ---\n")

    try:
        points_added_in_part4 = run_minigame_timer(standalone_screen, start_res1_sa, start_res2_sa, start_score_sa, id1_sa, id2_sa)
        print(f"\n--- Standalone Part 4 Beendet. Ergebnis: ---"); print(f"  In Part 4 erzielte Punkte: {points_added_in_part4}")
        print("-------------------------------------\n")
    except Exception as e_main: print(f"FEHLER in Standalone: {e_main}"); traceback.print_exc()
    finally: pygame.quit(); sys.exit()
# --- Ende Standalone-Code ---