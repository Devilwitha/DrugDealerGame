# -*- coding: utf-8 -*-
# pygame_minigame_template_v2.py - Mit Android-Erkennung
import pygame
import sys
import os
import traceback
import time
import random
try:
    import jnius
except:
    print("Kein Android Erkannt")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
TEMPLATE_COLOR_1 = (0, 100, 200)
TEMPLATE_COLOR_2 = (200, 100, 0)

# --- Dateinamen für Assets (Platzhalter) ---
# Definiere hier die Dateinamen für deine Bilder und Sounds
background_image_filename = "template_background.png" # Optionaler Hintergrund
# UI Elemente
ui_element_1_filename = "ui_element_1.png"
ui_element_2_up_filename = "button_up.png"
ui_element_2_down_filename = "button_down.png" # Für Klick-Feedback
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
# Animation (Beispiel)
animation_filenames = [
    "anim_frame_1.png",
    "anim_frame_2.png",
    "anim_frame_3.png",
    # ... mehr Frames ...
]
# Sounds
sound_effect_1_filename = "success.wav"
sound_effect_2_filename = "failure.wav"

# --- Hauptfunktion des Minispiels (Template) ---
def run_minigame_template(screen_surface, start_resource1, start_resource2, start_score, id1, id2):
    """ Template für ein Pygame Minispiel mit Bild-Assets und Animation. """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    print(f"DEBUG (Template): Nutze Screen-Größe: {actual_screen_size}")

    # --- Interne Statusvariablen ---
    # Initialisiere hier deine Spielzustandsvariablen
    current_resource1 = start_resource1
    current_resource2 = start_resource2
    current_score = start_score
    identifier1 = id1 # Beispielhafte Übernahme der IDs
    identifier2 = id2
    print(f"DEBUG (Template): Startwerte: Res1={current_resource1} ('{identifier1}'), Res2={current_resource2} ('{identifier2}'), Score={current_score}")

    # Spielspezifische Zustände
    game_state = "running" # z.B. 'running', 'paused', 'game_over'
    # Füge weitere Zustandsvariablen hinzu
    # Beispiel: player_x = screen_center_x

    # Animationsvariablen (falls verwendet)
    animation_frames = []
    animation_index = 0
    animation_timer = 0.0
    animation_frame_duration = 0.1 # Sekunden pro Frame
    show_animation = False

    # --- Referenz-Dimensionen (für Skalierung) ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0 # Referenz für Font-Skalierung

    # --- Mixer Initialisierung ---
    sound_effect_1 = None
    sound_effect_2 = None
    mixer_ok = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (Template): Mixer initialisiert.")
            mixer_ok = True
        except pygame.error as e:
            print(f"WARNUNG (Template): Mixer fehlgeschlagen: {e}")
    else:
        print("DEBUG (Template): Mixer war bereits initialisiert.")
        mixer_ok = True

    # --- PFAD-SETUP ---
    # (Diese Logik zum Finden der Asset-Ordner kannst du wahrscheinlich beibehalten)
    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    # *** ANPASSEN, FALLS DEINE STRUKTUR ANDERS IST! ***
    project_root_folder = os.path.join(script_dir_game, "..", "..", "..") # Beispiel: 3 Ebenen hoch
    data_subfolder = "data"
    image_folder_rel = os.path.join(data_subfolder, "bilder")
    sound_folder_rel = os.path.join(data_subfolder, "sounds")
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, image_folder_rel))
    sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, sound_folder_rel))
    print(f"DEBUG (Template): Script Dir: {script_dir_game}")
    print(f"DEBUG (Template): Image folder (abs): {image_folder_abs}")
    print(f"DEBUG (Template): Sound folder (abs): {sound_folder_abs}")
    # --- ENDE PFAD-SETUP ---

    # --- NEU: Android Immersive Mode & Platform Detection --- ### WICHTIG ###
    is_android = False # Standardmäßig nicht Android
    try: # Android Specific Code
        from jnius import autoclass, cast, PythonJavaClass, java_method
        print("DEBUG (Template Android): Pyjnius importiert.")
        Build = autoclass('android.os.Build$VERSION')
        sdk_int = Build.SDK_INT
        if sdk_int > 0:
            is_android = True # Hier wird erkannt, dass es Android ist
            print(f"DEBUG (Template Android): Android erkannt (SDK: {sdk_int}).")
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
                        w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON) # Bildschirm anlassen
                    except Exception as e:
                        print(f"FEHLER (Runnable): {e}")
                        traceback.print_exc()
        runnable = SetUiVisibilityRunnablePJC(activity, flags)
        if activity:
            activity.runOnUiThread(runnable)
            print("DEBUG (Template Android): Runnable Immersive gestartet.")
    except ImportError:
        print("INFO (Template Android): Pyjnius nicht gefunden. Nehme an, es ist nicht Android.")
        is_android = False # Sicherstellen, dass es False ist, wenn Import fehlschlägt
    except Exception as e:
        print(f"FEHLER oder Info (Template Android): Immersive Mode fehlgeschlagen oder nicht Android: {e}")
        # traceback.print_exc() # Optional: Traceback nur bei echtem Fehler anzeigen
        is_android = False # Sicherstellen, dass es False ist bei anderen Fehlern
    # --- Ende Android ---

    # --- SPIEL ELEMENTE DEFINITIONEN ---
    # Definiere hier die Rechtecke (Rects) und Positionen deiner UI-Elemente
    # basierend auf `screen_width`, `screen_height` oder relativen Werten.
    # Du kannst `is_android` hier verwenden, um Layout-Anpassungen vorzunehmen.

    # Beispiel: Ein Button in der Mitte unten
    button_width = int(screen_width * 0.2)
    button_height = int(screen_height * 0.1)
    button_x = screen_center_x - button_width // 2
    button_y = screen_height - button_height - int(screen_height * 0.05) # 5% Abstand unten
    example_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    is_button_pressed = False # Zustand für Klick-Feedback

    # Beispiel: Ein Anzeigebereich oben
    info_panel_width = int(screen_width * 0.9)
    info_panel_height = int(screen_height * 0.1)
    info_panel_x = screen_center_x - info_panel_width // 2
    info_panel_y = int(screen_height * 0.05)
    info_panel_rect = pygame.Rect(info_panel_x, info_panel_y, info_panel_width, info_panel_height)

    # Zurück-Button (oft nützlich)
    BACK_BUTTON_WIDTH_PERCENT, BACK_BUTTON_HEIGHT_PERCENT, BASE_BACK_FONT_SIZE = 0.20, 0.08, 24
    back_button_width = int(screen_width * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(screen_height * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_y = 10 # Fester Abstand von oben
    back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, back_button_y, back_button_width, back_button_height)

    # Position für Animation (Beispiel: mittig im Anzeigebereich oben)
    anim_frame_width = int(info_panel_height * 0.8) # Beispiel: Höhe an Panel anpassen
    anim_frame_height = anim_frame_width
    animation_pos_x = info_panel_rect.centerx
    animation_pos_y = info_panel_rect.centery

    # Beispiel: Touch-Steuerungselemente (nur wenn is_android == True)
    touch_control_1_rect = None
    if is_android:
        touch_button_size = int(screen_width * 0.15)
        touch_control_1_rect = pygame.Rect(
            screen_width - touch_button_size - 20, # Rechts unten
            screen_height - touch_button_size - 20,
            touch_button_size, touch_button_size
        )

    # --- Assets Laden ---
    # Lade hier deine spezifischen Bilder und skaliere sie auf die Grösse der Rects

    # Hintergrundbild (optional)
    scaled_background_image = None
    use_background_image = False
    background_path = os.path.join(image_folder_abs, background_image_filename)
    try:
        loaded_bg = pygame.image.load(background_path).convert()
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG (Template): Hintergrundbild '{background_image_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG (Template): Hintergrundbild '{background_path}' laden fehlgeschlagen: {e}.")

    # Beispiel: UI Element 1 laden
    scaled_ui_element_1 = None
    use_ui_element_1_image = False
    ui_element_1_path = os.path.join(image_folder_abs, ui_element_1_filename)
    try:
        img = pygame.image.load(ui_element_1_path).convert_alpha()
        scaled_ui_element_1 = pygame.transform.smoothscale(img, info_panel_rect.size) # Skaliere auf Panel-Größe
        use_ui_element_1_image = True
        print(f"DEBUG (Template): UI Element 1 '{ui_element_1_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG (Template): UI Element 1 laden/skalieren fehlgeschlagen: {e}")

    # Beispiel: Button-Bilder laden
    scaled_button_up = None
    scaled_button_down = None
    use_button_images = False
    button_up_path = os.path.join(image_folder_abs, ui_element_2_up_filename)
    button_down_path = os.path.join(image_folder_abs, ui_element_2_down_filename)
    try:
        img_up = pygame.image.load(button_up_path).convert_alpha()
        img_down = pygame.image.load(button_down_path).convert_alpha()
        scaled_button_up = pygame.transform.smoothscale(img_up, example_button_rect.size)
        scaled_button_down = pygame.transform.smoothscale(img_down, example_button_rect.size)
        use_button_images = True
        print(f"DEBUG (Template): Button-Bilder '{ui_element_2_up_filename}', '{ui_element_2_down_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG (Template): Button-Bilder laden/skalieren fehlgeschlagen: {e}")

    # Beispiel: Zurück-Button Bilder laden
    scaled_back_button_bg = None
    scaled_back_button_hover = None
    use_back_button_images = False
    back_bg_path = os.path.join(image_folder_abs, back_button_bg_filename)
    back_hover_path = os.path.join(image_folder_abs, back_button_hover_filename)
    try:
        img_bg = pygame.image.load(back_bg_path).convert_alpha()
        img_hover = pygame.image.load(back_hover_path).convert_alpha()
        scaled_back_button_bg = pygame.transform.smoothscale(img_bg, back_button_rect.size)
        scaled_back_button_hover = pygame.transform.smoothscale(img_hover, back_button_rect.size)
        use_back_button_images = True
        print(f"DEBUG (Template): Zurück-Buttons '{back_button_bg_filename}', '{back_button_hover_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG (Template): Zurück-Buttons laden/skalieren fehlgeschlagen: {e}")

    # Lade Animations-Frames (falls verwendet)
    for filename in animation_filenames:
        anim_path = os.path.join(image_folder_abs, filename)
        try:
            img = pygame.image.load(anim_path).convert_alpha()
            scaled_img = pygame.transform.smoothscale(img, (anim_frame_width, anim_frame_height))
            animation_frames.append(scaled_img)
            print(f"DEBUG (Template): Animationsframe '{filename}' geladen.")
        except Exception as e:
            print(f"WARNUNG (Template): Animationsframe '{anim_path}' laden/skalieren fehlgeschlagen: {e}")

    # --- Schriftarten ---
    # Definiere hier die Schriftarten, die du benötigst
    BASE_INFO_FONT_SIZE = 24
    info_font_size = max(12, int(screen_height * (BASE_INFO_FONT_SIZE / FONT_SIZE_REF_H)))
    info_font = None
    try: info_font = pygame.font.SysFont("arial", info_font_size)
    except: info_font = pygame.font.Font(None, info_font_size)
    if not info_font: info_font = pygame.font.Font(None, 24); info_font_size = 24 # Fallback

    BASE_BUTTON_FONT_SIZE = 20
    button_font_size = max(12, int(screen_height * (BASE_BUTTON_FONT_SIZE / FONT_SIZE_REF_H)))
    button_font = None
    try: button_font = pygame.font.SysFont("arial", button_font_size)
    except: button_font = pygame.font.Font(None, button_font_size)
    if not button_font: button_font = pygame.font.Font(None, 20); button_font_size = 20 # Fallback

    # --- Sounds laden ---
    sound_path_1 = os.path.join(sound_folder_abs, sound_effect_1_filename)
    sound_path_2 = os.path.join(sound_folder_abs, sound_effect_2_filename)
    if mixer_ok:
        try:
            sound_effect_1 = pygame.mixer.Sound(sound_path_1); sound_effect_1.set_volume(0.8) # Beispiel-Lautstärke
            print(f"DEBUG (Template): Sound 1 '{sound_effect_1_filename}' geladen.")
        except Exception as e:
            print(f"WARNUNG (Template): Sound 1 '{sound_path_1}' laden fehlgeschlagen: {e}")
            sound_effect_1 = None
        try:
            sound_effect_2 = pygame.mixer.Sound(sound_path_2); sound_effect_2.set_volume(0.8) # Beispiel-Lautstärke
            print(f"DEBUG (Template): Sound 2 '{sound_effect_2_filename}' geladen.")
        except Exception as e:
            print(f"WARNUNG (Template): Sound 2 '{sound_path_2}' laden fehlgeschlagen: {e}")
            sound_effect_2 = None
    # -------------------------------------

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1) # Delta time capped
        last_time = current_time

        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling ---
        is_button_pressed = False # Reset Klick-Zustand für Button-Bild
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("WARNUNG (Template): QUIT Event empfangen.")
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue
                # Füge hier deine Tastatur-Events hinzu (nur wenn nicht Android?)
                # if not is_android and event.key == pygame.K_SPACE:
                #    # Mache etwas...

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    # Zurück Button
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False
                        continue

                    # Beispiel Button
                    if example_button_rect.collidepoint(event.pos):
                        print("DEBUG (Template): Beispiel-Button geklickt!")
                        is_button_pressed = True # Für visuelles Feedback
                        # Füge hier die Logik für den Button-Klick hinzu
                        if current_resource1 > 0:
                             current_resource1 -= 1
                             current_score += 10
                             if sound_effect_1: sound_effect_1.play()
                             show_animation = True # Starte Animation bei Klick
                             animation_timer = 0.0
                             animation_index = 0
                        else:
                             if sound_effect_2: sound_effect_2.play()

                    # Beispiel Touch Control (nur wenn Android)
                    if is_android and touch_control_1_rect and touch_control_1_rect.collidepoint(event.pos):
                        print("DEBUG (Template): Touch Control 1 geklickt!")
                        # Füge Logik für Touch-Steuerung hinzu
                        if sound_effect_1: sound_effect_1.play()


            if event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1:
                     # Füge hier Logik für das Loslassen der Maustaste hinzu
                     # z.B. für den Beispiel-Button oder Touch-Controls
                     pass

            # --- Ende Event Handling ---

        # --- Spiel-Logik Update ---
        if game_state == "running":
            # Aktualisiere hier den Zustand deines Spiels basierend auf dt (Zeit)

            # Animations-Update (falls verwendet und aktiv)
            if show_animation and animation_frames:
                animation_timer += dt
                if animation_timer >= animation_frame_duration:
                    animation_timer -= animation_frame_duration
                    animation_index = (animation_index + 1) % len(animation_frames)
                    # if animation_index == 0: show_animation = False # Beispiel: Stop nach 1 Runde

            # Füge hier deine Spiel-Logik ein (Bewegung, Kollision, Timer, etc.)

        elif game_state == "game_over":
            # Logik für das Spielende
            pass
        # --- Ende Spiel-Logik Update ---


        # --- Zeichnen ---
        # Hintergrund
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        else:
            screen.fill(WHITE) # Fallback-Hintergrund

        # --- Zeichne deine Spielelemente ---

        # Beispiel: Oberes Info-Panel (Bild oder Fallback)
        if use_ui_element_1_image and scaled_ui_element_1:
            screen.blit(scaled_ui_element_1, info_panel_rect.topleft)
        else:
            pygame.draw.rect(screen, GRAY, info_panel_rect) # Fallback

        # Beispiel: Animation zeichnen (falls aktiv)
        if show_animation and animation_frames:
            current_frame_image = animation_frames[animation_index]
            frame_rect = current_frame_image.get_rect(center=animation_pos_x, centery=animation_pos_y) # Positionieren
            screen.blit(current_frame_image, frame_rect)

        # Beispiel: Button zeichnen (Bild oder Fallback)
        if use_button_images and scaled_button_up and scaled_button_down:
            current_button_image = scaled_button_down if is_button_pressed else scaled_button_up
            screen.blit(current_button_image, example_button_rect.topleft)
        else:
            # Fallback: Rechteck zeichnen
            btn_color = DARK_GRAY if is_button_pressed else GRAY
            pygame.draw.rect(screen, btn_color, example_button_rect)
            pygame.draw.rect(screen, BLACK, example_button_rect, 2)
            if button_font: # Fallback Text
                btn_text_surf = button_font.render("Aktion", True, BLACK)
                btn_text_rect = btn_text_surf.get_rect(center=example_button_rect.center)
                screen.blit(btn_text_surf, btn_text_rect)

        # Beispiel: Status-Text zeichnen (im Info-Panel)
        if info_font:
             score_text = info_font.render(f"Punkte: {current_score}", True, BLACK)
             res1_text = info_font.render(f"{identifier1}: {current_resource1}", True, BLACK)
             res2_text = info_font.render(f"{identifier2}: {current_resource2}", True, BLACK)
             # Positioniere Texte im Panel
             text_y_start = info_panel_rect.top + 10
             text_x_start = info_panel_rect.left + 10
             screen.blit(score_text, (text_x_start, text_y_start))
             screen.blit(res1_text, (text_x_start, text_y_start + info_font_size + 5))
             screen.blit(res2_text, (text_x_start, text_y_start + 2*(info_font_size + 5)))

        # Beispiel: Touch Control zeichnen (nur wenn Android)
        if is_android and touch_control_1_rect:
            # Hier könntest du ein Bild laden oder einfach ein Rechteck zeichnen
            pygame.draw.rect(screen, TEMPLATE_COLOR_2, touch_control_1_rect)
            pygame.draw.rect(screen, BLACK, touch_control_1_rect, 2)
            # Text hinzufügen?
            if button_font:
                 touch_text = button_font.render("Touch", True, BLACK)
                 touch_rect = touch_text.get_rect(center=touch_control_1_rect.center)
                 screen.blit(touch_text, touch_rect)


        # Zurück Button zeichnen (Bild oder Fallback)
        if back_button_rect:
            current_back_img = scaled_back_button_bg
            is_hovering = back_button_rect.collidepoint(mouse_pos)
            if is_hovering and use_back_button_images and scaled_back_button_hover:
                 current_back_img = scaled_back_button_hover
            elif not use_back_button_images: # Fallback Zeichnung
                 btn_color = DARK_GRAY if is_hovering else GRAY
                 pygame.draw.rect(screen, btn_color, back_button_rect)
                 pygame.draw.rect(screen, BLACK, back_button_rect, 2)

            if use_back_button_images and current_back_img:
                 screen.blit(current_back_img, back_button_rect.topleft)

            # Fallback Text für Zurück-Button (falls Bilder fehlen oder gewünscht)
            if not use_back_button_images and button_font:
                 back_text_surf = button_font.render("Zurück", True, BLACK)
                 back_text_rect = back_text_surf.get_rect(center=back_button_rect.center)
                 screen.blit(back_text_surf, back_text_rect)

        # --- Ende Zeichnen ---

        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print(f"INFO (Template): Minispiel-Schleife beendet. Spielzustand: {game_state}")

    # Gebe die finalen Werte zurück (passe an, was zurückgegeben werden soll)
    return current_resource1, current_resource2, current_score

# --- Ende der run_minigame_template Funktion ---


# --- Standalone Code (Zum Testen des Templates) ---
if __name__ == "__main__":
    print("INFO: pygame_minigame_template_v2.py wird eigenständig ausgeführt.")
    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
    except Exception: _sw = 800; _sh = 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Pygame Minispiel Template V2 (Standalone)")

    # Beispielwerte für Standalone
    start_res1_sa = 10
    start_res2_sa = 5
    start_score_sa = 0
    id1_sa = "Energie"
    id2_sa = "Material"

    print(f"\n--- Starte Standalone mit: Res1={start_res1_sa}, Res2={start_res2_sa}, Score={start_score_sa} ---\n")

    try:
        final_res1, final_res2, final_score = run_minigame_template(
            standalone_screen, start_res1_sa, start_res2_sa, start_score_sa, id1_sa, id2_sa
        )
        print(f"\n--- Standalone Beendet. Ergebnis: ---")
        print(f"  Verbleibende Ressource 1: {final_res1}")
        print(f"  Verbleibende Ressource 2: {final_res2}")
        print(f"  Finaler Punktestand: {final_score}")
        print("-------------------------------------\n")

    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---