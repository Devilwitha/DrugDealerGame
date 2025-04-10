# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os
import traceback
import json # Importieren für das Laden der Einstellungen im Standalone-Modus

# --- Konstanten und Farben ---
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)

# --- Standardeinstellungen (für Standalone Fallback) ---
DEFAULT_SETTINGS = {
    "music_volume": 0.7,
    "sfx_volume": 0.8,
    "master_volume": 1.0
}

# --- Hilfsfunktion zum Laden der Einstellungen (wird nur für Standalone benötigt) ---
#     Wenn als Modul genutzt, werden die Einstellungen übergeben.
def load_standalone_settings(filepath):
    settings = DEFAULT_SETTINGS.copy() # Start mit Defaults
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                loaded_data = json.load(f)
                # Überprüfe und übernehme gültige Werte
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key in loaded_data and isinstance(loaded_data[key], (int, float)):
                         # Clamping
                         settings[key] = max(0.0, min(1.0, float(loaded_data[key])))
                    # else: Lasse den Default-Wert, wenn Key fehlt oder ungültig
                print(f"INFO (zipWeed Standalone): Einstellungen geladen aus {filepath}: {settings}")
        else:
            print(f"INFO (zipWeed Standalone): Einstellungsdatei {filepath} nicht gefunden. Nutze Standardeinstellungen.")
    except json.JSONDecodeError:
        print(f"FEHLER (zipWeed Standalone): Einstellungsdatei {filepath} ist korrupt. Nutze Standardeinstellungen.")
    except Exception as e:
        print(f"FEHLER (zipWeed Standalone): Laden der Einstellungen fehlgeschlagen: {e}")
    return settings

