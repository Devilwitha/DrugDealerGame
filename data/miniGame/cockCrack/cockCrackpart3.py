# -*- coding: utf-8 -*-
# cockCrackpart3.py - V9 - Stoppt Sound vor Part 4 (KORRIGIERT V4)
import pygame
import sys
import math
import os
import traceback
import time
import random

try:
    # Versuche relativen Import zuerst
    from . import cockCrackpart4 # <<< NEU
    print("DEBUG: cockCrackpart4 relativ importiert.")
except ImportError:
    try:
        import cockCrackpart4 # <<< NEU
        print("DEBUG: cockCrackpart4 direkt importiert.")
    except ImportError as e:
        print(f"FEHLER: Konnte cockCrackpart4 nicht importieren: {e}")
        cockCrackpart4 = None # Setze auf None, falls es fehlt
# --- ENDE IMPORTS ---


# --- Konstanten und Farben ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
CENTER_RECT_COLOR = (50, 50, 50)
INTERACTION_CIRCLE_COLOR = ORANGE

# --- Dateinamen für Bilder ---
background_image_filename = "laborTable.png"
top_bar_blue_bg_filename = "bar_blue_bg.png"
top_bar_green_overlay_filename = "bar_green_overlay.png"
arrow_indicator_filename = "arrow_indicator.png"
lower_panel_bg_filename = "lower_panel_bg.png"
interaction_button_up_filename = "interaction_button_up.png"
interaction_button_down_filename = "interaction_button_down.png"
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
animation_filenames = [
    "flame_anim_frame_1.png", "flame_anim_frame_2.png", "flame_anim_frame_3.png",
    "flame_anim_frame_4.png", "flame_anim_frame_5.png", "flame_anim_frame_6.png",
    "flame_anim_frame_7.png", "flame_anim_frame_8.png",
]

# --- Sound-Dateinamen ---
sound_filename_score = "bagFinish.wav"
sound_filename_no_resource = "error.wav"
# !!! ERSETZE DIESEN DATEINAMEN durch deine WAV-Datei !!!
arrow_moving_sound_filename = "gasfire.wav" # <<< Platzhalter für Bewegungs-Sound

