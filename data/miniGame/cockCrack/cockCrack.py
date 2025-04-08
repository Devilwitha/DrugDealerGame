# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os
import traceback

# --- Konstanten und Farben ---
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)

# --- Hauptfunktion des Spiels ---
def run_zip_weed_game(screen_surface):
    screen = screen_surface
    actual_screen_size = screen.get_size()
    print(f"DEBUG (zipWeed): Nutze Screen-Größe: {actual_screen_size}")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0 # Referenz für Schriftgrößen-Skalierung

    # --- Mixer Initialisierung ---
    music_available = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (zipWeed): Pygame Mixer initialisiert.")
            try: pygame.mixer.music.get_volume(); music_available = True; print("DEBUG (zipWeed): Music Modul verfügbar.")
            except pygame.error: print("WARNUNG (zipWeed): Music Modul nicht verfügbar."); music_available = False
        except pygame.error as e: print(f"WARNUNG (zipWeed): Mixer konnte nicht initialisiert werden: {e}"); music_available = False
    else:
        print("DEBUG (zipWeed): Mixer war bereits initialisiert.")
        try: pygame.mixer.music.get_volume(); music_available = True; print("DEBUG (zipWeed): Music Modul ist verfügbar.")
        except pygame.error: music_available = False; print("WARNUNG (zipWeed): Music Modul nicht verfügbar.")

    # --- Android Immersive Mode ---
    is_android = False
    # ... (Code für Immersive Mode bleibt unverändert, hier gekürzt) ...
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method; print("DEBUG (zipWeed): Pyjnius importiert.")
        try: Build = autoclass('android.os.Build$VERSION'); sdk_int = Build.SDK_INT
        except Exception as e_build: print(f"FEHLER (zipWeed): Build laden fehlgeschlagen: {e_build}"); raise
        if sdk_int > 0: is_android = True; print(f"DEBUG (zipWeed): Android erkannt (SDK: {sdk_int}).")
        else: raise RuntimeError("Nicht Android")
        try: PythonActivity = autoclass('org.kivy.android.PythonActivity'); activity = PythonActivity.mActivity; assert activity is not None
        except Exception as e_activity: print(f"FEHLER (zipWeed): Activity holen fehlgeschlagen: {e_activity}"); raise
        try: View = autoclass('android.view.View'); Window = autoclass('android.view.Window'); WindowManager = autoclass('android.view.WindowManager$LayoutParams')
        except Exception as e_classes: print(f"FEHLER (zipWeed): View/Window Klassen laden fehlgeschlagen: {e_classes}"); raise
        try:
            flags = (View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)
            class SetUiVisibilityRunnablePJC(PythonJavaClass):
                    __javainterfaces__ = ['java/lang/Runnable']
                    def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
                    @java_method('()V')
                    def run(self):
                            try: w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f); w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                            except Exception as e: print(f"FEHLER (Runnable): {e}"); traceback.print_exc()
            runnable = SetUiVisibilityRunnablePJC(activity, flags)
            if activity: activity.runOnUiThread(runnable); print("DEBUG (zipWeed): Runnable Immersive gestartet.")
        except Exception as e_runnable: print(f"FEHLER (zipWeed): Runnable Setup fehlgeschlagen: {e_runnable}"); raise
    except Exception as e: print(f"FEHLER (zipWeed): Immersive Mode fehlgeschlagen: {e}"); is_android = False
    # --- Ende Immersive Mode ---


    # --- Proportionale Berechnungen ---
    if actual_screen_size[1] > actual_screen_size[0]: CALC_WIDTH=actual_screen_size[1]; CALC_HEIGHT=actual_screen_size[0]
    else: CALC_WIDTH=actual_screen_size[0]; CALC_HEIGHT=actual_screen_size[1]
    target_width = max(1, int(CALC_WIDTH * (150 / ref_w))); target_height = max(1, int(CALC_HEIGHT * (200 / ref_h)))
    target_padding_right = max(1, int(CALC_WIDTH * (50 / ref_w))); target_padding_bottom = max(1, int(CALC_HEIGHT * (100 / ref_h)))
    target_x = actual_screen_size[0] - target_width - target_padding_right; target_y = actual_screen_size[1] - target_height - target_padding_bottom
    target_rect = pygame.Rect(target_x, target_y, target_width, target_height)
    base_swipe_line_height = max(1, int(CALC_HEIGHT * (12 / ref_h)))
    if is_android: swipe_line_height = max(1, int(base_swipe_line_height * 6.0))
    else: swipe_line_height = base_swipe_line_height
    swipe_line_rect = None; min_swipe_distance = 100
    if target_rect: swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height); min_swipe_distance = swipe_line_rect.width * 0.85

    # --- Kreise statt Viereck ---
    NUM_CIRCLES = 4
    # Kleinere Größe für Kreise, damit 4 nebeneinander passen
    circle_diameter = max(10, int(CALC_WIDTH * (40 / ref_w)))
    circle_radius = circle_diameter // 2
    circle_spacing = max(2, int(CALC_WIDTH * (8 / ref_w))) # Abstand zwischen Kreisen
    total_circles_width = NUM_CIRCLES * circle_diameter + (NUM_CIRCLES - 1) * circle_spacing

    # Startposition anpassen, damit die Gruppe zentriert oder links beginnt
    start_padding_left = max(1, int(CALC_WIDTH * (50 / ref_w))) # Etwas weniger Padding links
    start_padding_top = max(1, int(CALC_HEIGHT * (400 / ref_h)))
    start_pos = [start_padding_left, start_padding_top]

    small_circles_rects = []
    for i in range(NUM_CIRCLES):
        circle_x = start_pos[0] + i * (circle_diameter + circle_spacing)
        circle_y = start_pos[1]
        small_circles_rects.append(pygame.Rect(circle_x, circle_y, circle_diameter, circle_diameter))

    gravity = max(1, int(CALC_HEIGHT * (6 / ref_h)))

    # Proportionale Schriftgröße für Score etc.
    BASE_GAME_FONT_SIZE = 36
    game_font_size = max(12, int(CALC_HEIGHT * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try: font = pygame.font.SysFont("arial", game_font_size)
    except pygame.error: font = pygame.font.Font(None, game_font_size) # Fallback
    if not font: print("WARNUNG: Konnte keine Spiel-Schriftart laden!"); font = pygame.font.Font(None, 30) # Absoluter Fallback

    score_pos_x = max(1, int(actual_screen_size[0] * (10 / ref_w))); score_pos_y = max(1, int(actual_screen_size[1] * (10 / ref_h)))

    # --- Pfad-Setup ---
    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    data_root_folder = os.path.join(script_dir_game, "..", "..") # Zwei Ebenen hoch
    image_folder = "bilder"; sound_folder = "sounds"

    # --- Bilder laden ---
    # Kein 'small_image' mehr nötig, wir zeichnen Kreise direkt
    target_image = None; use_target_image = False; target_image_filename = "grip.png"
    target_image_path = os.path.join(data_root_folder, image_folder, target_image_filename)
    try: original_target_image = pygame.image.load(target_image_path).convert_alpha()
    except Exception as e: print(f"WARNUNG: Laden '{target_image_path}' fehlgeschlagen: {e}")
    else:
        if target_rect and target_rect.width > 0 and target_rect.height > 0: target_image = pygame.transform.smoothscale(original_target_image, (target_rect.width, target_rect.height)); use_target_image = True

    # --- Sounds laden ---
    ready_sound = None; score_sound = None; swipe_sound_duration = 0.0
    sound_filename_ready = "weedInBag.wav"; sound_filename_score = "bagFinish.wav"; sound_filename_swipe = "closeBag.ogg"

    sound_path_ready = os.path.join(data_root_folder, sound_folder, sound_filename_ready)
    try:
        if pygame.mixer.get_init(): ready_sound = pygame.mixer.Sound(sound_path_ready); ready_sound.set_volume(0.7)
    except Exception as e: print(f"WARNUNG (zipWeed): Laden Ready-Sound fehlgeschlagen: {e}")

    sound_path_score = os.path.join(data_root_folder, sound_folder, sound_filename_score)
    try:
        if pygame.mixer.get_init(): score_sound = pygame.mixer.Sound(sound_path_score); score_sound.set_volume(0.9)
    except Exception as e: print(f"WARNUNG (zipWeed): Laden Score-Sound fehlgeschlagen: {e}")

    swipe_sound_path = os.path.join(data_root_folder, sound_folder, sound_filename_swipe)
    try:
        if music_available:
            temp_sound = pygame.mixer.Sound(swipe_sound_path); swipe_sound_duration = temp_sound.get_length(); del temp_sound
            pygame.mixer.music.load(swipe_sound_path); pygame.mixer.music.play(-1); pygame.mixer.music.pause(); pygame.mixer.music.set_volume(0.8)
        else: print("WARNUNG (zipWeed): Music Modul nicht verfügbar.")
    except Exception as e: print(f"WARNUNG (zipWeed): Laden Swipe-Musik fehlgeschlagen: {e}"); swipe_sound_duration = 0.0

    # --- Zurück-Button Definition (Proportional & Zentriert) ---
    BACK_BUTTON_WIDTH_PERCENT = 0.20 # 20% der Bildschirmbreite
    BACK_BUTTON_HEIGHT_PERCENT = 0.08 # 8% der Bildschirmhöhe
    BASE_BACK_FONT_SIZE = 24

    back_button_width = int(actual_screen_size[0] * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(actual_screen_size[1] * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_x = (actual_screen_size[0] - back_button_width) // 2
    back_button_y = 20 # Fester Abstand von oben
    back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)

    back_button_font_size = max(16, int(actual_screen_size[1] * (BASE_BACK_FONT_SIZE / FONT_SIZE_REF_H)))
    back_button_font = None
    back_text_surface = None
    try:
        back_button_font = pygame.font.SysFont("arial", back_button_font_size)
        back_text_surface = back_button_font.render("Zurück", True, BLACK)
    except Exception as e_backfont:
        print(f"WARNUNG: Konnte Font für Zurück-Button nicht laden: {e_backfont}")
        try: # Fallback Font
            back_button_font = pygame.font.Font(None, int(back_button_font_size*1.1))
            back_text_surface = back_button_font.render("Zurück", True, BLACK)
        except Exception: pass # Ignoriere, wenn auch Fallback fehlschlägt


    # Spielzustands-Variablen
    dragging, is_falling, offset_x, offset_y, score = False, False, 0, 0, 0
    # dragging_circle_index = -1 # Welcher Kreis wird gedraggt? (-1 = keiner) -> Geändert: Ganze Gruppe wird bewegt
    ready_for_swipe, is_swiping, swipe_start_x, swipe_current_x = False, False, None, None
    swipe_min_x, swipe_max_x = None, None
    display_persistent_swipe_bar = False; persistent_bar_rect = None
    resumed_swipe_initial_width = 0; was_ready_for_swipe = False; was_swiping = False
    clock = pygame.time.Clock()

    # --- Spiel-Loop ---
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False; pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button_rect and back_button_rect.collidepoint(event.pos): running = False; continue
                    if ready_for_swipe and swipe_line_rect and swipe_line_rect.collidepoint(event.pos):
                        is_swiping = True; current_click_x = event.pos[0]; swipe_current_x = current_click_x; swipe_start_x = current_click_x
                        if display_persistent_swipe_bar and persistent_bar_rect is not None: swipe_min_x = min(persistent_bar_rect.left, current_click_x); swipe_max_x = max(persistent_bar_rect.right, current_click_x); resumed_swipe_initial_width = persistent_bar_rect.width; display_persistent_swipe_bar = False; persistent_bar_rect = None
                        else: swipe_min_x = current_click_x; swipe_max_x = current_click_x; resumed_swipe_initial_width = 0
                        dragging = False
                    # Prüfen, ob einer der Kreise geklickt wurde
                    elif not is_swiping:
                        clicked_on_circle = False
                        for i, circle_rect in enumerate(small_circles_rects):
                            if circle_rect.collidepoint(event.pos):
                                dragging = True
                                is_falling = False
                                ready_for_swipe = False
                                is_swiping = False
                                swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None
                                display_persistent_swipe_bar = False
                                persistent_bar_rect = None
                                resumed_swipe_initial_width = 0
                                # Offset relativ zum ersten Kreis berechnen, um die Gruppe zu bewegen
                                offset_x = small_circles_rects[0].x - event.pos[0]
                                offset_y = small_circles_rects[0].y - event.pos[1]
                                clicked_on_circle = True
                                break # Nur einen Kreis auf einmal greifen (bewegt die ganze Gruppe)
                        # if not clicked_on_circle: # Wenn außerhalb geklickt wurde
                             # Optional: Verhalten definieren, wenn neben die Kreise geklickt wird
                             # pass

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if is_swiping:
                        is_swiping = False; final_width = 0; final_rect = None
                        if swipe_line_rect and swipe_min_x is not None and swipe_max_x is not None:
                                clamped_orange_x=max(swipe_line_rect.left, swipe_min_x); clamped_orange_right=min(swipe_line_rect.right, swipe_max_x); final_width=max(0, clamped_orange_right - clamped_orange_x)
                                if final_width > 0: final_rect = pygame.Rect(clamped_orange_x, swipe_line_rect.y, final_width, swipe_line_rect.height)
                        if final_rect: persistent_bar_rect = final_rect; display_persistent_swipe_bar = True
                        swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None; resumed_swipe_initial_width = 0
                        # Prüfen ob nach Swipe noch alle Kreise im Ziel sind
                        all_inside_after_swipe = target_rect and all(target_rect.contains(cr) for cr in small_circles_rects)
                        if all_inside_after_swipe:
                             ready_for_swipe = True; is_falling = False
                        else:
                             ready_for_swipe = False; is_falling = True
                    elif dragging:
                        dragging = False
                        # Prüfen ob *alle* Kreise im Ziel sind
                        all_inside = target_rect and all(target_rect.contains(cr) for cr in small_circles_rects)
                        if all_inside:
                            ready_for_swipe = True
                            is_falling = False
                            # Ready-Sound hier direkt spielen, da der Zustand gesetzt wird
                            if ready_sound and not was_ready_for_swipe:
                                ready_sound.play()
                                was_ready_for_swipe = True
                        else:
                            ready_for_swipe = False
                            is_falling = True
                            if was_ready_for_swipe:
                                was_ready_for_swipe = False # Zurücksetzen, wenn nicht mehr bereit


            elif event.type == pygame.MOUSEMOTION:
                if is_swiping:
                    swipe_current_x = event.pos[0]
                    if swipe_min_x is not None and swipe_max_x is not None: swipe_min_x = min(swipe_min_x, swipe_current_x); swipe_max_x = max(swipe_max_x, swipe_current_x)
                    if swipe_start_x is not None and swipe_line_rect:
                        current_added_distance = abs(swipe_current_x - swipe_start_x); total_effective_distance = resumed_swipe_initial_width + current_added_distance
                        if total_effective_distance >= min_swipe_distance:
                            score += 1
                            if score_sound: score_sound.play()
                            # Kreise zurücksetzen
                            for i in range(NUM_CIRCLES):
                                circle_x = start_pos[0] + i * (circle_diameter + circle_spacing)
                                circle_y = start_pos[1]
                                small_circles_rects[i].topleft = (circle_x, circle_y)

                            ready_for_swipe=False; is_falling=False; is_swiping=False; dragging=False; display_persistent_swipe_bar=False; persistent_bar_rect=None; resumed_swipe_initial_width = 0
                            swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None
                            was_ready_for_swipe = False # Nach Score nicht mehr bereit
                elif dragging:
                    # Berechne neue Position für den ersten Kreis
                    potential_x = event.pos[0] + offset_x
                    potential_y = event.pos[1] + offset_y

                    # Berechne die Verschiebung (delta)
                    dx = potential_x - small_circles_rects[0].x
                    dy = potential_y - small_circles_rects[0].y

                    # Temporäre neue Positionen für Kollisionsprüfung
                    potential_rects = [r.move(dx, dy) for r in small_circles_rects]

                    # Screen-Grenzen prüfen für die *gesamte* Gruppe
                    screen_rect = pygame.Rect(0, 0, actual_screen_size[0], actual_screen_size[1])
                    group_rect_potential = potential_rects[0].unionall(potential_rects[1:]) # Bounding Box der Gruppe

                    can_move_x = True
                    can_move_y = True

                    if group_rect_potential.left < 0:
                        dx = -small_circles_rects[0].left # Verschiebung, um links an 0 zu stoppen
                    elif group_rect_potential.right > actual_screen_size[0]:
                        dx = actual_screen_size[0] - small_circles_rects[-1].right # Verschiebung, um rechts am Rand zu stoppen

                    if group_rect_potential.top < 0:
                        dy = -small_circles_rects[0].top # Verschiebung, um oben an 0 zu stoppen
                    elif group_rect_potential.bottom > actual_screen_size[1]:
                        dy = actual_screen_size[1] - small_circles_rects[0].bottom # Verschiebung, um unten am Rand zu stoppen


                    # Bewege alle Kreise um das (ggf. korrigierte) delta
                    for r in small_circles_rects:
                        r.move_ip(dx, dy)


        # --- Spiel-Logik / Physik (Fallen) ---
        if is_falling and not dragging and not ready_for_swipe and not is_swiping:
            # Wende Gravitation auf alle Kreise an (gleiche y-Bewegung)
            potential_y = small_circles_rects[0].y + gravity
            potential_bottom = potential_y + circle_diameter
            screen_height = actual_screen_size[1]

            # Kollision mit Bildschirmboden prüfen (für den ersten Kreis genügt, da alle gleiche Y haben)
            if potential_bottom >= screen_height:
                 dy = screen_height - small_circles_rects[0].bottom # Korrektur, um genau am Boden zu stoppen
                 for r in small_circles_rects:
                     r.move_ip(0, dy)
                 is_falling = False
                 ready_for_swipe = False # Am Boden nicht bereit für Swipe
            else:
                 # Alle Kreise nach unten bewegen
                 for r in small_circles_rects:
                    r.move_ip(0, gravity)

        # --- Zustandskorrektur ---
        # Wenn ready_for_swipe, aber nicht mehr alle Kreise im Ziel sind (z.B. durch externe Faktoren?)
        # und nicht gerade gezogen wird -> fallen lassen
        if ready_for_swipe and not is_swiping and not dragging:
             all_inside_check = target_rect and all(target_rect.contains(cr) for cr in small_circles_rects)
             if not all_inside_check:
                 ready_for_swipe = False
                 is_falling = True
                 if was_ready_for_swipe:
                     was_ready_for_swipe = False # Sound-Trigger zurücksetzen


        # --- Sound-Trigger (Ready Sound) ---
        # Wird jetzt in MOUSEBUTTONUP behandelt, wenn die Kreise platziert werden.
        # Hier nur das Zurücksetzen, falls der Zustand anderweitig verloren geht.
        if not ready_for_swipe and was_ready_for_swipe:
             was_ready_for_swipe = False


        # --- Swipe-Musik-Logik ---
        current_swipe_percentage = 0.0
        if is_swiping and swipe_line_rect and swipe_min_x is not None and swipe_max_x is not None:
            clamped_orange_x = max(swipe_line_rect.left, swipe_min_x); clamped_orange_right = min(swipe_line_rect.right, swipe_max_x); clamped_orange_width = max(0, clamped_orange_right - clamped_orange_x)
            if swipe_line_rect.width > 0: current_swipe_percentage = clamped_orange_width / swipe_line_rect.width
        if music_available and swipe_sound_duration > 0:
            if is_swiping:
                if not was_swiping: pygame.mixer.music.unpause(); was_swiping = True
                target_time = current_swipe_percentage * swipe_sound_duration
                try: pygame.mixer.music.set_pos(target_time)
                except pygame.error as e_setpos: print(f"WARNUNG: set_pos fehlgeschlagen: {e_setpos}")
            else:
                if was_swiping: pygame.mixer.music.pause(); was_swiping = False

        # --- Zeichnen ---
        screen.fill(WHITE)
        # Ziel
        if target_rect:
            if use_target_image and target_image is not None: screen.blit(target_image, target_rect.topleft)
            else: pygame.draw.rect(screen, BLUE, target_rect)
        # Swipe-Linie / Fortschritt
        if ready_for_swipe and swipe_line_rect:
            pygame.draw.rect(screen, GREEN, swipe_line_rect)
            bar_to_draw = None
            if is_swiping and swipe_min_x is not None and swipe_max_x is not None:
                clamped_orange_x_draw = max(swipe_line_rect.left, swipe_min_x); clamped_orange_right_draw = min(swipe_line_rect.right, swipe_max_x); clamped_orange_width_draw = max(0, clamped_orange_right_draw - clamped_orange_x_draw)
                if clamped_orange_width_draw > 0: bar_to_draw = pygame.Rect(clamped_orange_x_draw, swipe_line_rect.y, clamped_orange_width_draw, swipe_line_rect.height)
            elif display_persistent_swipe_bar and persistent_bar_rect is not None: bar_to_draw = persistent_bar_rect
            if bar_to_draw: pygame.draw.rect(screen, ORANGE, bar_to_draw)
        # else: display_persistent_swipe_bar = False; persistent_bar_rect = None; resumed_swipe_initial_width = 0 # Wird jetzt beim Setzen von ready_for_swipe=False behandelt

        # Kreise zeichnen
        for circle_rect in small_circles_rects:
             # pygame.draw.rect(screen, RED, circle_rect) # DEBUG: Zeige Rects
             pygame.draw.circle(screen, RED, circle_rect.center, circle_radius)

        # Score
        if font: score_text = font.render(f"Punkte: {score}", True, BLACK); screen.blit(score_text, (score_pos_x, score_pos_y))
        # Zurück-Button
        if back_button_rect: # Zeichne Zurück-Button
             # Hover-Effekt
             back_button_color = GRAY
             if back_button_rect.collidepoint(pygame.mouse.get_pos()):
                 back_button_color = DARK_GRAY
             pygame.draw.rect(screen, back_button_color, back_button_rect)
             pygame.draw.rect(screen, BLACK, back_button_rect, 2) # Rand etwas dünner
             if back_text_surface and back_button_font: # Nur zeichnen, wenn Font+Surface existieren
                 # Text zentrieren
                 back_text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                 screen.blit(back_text_surface, back_text_rect.topleft)

        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print("INFO (zipWeed): Minispiel-Schleife beendet.")
    if music_available:
        try: pygame.mixer.music.stop(); print("DEBUG (zipWeed): Swipe-Musik gestoppt.")
        except pygame.error as e_stop: print(f"WARNUNG (zipWeed): Fehler beim Stoppen der Musik: {e_stop}")

# --- Ende der run_zip_weed_game Funktion ---


# --- Code für Standalone-Ausführung ---
if __name__ == "__main__":
    print("INFO: zipWeed.py wird eigenständig ausgeführt.")
    pygame.init()
    try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
    except Exception: _sw = 800; _sh = 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE) # Resizable hinzugefügt für Tests
    pygame.display.set_caption("ZipWeed Minispiel (Standalone)")
    try:
        run_zip_weed_game(standalone_screen) # Rufe die Funktion auf
    except Exception as e_main: print(f"FEHLER in Standalone: {e_main}"); traceback.print_exc()
    finally: pygame.quit(); sys.exit()
# --- Ende Standalone-Code ---