# --- Hauptfunktion des Spiels (NEUE SIGNATUR mit `game_settings`) ---
def run_zip_weed_game(screen_surface, initial_weed, initial_grips, sorte_name, game_settings):
    """
    Führt das ZipWeed Minispiel aus.

    Args:
        screen_surface (pygame.Surface): Die Oberfläche, auf der gezeichnet wird.
        initial_weed (int): Anfangsmenge Weed.
        initial_grips (int): Anfangsmenge Grips.
        sorte_name (str): Der Name der Weed-Sorte (für Bildauswahl).
        game_settings (dict): Ein Dictionary mit den geladenen Spieleinstellungen
                                (z.B. {'music_volume': 0.7, 'sfx_volume': 0.8, ...}).
    """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    print(f"DEBUG (zipWeed): Nutze Screen-Größe: {actual_screen_size}")
    print(f"DEBUG (zipWeed): Startwerte erhalten: Weed={initial_weed}, Grips={initial_grips}, Sorte='{sorte_name}'")
    print(f"DEBUG (zipWeed): Übergebene Einstellungen: {game_settings}")

    # --- Einstellungen extrahieren (mit Fallback) ---
    # Verwende .get() mit einem Default, falls der Key fehlt (sollte nicht passieren, wenn vom Hauptmenü korrekt übergeben)
    sfx_volume = game_settings.get("sfx_volume", DEFAULT_SETTINGS["sfx_volume"])
    print(f"DEBUG (zipWeed): Soundeffekt-Lautstärke gesetzt auf: {sfx_volume:.2f}")
    # music_volume = game_settings.get("music_volume", DEFAULT_SETTINGS["music_volume"]) # Falls benötigt
    # master_volume = game_settings.get("master_volume", DEFAULT_SETTINGS["master_volume"]) # Falls benötigt

    # Spielzustands-Variablen basierend auf Inputs
    current_weed = initial_weed
    current_grips = initial_grips
    packed_weed = 0 # Startet bei 0

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0 # Referenz für Schriftgrößen-Skalierung

    # --- Mixer Initialisierung prüfen (wird normalerweise vom Hauptmenü gemacht) ---
    mixer_ok = bool(pygame.mixer.get_init()) # Prüfen ob Mixer läuft
    if not mixer_ok:
         print("WARNUNG (zipWeed): Mixer wurde nicht vom Hauptmenü initialisiert! Sounds könnten fehlen.")
    else:
         print("DEBUG (zipWeed): Mixer ist verfügbar.")

    # --- Android Immersive Mode (Code unverändert) ---
    is_android = False
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        print("DEBUG (zipWeed): Pyjnius importiert.")
        Build = autoclass('android.os.Build$VERSION')
        sdk_int = Build.SDK_INT
        if sdk_int > 0:
            is_android = True
            print(f"DEBUG (zipWeed): Android erkannt (SDK: {sdk_int}).")
        else:
             raise RuntimeError("Nicht Android")
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        assert activity is not None
        View = autoclass('android.view.View')
        Window = autoclass('android.view.Window')
        WindowManager = autoclass('android.view.WindowManager$LayoutParams')
        flags = (View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)
        class SetUiVisibilityRunnablePJC(PythonJavaClass):
                __javainterfaces__ = ['java/lang/Runnable']
                def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
                @java_method('()V')
                def run(self):
                    try:
                        w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f); w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                    except Exception as e: print(f"FEHLER (Runnable): {e}"); traceback.print_exc()
        runnable = SetUiVisibilityRunnablePJC(activity, flags)
        if activity: activity.runOnUiThread(runnable); print("DEBUG (zipWeed): Runnable Immersive gestartet.")
    except ImportError: print("INFO (zipWeed): Pyjnius nicht gefunden. Nehme an, es ist nicht Android."); is_android = False
    except Exception as e: print(f"FEHLER oder Info (zipWeed): Immersive Mode fehlgeschlagen oder nicht Android: {e}"); is_android = False

    # --- Proportionale Berechnungen (Code unverändert) ---
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

    # Proportionale Schriftgröße für Statusanzeige (Code unverändert)
    BASE_GAME_FONT_SIZE = 30
    game_font_size = max(12, int(CALC_HEIGHT * (BASE_GAME_FONT_SIZE / FONT_SIZE_REF_H)))
    font = None
    try: font = pygame.font.SysFont("arial", game_font_size)
    except pygame.error: font = pygame.font.Font(None, game_font_size)
    if not font: print("WARNUNG: Konnte keine Spiel-Schriftart laden!"); font = pygame.font.Font(None, 30)

    status_pos_x = max(5, int(actual_screen_size[0] * (10 / ref_w)));
    status_pos_y = max(5, int(actual_screen_size[1] * (60 / ref_h)))

    # --- Pfad-Setup (Code unverändert) ---
    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    # Korrekter relativer Pfad von zipWeed.py zum data-Ordner auf der Hauptebene
    data_root_folder = os.path.join(script_dir_game, "..", "..")
    image_folder = "bilder"; sound_folder = "sounds" # Unterordner in data

    # --- Bilder laden (Code unverändert) ---
    background_image_scaled = None; use_background_image = False
    background_image_filename = "packingTable.png"
    background_image_path = os.path.join(data_root_folder, image_folder, background_image_filename)
    try:
        original_background_image = pygame.image.load(background_image_path).convert()
        background_image_scaled = pygame.transform.smoothscale(original_background_image, actual_screen_size)
        use_background_image = True
        print(f"DEBUG (zipWeed): Hintergrundbild '{background_image_filename}' geladen.")
    except Exception as e: print(f"WARNUNG: Laden Hintergrund '{background_image_path}' fehlgeschlagen: {e}.")

    small_image = None; use_small_image = False
    small_image_filename = f"weed_{sorte_name.lower()}.png"
    small_image_path = os.path.join(data_root_folder, image_folder, small_image_filename)
    try:
        original_small_image = pygame.image.load(small_image_path).convert_alpha()
        if small_size > 0:
            small_image = pygame.transform.smoothscale(original_small_image, (small_size, small_size))
            use_small_image = True
            print(f"DEBUG (zipWeed): Bild '{small_image_filename}' geladen.")
    except Exception as e: print(f"WARNUNG: Laden '{small_image_path}' fehlgeschlagen: {e}.")

    target_image = None; use_target_image = False; target_image_filename = "grip.png"
    target_image_path = os.path.join(data_root_folder, image_folder, target_image_filename)
    try:
        original_target_image = pygame.image.load(target_image_path).convert_alpha()
        if target_rect and target_rect.width > 0 and target_rect.height > 0:
            target_image = pygame.transform.smoothscale(original_target_image, (target_rect.width, target_rect.height))
            use_target_image = True
    except Exception as e: print(f"WARNUNG: Laden '{target_image_path}' fehlgeschlagen: {e}.")

    # --- Sounds laden (ALS SOUND-EFFEKTE mit angepasster Lautstärke) ---
    ready_sound = None; score_sound = None; no_resource_sound = None
    swipe_sound = None

    sound_filename_ready = "weedInBag.wav"; sound_filename_score = "bagFinish.wav"; sound_filename_swipe = "closeBag.ogg"
    sound_filename_no_resource = "error.wav"

    if mixer_ok: # Nur laden, wenn Mixer verfügbar ist
        sound_path_ready = os.path.join(data_root_folder, sound_folder, sound_filename_ready)
        try:
            ready_sound = pygame.mixer.Sound(sound_path_ready)
            ready_sound.set_volume(sfx_volume) # <<< LAUTSTÄRKE ANGEWENDET
        except Exception as e: print(f"WARNUNG (zipWeed): Laden Ready-Sound fehlgeschlagen: {e}")

        sound_path_score = os.path.join(data_root_folder, sound_folder, sound_filename_score)
        try:
            score_sound = pygame.mixer.Sound(sound_path_score)
            score_sound.set_volume(sfx_volume) # <<< LAUTSTÄRKE ANGEWENDET
        except Exception as e: print(f"WARNUNG (zipWeed): Laden Score-Sound fehlgeschlagen: {e}")

        sound_path_no_resource = os.path.join(data_root_folder, sound_folder, sound_filename_no_resource)
        try:
            no_resource_sound = pygame.mixer.Sound(sound_path_no_resource)
            no_resource_sound.set_volume(sfx_volume * 0.8) # <<< LAUTSTÄRKE ANGEWENDET (ggf. etwas leiser)
        except Exception as e: print(f"WARNUNG (zipWeed): Laden No-Resource-Sound fehlgeschlagen: {e}")

        swipe_sound_path = os.path.join(data_root_folder, sound_folder, sound_filename_swipe)
        try:
            swipe_sound = pygame.mixer.Sound(swipe_sound_path)
            swipe_sound.set_volume(sfx_volume) # <<< LAUTSTÄRKE ANGEWENDET
            print(f"DEBUG (zipWeed): Swipe-Sound '{sound_filename_swipe}' geladen.")
        except Exception as e:
            print(f"WARNUNG (zipWeed): Laden Swipe-Sound fehlgeschlagen: {e}")
            swipe_sound = None

    # --- Zurück-Button Definition (Code unverändert) ---
    BACK_BUTTON_WIDTH_PERCENT = 0.20
    BACK_BUTTON_HEIGHT_PERCENT = 0.08
    BASE_BACK_FONT_SIZE = 24
    back_button_width = int(actual_screen_size[0] * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(actual_screen_size[1] * BACK_BUTTON_HEIGHT_PERCENT)
    back_button_x = (actual_screen_size[0] - back_button_width) // 2
    back_button_y = 10
    back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
    back_button_font_size = max(16, int(actual_screen_size[1] * (BASE_BACK_FONT_SIZE / FONT_SIZE_REF_H)))
    back_button_font = None; back_text_surface = None
    try:
        back_button_font = pygame.font.SysFont("arial", back_button_font_size)
        back_text_surface = back_button_font.render("Zurück", True, BLACK)
    except Exception as e_backfont:
        print(f"WARNUNG: Konnte Font für Zurück-Button nicht laden: {e_backfont}")
        try: back_button_font = pygame.font.Font(None, int(back_button_font_size*1.1)); back_text_surface = back_button_font.render("Zurück", True, BLACK)
        except Exception: pass

    # Spielzustands-Variablen (Interaktion) - unverändert
    dragging, is_falling, offset_x, offset_y = False, False, 0, 0
    ready_for_swipe, is_swiping, swipe_start_x, swipe_current_x = False, False, None, None
    swipe_min_x, swipe_max_x = None, None
    display_persistent_swipe_bar = False; persistent_bar_rect = None
    resumed_swipe_initial_width = 0; was_ready_for_swipe = False
    clock = pygame.time.Clock()

    # --- Spiel-Loop (Logik und Zeichnen unverändert, Sound Playback nutzt die bereits gesetzte Lautstärke) ---
    running = True
    while running:
        # --- Event Handling ---
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("WARNUNG (zipWeed): QUIT Event empfangen. Beende nur Minispiel-Loop.")
                running = False # Beendet nur die zipWeed-Schleife
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False # Beendet nur die zipWeed-Schleife
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # --- Zurück-Button ---
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False;
                        continue # Restliche Klick-Logik überspringen

                    # --- Swipe Start ---
                    if current_grips >= 1 and current_weed >= 1 and ready_for_swipe and swipe_line_rect and swipe_line_rect.collidepoint(event.pos):
                        is_swiping = True; current_click_x = event.pos[0]; swipe_current_x = current_click_x; swipe_start_x = current_click_x
                        if display_persistent_swipe_bar and persistent_bar_rect is not None: swipe_min_x = min(persistent_bar_rect.left, current_click_x); swipe_max_x = max(persistent_bar_rect.right, current_click_x); resumed_swipe_initial_width = persistent_bar_rect.width; display_persistent_swipe_bar = False; persistent_bar_rect = None
                        else: swipe_min_x = current_click_x; swipe_max_x = current_click_x; resumed_swipe_initial_width = 0
                        dragging = False # Nicht mehr ziehen, wenn Swipe beginnt

                    # --- Drag Start ---
                    elif current_weed >= 1 and small_rect and small_rect.collidepoint(event.pos) and not is_swiping:
                        dragging = True; is_falling = False; ready_for_swipe = False; is_swiping = False
                        swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None; display_persistent_swipe_bar = False; persistent_bar_rect = None; resumed_swipe_initial_width = 0
                        offset_x = small_rect.x - event.pos[0]; offset_y = small_rect.y - event.pos[1]

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # --- Swipe Ende ---
                    if is_swiping:
                        is_swiping = False; final_width = 0; final_rect = None
                        # Logik zum Speichern des persistenten Balkens...
                        if current_grips >= 1 and swipe_line_rect and swipe_min_x is not None and swipe_max_x is not None:
                            clamped_orange_x=max(swipe_line_rect.left, swipe_min_x); clamped_orange_right=min(swipe_line_rect.right, swipe_max_x); final_width=max(0, clamped_orange_right - clamped_orange_x)
                            if final_width > 0: final_rect = pygame.Rect(clamped_orange_x, swipe_line_rect.y, final_width, swipe_line_rect.height)
                        if final_rect: persistent_bar_rect = final_rect; display_persistent_swipe_bar = True
                        else: display_persistent_swipe_bar = False; persistent_bar_rect = None
                        swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None; resumed_swipe_initial_width = 0

                        # Zustand nach Swipe-Ende prüfen (fallen oder bereit bleiben?)
                        if target_rect and small_rect and not target_rect.contains(small_rect):
                            ready_for_swipe = False; is_falling = True
                        elif target_rect and small_rect:
                            if current_weed >= 1 and current_grips >= 1: ready_for_swipe = True
                            else: ready_for_swipe = False
                            is_falling = False

                    # --- Drag Ende ---
                    elif dragging:
                        dragging = False
                        # Prüfen ob im Ziel oder fallen lassen
                        if target_rect and small_rect and target_rect.contains(small_rect):
                            if current_weed >= 1 and current_grips >= 1: ready_for_swipe = True
                            else: ready_for_swipe = False
                            is_falling = False
                            if ready_sound and ready_for_swipe: ready_sound.play() # Sound spielen
                        elif target_rect and small_rect: # Außerhalb des Ziels losgelassen
                            ready_for_swipe = False; is_falling = True

            elif event.type == pygame.MOUSEMOTION:
                # --- Swiping ---
                if is_swiping:
                    swipe_current_x = event.pos[0]
                    # Min/Max für Balken aktualisieren
                    if swipe_min_x is not None and swipe_max_x is not None: swipe_min_x = min(swipe_min_x, swipe_current_x); swipe_max_x = max(swipe_max_x, swipe_current_x)

                    # Swipe-Distanz prüfen und punkten
                    if swipe_start_x is not None and swipe_line_rect:
                        current_added_distance = abs(swipe_current_x - swipe_start_x); total_effective_distance = resumed_swipe_initial_width + current_added_distance

                        if total_effective_distance >= min_swipe_distance:
                            if current_weed >= 1 and current_grips >= 1: # Nur punkten, wenn Ressourcen da sind
                                packed_weed += 1
                                current_weed -= 1
                                current_grips -= 1
                                print(f"DEBUG: Punkt erzielt! Weed: {current_weed}, Grips: {current_grips}, Packed: {packed_weed}")
                                if score_sound: score_sound.play()
                                if swipe_sound: swipe_sound.play() # Swipe-Sound beim Erfolg

                                # Objekt zurücksetzen, wenn noch Weed da ist
                                if current_weed >= 1 and small_rect:
                                    small_rect.topleft = tuple(start_pos)
                                else:
                                    print("INFO: Kein Weed mehr zum Zurücksetzen.")
                                    dragging = False # Sicherheitshalber

                                # Swipe beenden und Zustand zurücksetzen
                                ready_for_swipe=False; is_falling=False; is_swiping=False; display_persistent_swipe_bar=False; persistent_bar_rect=None; resumed_swipe_initial_width = 0
                                swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None
                            else:
                                # Swipe-Ziel erreicht, aber keine Ressourcen
                                print("DEBUG: Swipe-Ziel erreicht, aber keine Ressourcen (Weed oder Grips).")
                                if no_resource_sound: no_resource_sound.play()
                                # Swipe beenden und Zustand zurücksetzen
                                is_swiping=False; display_persistent_swipe_bar=False; persistent_bar_rect=None; resumed_swipe_initial_width = 0
                                swipe_start_x=swipe_current_x=swipe_min_x=swipe_max_x=None
                                # Prüfen ob Objekt im Ziel war oder fallen soll
                                if target_rect and small_rect and target_rect.contains(small_rect):
                                    ready_for_swipe = False # Kann nicht mehr swipen
                                    is_falling = False
                                else:
                                    ready_for_swipe = False
                                    is_falling = True

                # --- Dragging ---
                elif dragging and small_rect and current_weed >= 1:
                    # Objekt bewegen, Kollision und Grenzen prüfen (Code unverändert)
                    old_rect = small_rect.copy(); potential_x = event.pos[0] + offset_x; potential_y = event.pos[1] + offset_y; small_rect.topleft = (potential_x, potential_y)
                    if current_grips >= 1 and target_rect and not target_rect.contains(old_rect) and small_rect.colliderect(target_rect):
                        if old_rect.right <= target_rect.left and small_rect.right > target_rect.left: small_rect.right = target_rect.left
                        elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right: small_rect.left = target_rect.right
                        elif old_rect.bottom <= target_rect.top and small_rect.bottom > target_rect.top: small_rect.bottom = target_rect.top
                        elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom: small_rect.top = target_rect.bottom
                    screen_rect = pygame.Rect(0, 0, actual_screen_size[0], actual_screen_size[1]); small_rect.clamp_ip(screen_rect)

        # --- Spiel-Logik / Physik (Fallen) --- (Code unverändert)
        if small_rect and is_falling and not dragging and not ready_for_swipe and not is_swiping:
            potential_y = small_rect.y + gravity; potential_rect = small_rect.copy(); potential_rect.y = potential_y; screen_height = actual_screen_size[1]
            collides_with_target_bottom = False
            if current_grips >= 1 and target_rect:
                collides_with_target_bottom = (potential_rect.bottom > target_rect.bottom and small_rect.bottom <= target_rect.bottom and potential_rect.right > target_rect.left and potential_rect.left < target_rect.right)

            if collides_with_target_bottom:
                small_rect.bottom = target_rect.bottom; is_falling = False
                if target_rect.contains(small_rect) and current_weed >= 1 and current_grips >= 1:
                    ready_for_swipe = True
                    if ready_sound and not was_ready_for_swipe: ready_sound.play() # Sound hier, da gelandet
                else: ready_for_swipe = False
            else:
                if potential_rect.bottom >= screen_height:
                    small_rect.bottom = screen_height; is_falling = False; ready_for_swipe = False
                else: small_rect.y = potential_y

        # --- Zustandskorrektur --- (Code unverändert)
        if ready_for_swipe and not is_swiping and target_rect and small_rect and not target_rect.contains(small_rect):
            if not dragging: ready_for_swipe = False; is_falling = True

        # --- Sound-Trigger State Update --- (Code unverändert)
        if ready_for_swipe and not was_ready_for_swipe:
            was_ready_for_swipe = True
        elif not ready_for_swipe and was_ready_for_swipe:
            was_ready_for_swipe = False

        # --- Zeichnen --- (Code unverändert)
        if use_background_image and background_image_scaled:
            screen.blit(background_image_scaled, (0, 0))
        else:
            screen.fill(WHITE)

        # Zielzone (Grip)
        if current_grips >= 1 and target_rect:
            if use_target_image and target_image is not None: screen.blit(target_image, target_rect.topleft)
            else: pygame.draw.rect(screen, BLUE, target_rect)

        # Swipe-Linie und Fortschrittsbalken
        if current_grips >= 1 and ready_for_swipe and swipe_line_rect:
            pygame.draw.rect(screen, GREEN, swipe_line_rect)
            bar_to_draw = None
            if is_swiping and swipe_min_x is not None and swipe_max_x is not None:
                clamped_orange_x_draw = max(swipe_line_rect.left, swipe_min_x); clamped_orange_right_draw = min(swipe_line_rect.right, swipe_max_x); clamped_orange_width_draw = max(0, clamped_orange_right_draw - clamped_orange_x_draw)
                if clamped_orange_width_draw > 0: bar_to_draw = pygame.Rect(clamped_orange_x_draw, swipe_line_rect.y, clamped_orange_width_draw, swipe_line_rect.height)
            elif display_persistent_swipe_bar and persistent_bar_rect is not None: bar_to_draw = persistent_bar_rect
            if bar_to_draw: pygame.draw.rect(screen, ORANGE, bar_to_draw)
        else: # Reset persistent bar if not ready anymore
            display_persistent_swipe_bar = False; persistent_bar_rect = None; resumed_swipe_initial_width = 0

        # Bewegliches Objekt (Weed)
        if current_weed >= 1 and small_rect:
            if use_small_image and small_image is not None: screen.blit(small_image, small_rect.topleft)
            else: pygame.draw.rect(screen, RED, small_rect)

        # Statusanzeige
        if font:
            weed_text = font.render(f"Weed: {current_weed}", True, RED)
            grips_text = font.render(f"Grips: {current_grips}", True, BLUE)
            packed_text = font.render(f"Verpackt: {packed_weed}", True, GREEN)
            line_height = game_font_size + 5
            screen.blit(weed_text, (status_pos_x, status_pos_y))
            screen.blit(grips_text, (status_pos_x, status_pos_y + line_height))
            screen.blit(packed_text, (status_pos_x, status_pos_y + 2 * line_height))

        # Zurück-Button
        if back_button_rect:
            back_button_color = GRAY if not back_button_rect.collidepoint(mouse_pos) else DARK_GRAY
            pygame.draw.rect(screen, back_button_color, back_button_rect)
            pygame.draw.rect(screen, BLACK, back_button_rect, 2)
            if back_text_surface and back_button_font:
                back_text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                screen.blit(back_text_surface, back_text_rect.topleft)

        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print("INFO (zipWeed): Minispiel-Schleife beendet.")
    # Kein pygame.mixer.music.stop() hier! Das Hauptmenü steuert die Musik.

    # Gebe die finalen Werte zurück
    return current_weed, current_grips, packed_weed, sorte_name

# --- Ende der run_zip_weed_game Funktion ---


# --- Code für Standalone-Ausführung ---
if __name__ == "__main__":
    print("INFO: zipWeed.py wird eigenständig ausgeführt.")
    pygame.init()
    # Mixer hier initialisieren für Standalone
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
    except Exception: _sw = 800; _sh = 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED)
    pygame.display.set_caption("ZipWeed Minispiel (Standalone)")

    # --- EINSTELLUNGEN LADEN für Standalone ---
    try: standalone_script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError: standalone_script_dir = os.path.abspath(".")
    standalone_settings_dir = os.path.join(standalone_script_dir, "..", "..", "data", "settings")
    standalone_settings_file = os.path.join(standalone_settings_dir, "settings.json")
    standalone_game_settings = load_standalone_settings(standalone_settings_file)
    # --- Ende Einstellungen Laden ---

    try:
        start_weed = 10
        start_grips = 8
        start_sorte = "Normal"
        print(f"\n--- Starte Standalone mit: Weed={start_weed}, Grips={start_grips}, Sorte='{start_sorte}' ---\n")
        # Übergebe die geladenen Einstellungen an die Funktion
        result = run_zip_weed_game(standalone_screen, start_weed, start_grips, start_sorte, standalone_game_settings) # <<< EINSTELLUNGEN ÜBERGEBEN
        print(f"\n--- Standalone Beendet. Ergebnis: ---")
        print(f"  Verbleibendes Weed: {result[0]}")
        print(f"  Verbleibende Grips: {result[1]}")
        print(f"  Verpacktes Weed:    {result[2]}")
        print(f"  Sorte gespielt:     '{result[3]}'")
        print("-------------------------------------\n")

    except Exception as e_main: print(f"FEHLER in Standalone: {e_main}"); traceback.print_exc()
    finally:
        # Wichtig: Nur im Standalone-Modus Pygame beenden!
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---