# --- Hauptfunktion des Spiels ---
def run_cock_crack_game(screen_surface, start_pills, start_liquid, start_crack, liquid_id, pills_id):
    """ Führt das modifizierte CockCrack Minispiel aus (V9 Kette Part3->Part4, Sound-Stopp vor Part 4). """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    print(f"DEBUG (cockCrack V9): Nutze Screen-Größe: {actual_screen_size}")

    # Interne Statusvariablen
    current_pills = start_pills
    current_liquid = start_liquid
    current_crack = start_crack
    liquid_name = liquid_id
    pills_name = pills_id
    print(f"DEBUG (cockCrack V9): Startwerte: Pills={current_pills}, Liquid={current_liquid}, Crack={current_crack}")

    # Referenz-Dimensionen
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # Mixer Initialisierung
    score_sound = None
    no_resource_sound = None
    arrow_moving_sound = None
    mixer_ok = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (cockCrack V9): Mixer initialisiert.")
            mixer_ok = True
        except pygame.error as e:
            print(f"WARNUNG (cockCrack V9): Mixer fehlgeschlagen: {e}")
    else:
        print("DEBUG (cockCrack V9): Mixer war bereits initialisiert.")
        mixer_ok = True

    # --- PFAD-SETUP ---
    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    project_root_folder = os.path.join(script_dir_game, "..", "..", "..") # Anpassen!
    data_subfolder = "data"
    image_folder_rel = os.path.join(data_subfolder, "bilder")
    sound_folder_rel = os.path.join(data_subfolder, "sounds")
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, image_folder_rel))
    sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, sound_folder_rel))
    print(f"DEBUG (cockCrack V9): Image folder (abs): {image_folder_abs}")
    print(f"DEBUG (cockCrack V9): Sound folder (abs): {sound_folder_abs}")
    # --- ENDE PFAD-SETUP ---

    # Zustand für Mechanik
    arrow_width, arrow_height = 30, 30
    arrow_x = 0
    arrow_speed, arrow_return_speed_factor = 150, 1.5
    arrow_moving_right, arrow_momentum_timer = False, 0.0
    momentum_factor = 0.8
    circle_held_down, press_start_time = False, 0.0
    time_in_green_zone, goal_duration = 0.0, 5.0
    goal_achieved_this_round, can_trigger_win = False, True

    # Animation
    animation_frames, animation_index, animation_timer = [], 0, 0.0
    animation_frame_duration, show_animation = 0.1, False

    # Sound-Status
    is_arrow_sound_playing = False

    # --- Android Immersive Mode & Platform Detection ---
    is_android = False
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        print("DEBUG (cockCrack V9): Pyjnius importiert.")
        Build = autoclass('android.os.Build$VERSION')
        sdk_int = Build.SDK_INT
        if sdk_int > 0:
            is_android = True
            print(f"DEBUG (cockCrack V9): Android erkannt (SDK: {sdk_int}).")
        else:
             raise RuntimeError("Nicht Android")
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
                def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
                @java_method('()V')
                def run(self):
                    try:
                        w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f)
                        w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                    except Exception as e: print(f"FEHLER (Runnable): {e}"); traceback.print_exc()
        runnable = SetUiVisibilityRunnablePJC(activity, flags)
        if activity: activity.runOnUiThread(runnable); print("DEBUG (cockCrack V9): Runnable Immersive gestartet.")
    except ImportError: print("INFO (cockCrack V9): Pyjnius nicht gefunden. Nicht Android."); is_android = False
    except Exception as e: print(f"FEHLER/Info (cockCrack V9): Immersive Mode fehlgeschlagen/nicht Android: {e}"); is_android = False


    # --- SPIEL ELEMENTE DEFINITIONEN ---
    center_rect_width = int(screen_width * 0.4)
    center_rect_height = int(screen_height * 0.4)
    center_rect_x = screen_center_x - center_rect_width // 2
    bottom_rect_top_y = screen_center_y + int(screen_height * 0.05)
    bottom_margin = int(screen_height * 0.05)
    center_rect_y = min(bottom_rect_top_y, screen_height - center_rect_height - bottom_margin)
    center_rect_y = max(center_rect_y, screen_center_y)
    center_rect = pygame.Rect(center_rect_x, center_rect_y, center_rect_width, center_rect_height)

    anim_frame_width = int(center_rect_width * 0.5); anim_frame_height = int(anim_frame_width * 0.5)

    bar_height = int(screen_height * 0.04); bar_top_margin = int(screen_height * 0.10)
    extra_width_side = int(center_rect_width * 0.10); bar_width = center_rect_width + (2 * extra_width_side)
    bar_x = screen_center_x - bar_width // 2; bar_y = bar_top_margin
    bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

    green_area_width = int(bar_width * 0.1); green_area_x = bar_rect.centerx - green_area_width // 2
    green_area_rect = pygame.Rect(green_area_x, bar_rect.top, green_area_width, bar_rect.height)

    arrow_x = bar_rect.left

    interaction_circle_radius = int(min(center_rect_width, center_rect_height) * 0.12)
    interaction_circle_x = center_rect.centerx; interaction_circle_y = center_rect.top + int(center_rect.height * 0.75)
    interaction_circle_pos = (interaction_circle_x, interaction_circle_y)
    interaction_circle_rect = pygame.Rect(
        interaction_circle_x - interaction_circle_radius, interaction_circle_y - interaction_circle_radius,
        interaction_circle_radius * 2, interaction_circle_radius * 2
    )

    BACK_BUTTON_WIDTH_PERCENT, BACK_BUTTON_HEIGHT_PERCENT = 0.20, 0.08
    back_button_width = int(screen_width * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(screen_height * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_y = max(0, (bar_top_margin // 2) - (back_button_height // 2))
    back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, back_button_y, back_button_width, back_button_height)

    # --- Assets Laden ---
    def load_and_scale(filename, size):
        path = os.path.join(image_folder_abs, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            scaled_img = pygame.transform.smoothscale(img, size)
            print(f"DEBUG: Bild '{filename}' geladen und skaliert.")
            return scaled_img, True
        except Exception as e:
            if not os.path.exists(path): print(f"WARNUNG: Bilddatei nicht gefunden: '{path}'")
            else: print(f"WARNUNG: Bild '{path}' laden/skalieren fehlgeschlagen: {e}")
            return None, False

    scaled_background_image, use_background_image = load_and_scale(background_image_filename, actual_screen_size)
    scaled_top_bar_blue, use_top_bar_blue_image = load_and_scale(top_bar_blue_bg_filename, bar_rect.size)
    scaled_green_area_overlay, use_green_area_overlay_image = load_and_scale(top_bar_green_overlay_filename, green_area_rect.size)
    scaled_arrow_indicator, use_arrow_indicator_image = load_and_scale(arrow_indicator_filename, (arrow_width, arrow_height))
    scaled_lower_panel_bg, use_lower_panel_bg_image = load_and_scale(lower_panel_bg_filename, center_rect.size)
    scaled_interaction_button_up, use_interaction_button_images_up = load_and_scale(interaction_button_up_filename, (interaction_circle_radius * 2, interaction_circle_radius * 2))
    scaled_interaction_button_down, use_interaction_button_images_down = load_and_scale(interaction_button_down_filename, (interaction_circle_radius * 2, interaction_circle_radius * 2))
    use_interaction_button_images = use_interaction_button_images_up and use_interaction_button_images_down
    scaled_back_button_bg, use_back_button_images_bg = load_and_scale(back_button_bg_filename, back_button_rect.size)
    scaled_back_button_hover, use_back_button_images_hover = load_and_scale(back_button_hover_filename, back_button_rect.size)
    use_back_button_images = use_back_button_images_bg and use_back_button_images_hover

    for filename in animation_filenames:
        scaled_frame, success = load_and_scale(filename, (anim_frame_width, anim_frame_height))
        if success: animation_frames.append(scaled_frame)

    # --- Basisschriftgrößen ---
    BASE_GAME_FONT_SIZE = 36; BASE_INFO_FONT_SIZE = 18; BASE_BACK_FONT_SIZE = 24

    # --- Schriftarten ---
    def load_font(base_size, sys_font_name="arial"):
        scaled_size = max(12, int(screen_height * (base_size / FONT_SIZE_REF_H)))
        try: font_obj = pygame.font.SysFont(sys_font_name, scaled_size); return font_obj, scaled_size
        except: pass
        try: font_obj = pygame.font.Font(None, scaled_size); return font_obj, scaled_size
        except: pass
        print(f"WARNUNG: Schriftart (Basis {base_size}) nicht ladbar, nutze Fallback."); return pygame.font.Font(None, int(base_size * 0.8)), int(base_size * 0.8)

    font, game_font_size = load_font(BASE_GAME_FONT_SIZE)
    info_font, info_font_size = load_font(BASE_INFO_FONT_SIZE)
    back_button_font, back_font_size = load_font(BASE_BACK_FONT_SIZE)
    back_text_surface = back_button_font.render("Zurück", True, BLACK) if back_button_font else None

    # --- Sounds laden ---
    def load_sound(filename, volume=0.8):
        path = os.path.join(sound_folder_abs, filename)
        if mixer_ok and os.path.exists(path):
            try: sound_obj = pygame.mixer.Sound(path); sound_obj.set_volume(volume); print(f"DEBUG: Sound '{filename}' geladen."); return sound_obj
            except Exception as e: print(f"WARNUNG: Sound '{path}' laden fehlgeschlagen: {e}")
        elif mixer_ok:
            if filename != arrow_moving_sound_filename: print(f"INFO: Sounddatei '{path}' nicht gefunden.")
            else: print(f"INFO: Platzhalter-Sounddatei '{path}' nicht gefunden (ersetzen!).")
        return None

    score_sound = load_sound(sound_filename_score, 0.9)
    no_resource_sound = load_sound(sound_filename_no_resource, 0.7)
    arrow_moving_sound = load_sound(arrow_moving_sound_filename, 0.6)

    # --- Statusanzeige Position ---
    status_pos_x = max(10, int(screen_width * 0.02))
    status_start_y = bar_rect.bottom + int(screen_height * 0.02)
    status_pos_y = status_start_y
    resource_pos_y = status_pos_y + max(12, game_font_size) + 10

    # --- UI Elemente ---
    game_over_delay_timer = 0.0
    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    try:
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
                        if interaction_circle_rect.collidepoint(event.pos):
                            if not circle_held_down:
                                press_start_time = time.time(); arrow_moving_right = True
                                arrow_momentum_timer = 0.0; circle_held_down = True
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if circle_held_down:
                            press_duration = time.time() - press_start_time
                            arrow_momentum_timer = press_duration * momentum_factor; circle_held_down = False

            # --- Spiel-Logik Update ---
            # Pfeilbewegung
            if circle_held_down: arrow_x += arrow_speed * dt; arrow_x = min(arrow_x, bar_rect.right); arrow_moving_right = True
            elif arrow_momentum_timer > 0:
                arrow_momentum_timer -= dt; arrow_x += arrow_speed * dt; arrow_x = min(arrow_x, bar_rect.right)
                if arrow_x >= bar_rect.right or arrow_momentum_timer <= 0: arrow_momentum_timer = 0; arrow_moving_right = False
            elif not arrow_moving_right and arrow_x > bar_rect.left: arrow_x -= arrow_speed * arrow_return_speed_factor * dt; arrow_x = max(arrow_x, bar_rect.left)

            # Bewegungs-Sound Logik
            arrow_is_moving_now = circle_held_down or arrow_momentum_timer > 0 or (not arrow_moving_right and arrow_x > bar_rect.left)
            if arrow_is_moving_now and not is_arrow_sound_playing:
                if arrow_moving_sound: arrow_moving_sound.play(loops=-1); is_arrow_sound_playing = True
            elif not arrow_is_moving_now and is_arrow_sound_playing:
                if arrow_moving_sound: arrow_moving_sound.stop(); is_arrow_sound_playing = False

            # Animation
            if arrow_is_moving_now:
                show_animation = True; animation_timer += dt
                if animation_timer >= animation_frame_duration and len(animation_frames) > 0:
                    animation_timer -= animation_frame_duration; animation_index = (animation_index + 1) % len(animation_frames)
            else: show_animation = False; animation_index = 0; animation_timer = 0.0

            # Ziel-Überprüfung
            is_in_green = green_area_rect.left <= arrow_x <= green_area_rect.right
            if is_in_green:
                if not goal_achieved_this_round: time_in_green_zone += dt
            else: time_in_green_zone = 0


            # -------- Part 3 -> Part 4 Logik --------
            if can_trigger_win and time_in_green_zone >= goal_duration and not goal_achieved_this_round:
                goal_achieved_this_round = True; can_trigger_win = False
                print(f"INFO (V9): Ziel erreicht! {goal_duration}s im grünen Bereich.")
                needed_pills, needed_liquid = 1, 1
                part3_successful = False; points_from_part3 = 0

                if current_pills >= needed_pills and current_liquid >= needed_liquid:
                    print(f"INFO (V9): Genug Ressourcen für Part 3 Erfolg.")
                    part3_successful = True; points_from_part3 = 1

                    if part3_successful:
                        print(f"INFO (V9): {points_from_part3} Punkt(e) aus Part 3. Verbrauche Ressourcen & starte Part 4...")
                        current_pills -= needed_pills; current_liquid -= needed_liquid
                        current_crack += points_from_part3
                        print(f"DEBUG (V9): Ressourcen nach Part 3: Pills={current_pills}, Liquid={current_liquid}, Crack={current_crack}")

                        points_from_part4 = 0; part4_successful = False
                        if cockCrackpart4:
                            # --- Sound explizit vor Part 4 stoppen --- <<< NEUE ÄNDERUNG
                            if is_arrow_sound_playing and arrow_moving_sound:
                                print("DEBUG (V9): Stoppe Bewegungs-Sound vor Aufruf von Part 4.")
                                arrow_moving_sound.stop()
                                is_arrow_sound_playing = False
                            # --- Ende Sound Stopp ---

                            print(f"INFO (V9): Starte cockCrackpart4...")
                            try:
                                points_from_part4 = cockCrackpart4.run_minigame_timer(
                                    screen, current_pills, current_liquid, current_crack, liquid_name, pills_name
                                )
                                print(f"DEBUG (V9): cockCrackpart4 beendet. Ergebnis: {points_from_part4}")
                                if points_from_part4 > 0:
                                    current_crack += points_from_part4
                                    print(f"INFO (V9): {points_from_part4} Punkt(e) aus Part 4. Neuer Crack: {current_crack}")
                                    part4_successful = True
                                    if score_sound: score_sound.play()
                                    game_over_delay_timer = 2.0
                                else: print("INFO (V9): cockCrackpart4 ohne Punkt beendet."); game_over_delay_timer = 1.5
                            except AttributeError as e_attr4:
                                print(f"FEHLER (V9): Funktion (vermutl. run_minigame_timer) nicht in cockCrackpart4 gefunden! {e_attr4}")
                                if no_resource_sound: no_resource_sound.play(); game_over_delay_timer = 1.5
                            except Exception as e_part4:
                                print(f"FEHLER (V9) beim Ausführen von cockCrackpart4: {e_part4}"); traceback.print_exc()
                                if no_resource_sound: no_resource_sound.play(); game_over_delay_timer = 1.5
                        else:
                            print("FEHLER (V9): Modul cockCrackpart4 konnte nicht importiert werden!")
                            if no_resource_sound: no_resource_sound.play(); game_over_delay_timer = 1.5
                else: # Nicht genug Ressourcen initial
                    print(f"INFO (V9): Ziel erreicht, aber NICHT genug Ressourcen! Benötigt: {needed_pills}P, {needed_liquid}L.")
                    if no_resource_sound: no_resource_sound.play(); game_over_delay_timer = 1.5
            # -------- Ende Part 3 -> Part 4 Logik --------


            # Reset Timer Logik
            if game_over_delay_timer > 0 and not circle_held_down:
                game_over_delay_timer -= dt
                if game_over_delay_timer <= 0:
                    print("DEBUG (cockCrack V9): Reset nach Cooldown.")
                    arrow_x = bar_rect.left; arrow_moving_right = False; arrow_momentum_timer = 0.0
                    time_in_green_zone = 0.0; goal_achieved_this_round = False; can_trigger_win = True
                    show_animation = False; animation_index = 0; animation_timer = 0.0
                    if is_arrow_sound_playing and arrow_moving_sound:
                        arrow_moving_sound.stop(); is_arrow_sound_playing = False


            # --- Zeichnen ---
            if use_background_image and scaled_background_image: screen.blit(scaled_background_image, (0, 0))
            else: screen.fill(WHITE)
            if use_top_bar_blue_image and scaled_top_bar_blue: screen.blit(scaled_top_bar_blue, bar_rect.topleft)
            else: pygame.draw.rect(screen, BLUE, bar_rect)
            if use_green_area_overlay_image and scaled_green_area_overlay: screen.blit(scaled_green_area_overlay, green_area_rect.topleft)
            else: pygame.draw.rect(screen, GREEN, green_area_rect)
            arrow_draw_x = max(bar_rect.left + arrow_width/2, min(arrow_x, bar_rect.right - arrow_width/2))
            if use_arrow_indicator_image and scaled_arrow_indicator:
                arrow_rect = scaled_arrow_indicator.get_rect(midbottom=(int(arrow_draw_x), bar_rect.bottom)); screen.blit(scaled_arrow_indicator, arrow_rect)
            else:
                arrow_points = [(int(arrow_draw_x), bar_rect.bottom - arrow_height), (int(arrow_draw_x - arrow_width / 2), bar_rect.bottom), (int(arrow_draw_x + arrow_width / 2), bar_rect.bottom)]
                pygame.draw.polygon(screen, RED, arrow_points)
            if info_font:
                time_text_str = f"In Grün: {time_in_green_zone:.1f}s / {goal_duration:.1f}s"; time_text_color = GREEN if goal_achieved_this_round else BLACK
                time_text = info_font.render(time_text_str, True, time_text_color); time_text_rect = time_text.get_rect(midleft=(bar_rect.right + 10, bar_rect.centery))
                if time_text_rect.right > screen_width - 5: time_text_rect.right = screen_width - 5
                screen.blit(time_text, time_text_rect)
            if use_lower_panel_bg_image and scaled_lower_panel_bg: screen.blit(scaled_lower_panel_bg, center_rect.topleft)
            else: pygame.draw.rect(screen, CENTER_RECT_COLOR, center_rect)
            if show_animation and animation_frames:
                current_frame_image = animation_frames[animation_index]; anim_padding_bottom = 10
                frame_rect = current_frame_image.get_rect(midbottom=(center_rect.centerx, center_rect.top - anim_padding_bottom)); screen.blit(current_frame_image, frame_rect)
            if use_interaction_button_images and scaled_interaction_button_up and scaled_interaction_button_down:
                current_button_image = scaled_interaction_button_down if circle_held_down else scaled_interaction_button_up
                button_rect = current_button_image.get_rect(center=interaction_circle_pos); screen.blit(current_button_image, button_rect)
            else:
                pygame.draw.circle(screen, INTERACTION_CIRCLE_COLOR, interaction_circle_pos, interaction_circle_radius)
                if circle_held_down: pygame.draw.circle(screen, WHITE, interaction_circle_pos, interaction_circle_radius, 2)
            if font: crack_text = font.render(f"Crack: {current_crack}", True, RED); screen.blit(crack_text, (status_pos_x, status_pos_y))
            if info_font:
                pills_text = info_font.render(f"Pillen: {current_pills}", True, BLACK); liquid_text = info_font.render(f"Liquid: {current_liquid}", True, BLACK)
                screen.blit(pills_text, (status_pos_x, resource_pos_y)); screen.blit(liquid_text, (status_pos_x, resource_pos_y + info_font_size + 5))
            if back_button_rect:
                is_hovering = back_button_rect.collidepoint(mouse_pos)
                current_back_img = scaled_back_button_hover if is_hovering and use_back_button_images and scaled_back_button_hover else scaled_back_button_bg
                if use_back_button_images and current_back_img: screen.blit(current_back_img, back_button_rect.topleft)
                elif not use_back_button_images: pygame.draw.rect(screen, DARK_GRAY if is_hovering else GRAY, back_button_rect); pygame.draw.rect(screen, BLACK, back_button_rect, 2)
                if back_text_surface and back_button_font: text_rect = back_text_surface.get_rect(center=back_button_rect.center); screen.blit(back_text_surface, text_rect)

            pygame.display.flip()
            clock.tick(60)

    finally:
        if is_arrow_sound_playing and arrow_moving_sound:
            print("DEBUG (cockCrack V9): Stoppe Bewegungs-Sound beim Beenden.")
            arrow_moving_sound.stop()
        print("INFO (cockCrack V9): Minispiel-Schleife beendet.")

    return current_pills, current_liquid, current_crack

# --- Standalone Code ---
if __name__ == "__main__":
    print("INFO: cockCrackpart3.py (V9 Sound-Stopp) wird eigenständig ausgeführt.")
    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    standalone_screen = None
    try:
        try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
        except Exception: _sw = 800; _sh = 600
        standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption("CockCrack Minispiel Part 3 (V9 - Standalone)")

        start_pills_sa, start_liquid_sa, start_crack_sa = 5, 5, 0
        liquid_name_sa, pills_name_sa = "WasserID", "TafelganID"
        print(f"\n--- Starte Standalone mit: Pills={start_pills_sa}, Liquid={start_liquid_sa}, Crack={start_crack_sa} ---\n")

        final_pills, final_liquid, final_crack = run_cock_crack_game(
            standalone_screen, start_pills_sa, start_liquid_sa, start_crack_sa, liquid_name_sa, pills_name_sa
        )
        print(f"\n--- Standalone Part 3 (inkl. Versuch Part 4) Beendet. Ergebnis: ---")
        print(f"  Verbleibende Pillen: {final_pills}")
        print(f"  Verbleibende Flüssigkeit: {final_liquid}")
        print(f"  Erzeugtes Crack (inkl. Part 4, falls erfolgreich): {final_crack}")
        print("--------------------------------------------------------------\n")
    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}"); traceback.print_exc()
    finally:
        pygame.mixer.stop() # Stoppt alle Sounds
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---