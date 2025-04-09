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
# NEU: Akzeptiert Startwerte und Sorte
def run_zip_weed_game(screen_surface, initial_weed, initial_grips, sorte_name):
    screen = screen_surface
    actual_screen_size = screen.get_size()
    print(f"DEBUG (zipWeed): Nutze Screen-Größe: {actual_screen_size}")
    print(f"DEBUG (zipWeed): Startwerte erhalten: Weed={initial_weed}, Grips={initial_grips}, Sorte='{sorte_name}'")

    # NEU: Spielzustands-Variablen basierend auf Inputs
    current_weed = initial_weed
    current_grips = initial_grips
    packed_weed = 0 # Startet bei 0

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
    target_rect = pygame.Rect(target_x, target_y, target_width, target_height) # Grip Area
    base_swipe_line_height = max(1, int(CALC_HEIGHT * (12 / ref_h)))
    if is_android: swipe_line_height = max(1, int(base_swipe_line_height * 6.0))
    else: swipe_line_height = base_swipe_line_height
    swipe_line_rect = None; min_swipe_distance = 100
    if target_rect: swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height); min_swipe_distance = swipe_line_rect.width * 0.85
    small_size = max(1, int(CALC_WIDTH * (80 / ref_w))) # Weed Item size
    start_padding_left = max(1, int(CALC_WIDTH * (100 / ref_w))); start_padding_top = max(1, int(CALC_HEIGHT * (400 / ref_h)))
    start_pos = [start_padding_left, start_padding_top]; small_rect = pygame.Rect(start_pos[0], start_pos[1], small_size, small_size) # Weed Item Rect
    gravity = max(1, int(CALC_HEIGHT * (6 / ref_h)))

    # Proportionale Schriftgröße für Statusanzeige
    BASE_GAME_FONT_SIZE = 30 # Etwas kleiner, da mehr Text
    game_font_size = max(12, int(CALC_HEIGHT * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try: font = pygame.font.SysFont("arial", game_font_size)
    except pygame.error: font = pygame.font.Font(None, game_font_size) # Fallback
    if not font: print("WARNUNG: Konnte keine Spiel-Schriftart laden!"); font = pygame.font.Font(None, 30) # Absoluter Fallback

    status_pos_x = max(5, int(actual_screen_size[0] * (10 / ref_w)));
    status_pos_y = max(5, int(actual_screen_size[1] * (60 / ref_h))) # Weiter unten wegen Zurück-Button

    # --- Pfad-Setup ---
    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    data_root_folder = os.path.join(script_dir_game, "..", "..") # Zwei Ebenen hoch
    image_folder = "bilder"; sound_folder = "sounds"

    # --- Bilder laden ---
    # NEU: Lade Weed-Bild basierend auf Sorte
    small_image = None; use_small_image = False
    # Passe den Dateinamen an deine Konvention an!
    # Beispiel: Wenn sorte_name="Normal", wird "weed_normal.png" gesucht.
    small_image_filename = f"weed_{sorte_name.lower()}.png"
    print(f"DEBUG (zipWeed): Versuche Weed-Bild zu laden: '{small_image_filename}'")
    small_image_path = os.path.join(data_root_folder, image_folder, small_image_filename)
    try:
        original_small_image = pygame.image.load(small_image_path).convert_alpha()
        if small_size > 0:
            small_image = pygame.transform.smoothscale(original_small_image, (small_size, small_size))
            use_small_image = True
            print(f"DEBUG (zipWeed): Bild '{small_image_filename}' erfolgreich geladen und skaliert.")
    except Exception as e:
        print(f"WARNUNG: Laden von '{small_image_path}' fehlgeschlagen: {e}. Nutze rotes Viereck als Fallback.")
        use_small_image = False # Fallback

    # Bild für Grip-Zone (Ziel)
    target_image = None; use_target_image = False; target_image_filename = "grip.png" # Annahme: Grip-Bild ist immer gleich
    target_image_path = os.path.join(data_root_folder, image_folder, target_image_filename)
    try:
        original_target_image = pygame.image.load(target_image_path).convert_alpha()
        if target_rect and target_rect.width > 0 and target_rect.height > 0:
            target_image = pygame.transform.smoothscale(original_target_image, (target_rect.width, target_rect.height))
            use_target_image = True
    except Exception as e: print(f"WARNUNG: Laden '{target_image_path}' fehlgeschlagen: {e}. Nutze blaues Viereck.")

    # --- Sounds laden ---
    ready_sound = None; score_sound = None; swipe_sound_duration = 0.0; no_resource_sound = None # Optional: Sound für Fehler
    sound_filename_ready = "weedInBag.wav"; sound_filename_score = "bagFinish.wav"; sound_filename_swipe = "closeBag.ogg"
    sound_filename_no_resource = "error.wav" # Optional: Dateiname für Fehler-Sound

    sound_path_ready = os.path.join(data_root_folder, sound_folder, sound_filename_ready)
    try:
        if pygame.mixer.get_init(): ready_sound = pygame.mixer.Sound(sound_path_ready); ready_sound.set_volume(0.7)
    except Exception as e: print(f"WARNUNG (zipWeed): Laden Ready-Sound fehlgeschlagen: {e}")

    sound_path_score = os.path.join(data_root_folder, sound_folder, sound_filename_score)
    try:
        if pygame.mixer.get_init(): score_sound = pygame.mixer.Sound(sound_path_score); score_sound.set_volume(0.9)
    except Exception as e: print(f"WARNUNG (zipWeed): Laden Score-Sound fehlgeschlagen: {e}")

    # Optional: Fehler-Sound laden
    sound_path_no_resource = os.path.join(data_root_folder, sound_folder, sound_filename_no_resource)
    try:
        if pygame.mixer.get_init(): no_resource_sound = pygame.mixer.Sound(sound_path_no_resource); no_resource_sound.set_volume(0.6)
    except Exception as e: print(f"WARNUNG (zipWeed): Laden No-Resource-Sound fehlgeschlagen: {e}")


    swipe_sound_path = os.path.join(data_root_folder, sound_folder, sound_filename_swipe)
    try:
        if music_available:
            temp_sound = pygame.mixer.Sound(swipe_sound_path); swipe_sound_duration = temp_sound.get_length(); del temp_sound
            pygame.mixer.music.load(swipe_sound_path); pygame.mixer.music.play(-1); pygame.mixer.music.pause(); pygame.mixer.music.set_volume(0.8)
        else: print("WARNUNG (zipWeed): Music Modul nicht verfügbar.")
    except Exception as e: print(f"WARNUNG (zipWeed): Laden Swipe-Musik fehlgeschlagen: {e}"); swipe_sound_duration = 0.0

    # --- Zurück-Button Definition (Proportional & Zentriert oben) ---
    BACK_BUTTON_WIDTH_PERCENT = 0.20 # 20% der Bildschirmbreite
    BACK_BUTTON_HEIGHT_PERCENT = 0.08 # 8% der Bildschirmhöhe
    BASE_BACK_FONT_SIZE = 24

    back_button_width = int(actual_screen_size[0] * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(actual_screen_size[1] * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_x = (actual_screen_size[0] - back_button_width) // 2
    back_button_y = 10 # Kleiner Abstand von oben
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


    # Spielzustands-Variablen (Interaktion)
    dragging, is_falling, offset_x, offset_y = False, False, 0, 0 # Score wird durch packed_weed ersetzt
    ready_for_swipe, is_swiping, swipe_start_x, swipe_current_x = False, False, None, None
    swipe_min_x, swipe_max_x = None, None
    display_persistent_swipe_bar = False; persistent_bar_rect = None
    resumed_swipe_initial_width = 0; was_ready_for_swipe = False; was_swiping = False
    clock = pygame.time.Clock()

    # --- Spiel-Loop ---
    running = True
    while running:
        # --- Event Handling ---
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False; pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Prüfen ob Zurück-Button geklickt
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False;
                        continue # Restliche Klick-Logik überspringen

                    # Prüfen ob Swipe gestartet werden kann/soll
                    # NEU: Prüfe auch, ob Grips und Weed vorhanden sind
                    if current_grips >= 1 and current_weed >= 1 and ready_for_swipe and swipe_line_rect and swipe_line_rect.collidepoint(event.pos):
                        is_swiping = True; current_click_x = event.pos[0]; swipe_current_x = current_click_x; swipe_start_x = current_click_x
                        if display_persistent_swipe_bar and persistent_bar_rect is not None: swipe_min_x = min(persistent_bar_rect.left, current_click_x); swipe_max_x = max(persistent_bar_rect.right, current_click_x); resumed_swipe_initial_width = persistent_bar_rect.width; display_persistent_swipe_bar = False; persistent_bar_rect = None
                        else: swipe_min_x = current_click_x; swipe_max_x = current_click_x; resumed_swipe_initial_width = 0
                        dragging = False # Sicherstellen, dass nicht gleichzeitig gezogen wird

                    # Prüfen ob Weed-Objekt gezogen werden kann/soll
                    # NEU: Prüfe auch, ob Weed vorhanden ist
                    elif current_weed >= 1 and small_rect and small_rect.collidepoint(event.pos) and not is_swiping:
                        dragging = True; is_falling = False; ready_for_swipe = False; is_swiping = False
                        swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None; display_persistent_swipe_bar = False; persistent_bar_rect = None; resumed_swipe_initial_width = 0
                        offset_x = small_rect.x - event.pos[0]; offset_y = small_rect.y - event.pos[1]

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if is_swiping:
                        is_swiping = False; final_width = 0; final_rect = None
                        # Persistenten Balken nur speichern, wenn Grips noch da sind
                        if current_grips >= 1 and swipe_line_rect and swipe_min_x is not None and swipe_max_x is not None:
                            clamped_orange_x=max(swipe_line_rect.left, swipe_min_x); clamped_orange_right=min(swipe_line_rect.right, swipe_max_x); final_width=max(0, clamped_orange_right - clamped_orange_x)
                            if final_width > 0: final_rect = pygame.Rect(clamped_orange_x, swipe_line_rect.y, final_width, swipe_line_rect.height)
                        if final_rect: persistent_bar_rect = final_rect; display_persistent_swipe_bar = True
                        else: display_persistent_swipe_bar = False; persistent_bar_rect = None # Kein Balken, wenn 0 Breite
                        swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None; resumed_swipe_initial_width = 0

                        # Prüfen, ob nach Loslassen bereit für neuen Swipe (oder Fallen)
                        if target_rect and small_rect and not target_rect.contains(small_rect):
                            ready_for_swipe = False; is_falling = True # Fallen lassen, wenn außerhalb
                        elif target_rect and small_rect:
                            # NEU: Nur bereit, wenn Ressourcen vorhanden
                            if current_weed >= 1 and current_grips >= 1: ready_for_swipe = True
                            else: ready_for_swipe = False
                            is_falling = False

                    elif dragging:
                        dragging = False
                        # Prüfen, ob im Zielbereich gelandet
                        if target_rect and small_rect and target_rect.contains(small_rect):
                             # NEU: Nur bereit, wenn Ressourcen vorhanden
                            if current_weed >= 1 and current_grips >= 1: ready_for_swipe = True
                            else: ready_for_swipe = False
                            is_falling = False
                            if ready_sound and ready_for_swipe: ready_sound.play() # Hier Sound spielen, da gerade reingelegt
                        elif target_rect and small_rect:
                            ready_for_swipe = False; is_falling = True # Fallen lassen, wenn außerhalb

            elif event.type == pygame.MOUSEMOTION:
                if is_swiping:
                    swipe_current_x = event.pos[0]
                    if swipe_min_x is not None and swipe_max_x is not None: swipe_min_x = min(swipe_min_x, swipe_current_x); swipe_max_x = max(swipe_max_x, swipe_current_x)
                    if swipe_start_x is not None and swipe_line_rect:
                        current_added_distance = abs(swipe_current_x - swipe_start_x); total_effective_distance = resumed_swipe_initial_width + current_added_distance

                        # NEU: Logik für Punktevergabe und Ressourcen-Update
                        if total_effective_distance >= min_swipe_distance:
                            if current_weed >= 1 and current_grips >= 1: # Nur punkten, wenn Ressourcen da sind
                                packed_weed += 1
                                current_weed -= 1
                                current_grips -= 1
                                print(f"DEBUG: Punkt erzielt! Weed: {current_weed}, Grips: {current_grips}, Packed: {packed_weed}")
                                if score_sound: score_sound.play()

                                # Objekt zurücksetzen, nur wenn noch Weed vorhanden ist
                                if current_weed >= 1 and small_rect:
                                    small_rect.topleft = tuple(start_pos)
                                else:
                                    # Optional: Was tun, wenn kein Weed mehr da ist?
                                    # small_rect könnte None werden oder unsichtbar bleiben
                                    print("INFO: Kein Weed mehr zum Zurücksetzen.")
                                    # Stellen sicher, dass nicht gezogen werden kann etc.
                                    dragging = False

                                # Swipe-Status zurücksetzen
                                ready_for_swipe=False; is_falling=False; is_swiping=False; display_persistent_swipe_bar=False; persistent_bar_rect=None; resumed_swipe_initial_width = 0
                                swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None
                            else:
                                # Keine Ressourcen mehr, Swipe abbrechen
                                print("DEBUG: Swipe-Ziel erreicht, aber keine Ressourcen (Weed oder Grips).")
                                if no_resource_sound: no_resource_sound.play() # Optional: Fehler-Sound
                                # Nur Swipe-Status zurücksetzen, keine Punkte/Ressourcen ändern
                                is_swiping=False; display_persistent_swipe_bar=False; persistent_bar_rect=None; resumed_swipe_initial_width = 0
                                swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None
                                # Prüfen ob das Objekt fallen soll oder im Ziel ist
                                if target_rect and small_rect and target_rect.contains(small_rect):
                                    ready_for_swipe = False # Kann nicht mehr swipen
                                    is_falling = False
                                else:
                                     ready_for_swipe = False
                                     is_falling = True


                elif dragging and small_rect and current_weed >= 1: # Nur ziehen, wenn Weed vorhanden
                    old_rect = small_rect.copy(); potential_x = event.pos[0] + offset_x; potential_y = event.pos[1] + offset_y; small_rect.topleft = (potential_x, potential_y)

                    # Kollisionsprüfung mit Ziel (nur wenn Grips vorhanden)
                    if current_grips >= 1 and target_rect and not target_rect.contains(old_rect) and small_rect.colliderect(target_rect):
                        # Einfache Kollisionsbehandlung (verhindert Eindringen)
                        if old_rect.right <= target_rect.left and small_rect.right > target_rect.left: small_rect.right = target_rect.left
                        elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right: small_rect.left = target_rect.right
                        elif old_rect.bottom <= target_rect.top and small_rect.bottom > target_rect.top: small_rect.bottom = target_rect.top
                        elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom: small_rect.top = target_rect.bottom

                    # Innerhalb Bildschirmgrenzen halten
                    screen_rect = pygame.Rect(0, 0, actual_screen_size[0], actual_screen_size[1]); small_rect.clamp_ip(screen_rect)

        # --- Spiel-Logik / Physik (Fallen) ---
        if small_rect and is_falling and not dragging and not ready_for_swipe and not is_swiping:
            potential_y = small_rect.y + gravity; potential_rect = small_rect.copy(); potential_rect.y = potential_y; screen_height = actual_screen_size[1]

            collides_with_target_bottom = False
            # Kollision mit Zielunterkante nur prüfen, wenn Grips vorhanden
            if current_grips >= 1 and target_rect:
                collides_with_target_bottom = (potential_rect.bottom > target_rect.bottom and small_rect.bottom <= target_rect.bottom and potential_rect.right > target_rect.left and potential_rect.left < target_rect.right)

            if collides_with_target_bottom:
                small_rect.bottom = target_rect.bottom; is_falling = False
                 # NEU: Prüfen ob bereit und Ressourcen vorhanden
                if target_rect.contains(small_rect) and current_weed >= 1 and current_grips >= 1:
                    ready_for_swipe = True
                    if ready_sound and not was_ready_for_swipe: ready_sound.play() # Sound hier, da gelandet
                else: ready_for_swipe = False
            else:
                if potential_rect.bottom >= screen_height:
                    small_rect.bottom = screen_height; is_falling = False; ready_for_swipe = False
                else: small_rect.y = potential_y

        # --- Zustandskorrektur ---
        # Wenn bereit zum swipen, aber Objekt nicht mehr im Ziel -> fallen lassen
        if ready_for_swipe and not is_swiping and target_rect and small_rect and not target_rect.contains(small_rect):
            if not dragging: ready_for_swipe = False; is_falling = True

        # --- Sound-Trigger (Ready Sound - hauptsächlich beim Reinlegen oben behandelt) ---
        if ready_sound:
             if ready_for_swipe and not was_ready_for_swipe:
                  # Sound wird jetzt meist in MOUSEBUTTONUP oder Fall-Logik gespielt
                  # ready_sound.play() # Ggf. doppelt, kann hier weg
                  was_ready_for_swipe = True
             elif not ready_for_swipe and was_ready_for_swipe:
                  was_ready_for_swipe = False


        # --- Swipe-Musik-Logik ---
        current_swipe_percentage = 0.0
        # Nur berechnen, wenn Grips da sind und geswiped wird
        if current_grips >= 1 and is_swiping and swipe_line_rect and swipe_min_x is not None and swipe_max_x is not None:
            clamped_orange_x = max(swipe_line_rect.left, swipe_min_x); clamped_orange_right = min(swipe_line_rect.right, swipe_max_x); clamped_orange_width = max(0, clamped_orange_right - clamped_orange_x)
            if swipe_line_rect.width > 0: current_swipe_percentage = clamped_orange_width / swipe_line_rect.width

        if music_available and swipe_sound_duration > 0:
            if is_swiping and current_grips >= 1: # Nur abspielen wenn Grips da
                if not was_swiping: pygame.mixer.music.unpause(); was_swiping = True
                target_time = current_swipe_percentage * swipe_sound_duration
                try: pygame.mixer.music.set_pos(target_time)
                except pygame.error as e_setpos: print(f"WARNUNG: set_pos fehlgeschlagen: {e_setpos}")
            else:
                if was_swiping: pygame.mixer.music.pause(); was_swiping = False


        # --- Zeichnen ---
        screen.fill(WHITE)

        # Ziel (Grip-Zone) - NEU: Nur zeichnen, wenn Grips vorhanden
        if current_grips >= 1 and target_rect:
            if use_target_image and target_image is not None:
                screen.blit(target_image, target_rect.topleft)
            else:
                pygame.draw.rect(screen, BLUE, target_rect)

        # Swipe-Linie / Fortschritt - NEU: Nur wenn Grips da & bereit
        if current_grips >= 1 and ready_for_swipe and swipe_line_rect:
            pygame.draw.rect(screen, GREEN, swipe_line_rect)
            bar_to_draw = None
            if is_swiping and swipe_min_x is not None and swipe_max_x is not None:
                clamped_orange_x_draw = max(swipe_line_rect.left, swipe_min_x); clamped_orange_right_draw = min(swipe_line_rect.right, swipe_max_x); clamped_orange_width_draw = max(0, clamped_orange_right_draw - clamped_orange_x_draw)
                if clamped_orange_width_draw > 0: bar_to_draw = pygame.Rect(clamped_orange_x_draw, swipe_line_rect.y, clamped_orange_width_draw, swipe_line_rect.height)
            elif display_persistent_swipe_bar and persistent_bar_rect is not None: bar_to_draw = persistent_bar_rect
            if bar_to_draw: pygame.draw.rect(screen, ORANGE, bar_to_draw)
        else:
            # Sicherstellen, dass kein alter Balken gezeichnet wird, wenn nicht bereit/keine Grips
             display_persistent_swipe_bar = False; persistent_bar_rect = None; resumed_swipe_initial_width = 0

        # Viereck (Weed-Objekt) - NEU: Nur zeichnen, wenn Weed vorhanden
        if current_weed >= 1 and small_rect:
            if use_small_image and small_image is not None:
                screen.blit(small_image, small_rect.topleft)
            else:
                pygame.draw.rect(screen, RED, small_rect)

        # Statusanzeige (Weed, Grips, Packed)
        if font:
            weed_text = font.render(f"Weed: {current_weed}", True, RED)
            grips_text = font.render(f"Grips: {current_grips}", True, BLUE)
            packed_text = font.render(f"Verpackt: {packed_weed}", True, GREEN)
            # Positionieren (untereinander, links oben, unter dem Zurück-Button)
            line_height = game_font_size + 5 # Höhe einer Zeile + kleiner Abstand
            screen.blit(weed_text, (status_pos_x, status_pos_y))
            screen.blit(grips_text, (status_pos_x, status_pos_y + line_height))
            screen.blit(packed_text, (status_pos_x, status_pos_y + 2 * line_height))


        # Zurück-Button (immer sichtbar)
        if back_button_rect:
            back_button_color = GRAY
            if back_button_rect.collidepoint(mouse_pos):
                back_button_color = DARK_GRAY
            pygame.draw.rect(screen, back_button_color, back_button_rect)
            pygame.draw.rect(screen, BLACK, back_button_rect, 2)
            if back_text_surface and back_button_font:
                back_text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                screen.blit(back_text_surface, back_text_rect.topleft)

        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print("INFO (zipWeed): Minispiel-Schleife beendet.")
    if music_available:
        try: pygame.mixer.music.stop(); print("DEBUG (zipWeed): Swipe-Musik gestoppt.")
        except pygame.error as e_stop: print(f"WARNUNG (zipWeed): Fehler beim Stoppen der Musik: {e_stop}")

    # NEU: Gebe die finalen Werte zurück
    return current_weed, current_grips, packed_weed, sorte_name

# --- Ende der run_zip_weed_game Funktion ---


# --- Code für Standalone-Ausführung ---
if __name__ == "__main__":
    print("INFO: zipWeed.py wird eigenständig ausgeführt.")
    pygame.init()
    try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
    except Exception: _sw = 800; _sh = 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED)
    pygame.display.set_caption("ZipWeed Minispiel (Standalone)")
    try:
        # NEU: Rufe die Funktion mit Beispielwerten auf
        start_weed = 10
        start_grips = 8
        start_sorte = "Normal" # Wähle eine Sorte, für die du ein Bild hast (z.B. weed_normal.png)
        print(f"\n--- Starte Standalone mit: Weed={start_weed}, Grips={start_grips}, Sorte='{start_sorte}' ---\n")
        result = run_zip_weed_game(standalone_screen, start_weed, start_grips, start_sorte)
        # NEU: Gib das Ergebnis aus
        print(f"\n--- Standalone Beendet. Ergebnis: ---")
        print(f"  Verbleibendes Weed: {result[0]}")
        print(f"  Verbleibende Grips: {result[1]}")
        print(f"  Verpacktes Weed:   {result[2]}")
        print(f"  Sorte gespielt:    '{result[3]}'")
        print("-------------------------------------\n")

    except Exception as e_main: print(f"FEHLER in Standalone: {e_main}"); traceback.print_exc()
    finally: pygame.quit(); sys.exit()
# --- Ende Standalone-Code ---