# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os
import traceback
import time
import random
# --- KORRIGIERTER IMPORT (Name an Dateinamen angepasst) ---
# Stelle sicher, dass die Datei 'cockCrackpart2.py' im selben Verzeichnis liegt
# und klein geschrieben ist, falls nötig.
try:
    # Versuche relativen Import zuerst (wenn dies Teil eines Pakets ist)
    from . import cockCrackpart2
except ImportError:
    # Fallback für Standalone-Ausführung oder wenn die Struktur anders ist
    try:
        import cockCrackpart2
    except ImportError as e:
        print(f"FEHLER: Konnte cockCrackpart2 nicht importieren: {e}")
        cockCrackpart2 = None # Setze auf None, um Abstürze zu vermeiden, wenn es fehlt


# --- Konstanten und Farben ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0) # Farbe für Pfeil (Fallback)
BLUE = (0, 0, 255) # Farbe für Balken (Fallback)
GREEN = (0, 255, 0) # Farbe für grünen Bereich (Fallback)
ORANGE = (255, 165, 0) # Farbe für Kreis (Fallback)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
CENTER_RECT_COLOR = (50, 50, 50) # Farbe für Rechteck (Fallback)
INTERACTION_CIRCLE_COLOR = ORANGE # Fallback

# --- Dateinamen für Bilder (mit Dummies & neuen Elementen) ---
background_image_filename = "laborTable.png" # Optional
# NEU: Für UI-Elemente
top_bar_blue_bg_filename = "bar_blue_bg.png"
top_bar_green_overlay_filename = "bar_green_overlay.png" # Muss transparent sein ausser im grünen Bereich
arrow_indicator_filename = "arrow_indicator.png"
lower_panel_bg_filename = "lower_panel_bg.png"
interaction_button_up_filename = "interaction_button_up.png"
interaction_button_down_filename = "interaction_button_down.png" # Für Klick-Feedback
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png" # Für Hover-Effekt
# NEU: Für Animation
animation_filenames = [
    "anim_frame_1.png",
    "anim_frame_2.png",
    "anim_frame_3.png",
    # "anim_frame_4.png", # Füge mehr hinzu, falls gewünscht
]


# --- Sound-Dateinamen (Dummy Logik) ---
sound_filename_score = "bagFinish.wav" # Sound bei Erfolg
sound_filename_no_resource = "error.wav" # Sound bei Fehler/Mangel

# --- Hauptfunktion des Spiels (Stark modifiziert) ---
def run_cock_crack_game(screen_surface, start_pills, start_liquid, start_crack, liquid_id, pills_id):
    """ Führt das modifizierte CockCrack Minispiel aus (V6 Bilder & Anim). """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    print(f"DEBUG (cockCrack V6 Bilder & Anim): Nutze Screen-Größe: {actual_screen_size}")

    # Interne Statusvariablen initialisieren
    current_pills = start_pills
    current_liquid = start_liquid
    current_crack = start_crack
    liquid_name = liquid_id
    pills_name = pills_id
    print(f"DEBUG (cockCrack V6 Bilder & Anim): Startwerte: Pills={current_pills}, Liquid={current_liquid}, Crack={current_crack}")

    # --- Referenz-Dimensionen ---
    ref_w = 800.0
    ref_h = 600.0
    FONT_SIZE_REF_H = 600.0

    # --- Mixer Initialisierung ---
    score_sound = None
    no_resource_sound = None
    mixer_ok = False
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print("DEBUG (cockCrack V6 Bilder & Anim): Mixer initialisiert.")
            mixer_ok = True
        except pygame.error as e:
            print(f"WARNUNG (cockCrack V6 Bilder & Anim): Mixer fehlgeschlagen: {e}")
    else:
        print("DEBUG (cockCrack V6 Bilder & Anim): Mixer war bereits initialisiert.")
        mixer_ok = True

    # --- PFAD-SETUP (angepasst) ---
    try:
        script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir_game = os.path.abspath(".")
    # *** ANPASSEN, FALLS DEINE STRUKTUR ANDERS IST! ***
    project_root_folder = os.path.join(script_dir_game, "..", "..", "..")
    data_subfolder = "data"
    image_folder_rel = os.path.join(data_subfolder, "bilder")
    sound_folder_rel = os.path.join(data_subfolder, "sounds")
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, image_folder_rel))
    sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, sound_folder_rel))
    print(f"DEBUG (cockCrack V6 Bilder & Anim): Script Dir: {script_dir_game}")
    print(f"DEBUG (cockCrack V6 Bilder & Anim): Image folder (abs): {image_folder_abs}")
    print(f"DEBUG (cockCrack V6 Bilder & Anim): Sound folder (abs): {sound_folder_abs}")
    # --- ENDE PFAD-SETUP ---

    # --- Zustand für neue Mechanik ---
    arrow_width = 30          # Breite des Pfeil-Bildes (oder Fallback-Polygon)
    arrow_height = 30         # Höhe des Pfeil-Bildes (oder Fallback-Polygon)
    arrow_x = 0               # Startposition wird später gesetzt
    arrow_speed = 150         # Pixel pro Sekunde für Rechtsbewegung
    arrow_return_speed_factor = 1.5 # Faktor für Rückkehrgeschwindigkeit (1.5 = 50% schneller)
    arrow_moving_right = False  # Bewegt sich der Pfeil aktiv nach rechts (durch Drücken oder Momentum)?
    arrow_momentum_timer = 0.0 # Wie lange bewegt er sich noch nach rechts nach Loslassen?
    momentum_factor = 0.8     # Wie viel % der Drückdauer wird als Momentum addiert

    circle_held_down = False    # Wird der Interaktionskreis gerade gedrückt?
    press_start_time = 0.0      # Zeitpunkt, wann der Kreis gedrückt wurde

    time_in_green_zone = 0.0    # Wie lange ist der Pfeil schon im grünen Bereich?
    goal_duration = 5.0         # Ziel: 5 Sekunden
    goal_achieved_this_round = False # Wurde das Ziel in dieser Runde schon erreicht?
    can_trigger_win = True      # Kann ein Gewinn gerade ausgelöst werden (verhindert Mehrfachauslösung)

    # NEU: Animationsvariablen
    animation_frames = []      # Liste für geladene/skalierte Animationsbilder
    animation_index = 0        # Aktueller Frame-Index
    animation_timer = 0.0      # Timer für Frame-Wechsel
    animation_frame_duration = 0.1 # Sekunden pro Frame (ca. 10 FPS)
    show_animation = False     # Soll die Animation angezeigt werden?

    # --- Android Immersive Mode ---
    is_android = False
    # ... (Hier könnte der Code für Immersive Mode stehen) ...


    # --- SPIEL ELEMENTE DEFINITIONEN ---

    # Unteres Rechteck (bleibt gleich wie vorher)
    center_rect_width = int(screen_width * 0.4)
    center_rect_height = int(screen_height * 0.4)
    center_rect_x = screen_center_x - center_rect_width // 2
    bottom_rect_top_y = screen_center_y + int(screen_height * 0.05)
    bottom_margin = int(screen_height * 0.05)
    center_rect_y = min(bottom_rect_top_y, screen_height - center_rect_height - bottom_margin)
    center_rect_y = max(center_rect_y, screen_center_y)
    center_rect = pygame.Rect(center_rect_x, center_rect_y, center_rect_width, center_rect_height)
    print(f"DEBUG: Unteres Center Rect: {center_rect}")

    # Optional: Skalierte Grösse für Animationsframes (basierend auf center_rect)
    anim_frame_width = int(center_rect_width * 0.5) # z.B. 50% der Breite des unteren Panels
    anim_frame_height = int(anim_frame_width * 0.5) # Höhe anpassen (angenommenes Seitenverhältnis)

    # Oberer Balken (Breite angepasst, mehr Abstand oben)
    bar_height = int(screen_height * 0.04) # Schmaler gemacht
    bar_top_margin = int(screen_height * 0.10) # MEHR PLATZ OBEN für den Button (z.B. 10%)
    extra_width_side = int(center_rect_width * 0.10)
    bar_width = center_rect_width + (2 * extra_width_side)
    bar_x = screen_center_x - bar_width // 2
    bar_y = bar_top_margin
    bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    print(f"DEBUG: Angepasster Oberer Balken: {bar_rect}")

    # Grüner Bereich im Balken (mittig im *neuen* Balken)
    green_area_width = int(bar_width * 0.1) # Schmaler gemacht
    green_area_x = bar_rect.centerx - green_area_width // 2 # Zentriert im neuen Balken
    green_area_rect = pygame.Rect(green_area_x, bar_rect.top, green_area_width, bar_rect.height)
    print(f"DEBUG: Angepasster Grüner Bereich: {green_area_rect}")

    # Setze die Startposition des Pfeils auf den linken Rand des Balkens
    arrow_x = bar_rect.left


    # Interaktionskreis (bleibt relativ zum unteren Rechteck)
    interaction_circle_radius = int(min(center_rect_width, center_rect_height) * 0.12)
    interaction_circle_x = center_rect.centerx
    interaction_circle_y = center_rect.top + int(center_rect.height * 0.75)
    interaction_circle_pos = (interaction_circle_x, interaction_circle_y)
    interaction_circle_rect = pygame.Rect(
        interaction_circle_x - interaction_circle_radius,
        interaction_circle_y - interaction_circle_radius,
        interaction_circle_radius * 2,
        interaction_circle_radius * 2
    )
    print(f"DEBUG: Unterer Interaction Circle: pos={interaction_circle_pos}, radius={interaction_circle_radius}")

    # --- Assets Laden (mit Dummies & neuen Bildern) ---
    # Hintergrundbild (optional)
    scaled_background_image = None
    use_background_image = False
    background_path = os.path.join(image_folder_abs, background_image_filename)
    try:
        loaded_bg = pygame.image.load(background_path).convert()
        scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size)
        use_background_image = True
        print(f"DEBUG: Hintergrundbild '{background_image_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Hintergrundbild '{background_path}' laden fehlgeschlagen: {e}.")

    # NEU: Lade UI-Element-Bilder
    scaled_top_bar_blue = None
    use_top_bar_blue_image = False
    top_bar_blue_path = os.path.join(image_folder_abs, top_bar_blue_bg_filename)
    try:
        img = pygame.image.load(top_bar_blue_path).convert_alpha()
        scaled_top_bar_blue = pygame.transform.smoothscale(img, bar_rect.size)
        use_top_bar_blue_image = True
        print(f"DEBUG: Blauer Balken BG '{top_bar_blue_bg_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Blauer Balken BG laden/skalieren fehlgeschlagen: {e}")

    scaled_green_area_overlay = None
    use_green_area_overlay_image = False
    green_overlay_path = os.path.join(image_folder_abs, top_bar_green_overlay_filename)
    try:
        # Wichtig: Dieses Bild sollte nur im grünen Bereich sichtbar sein und sonst transparent!
        img = pygame.image.load(green_overlay_path).convert_alpha()
        scaled_green_area_overlay = pygame.transform.smoothscale(img, green_area_rect.size)
        use_green_area_overlay_image = True
        print(f"DEBUG: Grüner Overlay '{top_bar_green_overlay_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Grüner Overlay laden/skalieren fehlgeschlagen: {e}")

    scaled_arrow_indicator = None
    use_arrow_indicator_image = False
    arrow_indicator_path = os.path.join(image_folder_abs, arrow_indicator_filename)
    try:
        img = pygame.image.load(arrow_indicator_path).convert_alpha()
        # Skaliere basierend auf definierten arrow_width/height
        # Beachte: arrow_width/height sind jetzt die Zieldimensionen für das Bild
        scaled_arrow_indicator = pygame.transform.smoothscale(img, (arrow_width, arrow_height))
        use_arrow_indicator_image = True
        print(f"DEBUG: Pfeil-Indikator '{arrow_indicator_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Pfeil-Indikator laden/skalieren fehlgeschlagen: {e}")

    scaled_lower_panel_bg = None
    use_lower_panel_bg_image = False
    lower_panel_path = os.path.join(image_folder_abs, lower_panel_bg_filename)
    try:
        img = pygame.image.load(lower_panel_path).convert_alpha()
        scaled_lower_panel_bg = pygame.transform.smoothscale(img, center_rect.size)
        use_lower_panel_bg_image = True
        print(f"DEBUG: Unteres Panel BG '{lower_panel_bg_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Unteres Panel BG laden/skalieren fehlgeschlagen: {e}")

    scaled_interaction_button_up = None
    scaled_interaction_button_down = None
    use_interaction_button_images = False
    interaction_up_path = os.path.join(image_folder_abs, interaction_button_up_filename)
    interaction_down_path = os.path.join(image_folder_abs, interaction_button_down_filename)
    try:
        img_up = pygame.image.load(interaction_up_path).convert_alpha()
        img_down = pygame.image.load(interaction_down_path).convert_alpha()
        btn_size = (interaction_circle_radius * 2, interaction_circle_radius * 2)
        scaled_interaction_button_up = pygame.transform.smoothscale(img_up, btn_size)
        scaled_interaction_button_down = pygame.transform.smoothscale(img_down, btn_size)
        use_interaction_button_images = True
        print(f"DEBUG: Interaktions-Buttons '{interaction_button_up_filename}', '{interaction_button_down_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Interaktions-Buttons laden/skalieren fehlgeschlagen: {e}")

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
        print(f"DEBUG: Zurück-Buttons '{back_button_bg_filename}', '{back_button_hover_filename}' geladen.")
    except Exception as e:
        print(f"WARNUNG: Zurück-Buttons laden/skalieren fehlgeschlagen: {e}")

    # NEU: Lade Animations-Frames
    for filename in animation_filenames:
        anim_path = os.path.join(image_folder_abs, filename)
        try:
            img = pygame.image.load(anim_path).convert_alpha()
            # Skaliere auf gewünschte Grösse
            scaled_img = pygame.transform.smoothscale(img, (anim_frame_width, anim_frame_height))
            animation_frames.append(scaled_img)
            print(f"DEBUG: Animationsframe '{filename}' geladen und skaliert.")
        except Exception as e:
            print(f"WARNUNG: Animationsframe '{anim_path}' laden/skalieren fehlgeschlagen: {e}")
            # Optional: Füge einen Platzhalter hinzu oder überspringe


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

    # Position für Statusanzeige (unterhalb des Balkens)
    status_pos_x = max(10, int(screen_width * 0.02))
    status_start_y = bar_rect.bottom + int(screen_height * 0.02) # Start unter dem Balken
    status_pos_y = status_start_y # Y für Crack-Anzeige
    resource_pos_y = status_pos_y + max(12, game_font_size) + 10 # Y für Pillen/Liquid

    # --- Sounds laden (Dummy Logik) ---
    sound_path_score = os.path.join(sound_folder_abs, sound_filename_score)
    sound_path_no_resource = os.path.join(sound_folder_abs, sound_filename_no_resource)
    if mixer_ok:
        try:
            score_sound = pygame.mixer.Sound(sound_path_score); score_sound.set_volume(0.9)
            print(f"DEBUG: Score-Sound '{sound_filename_score}' geladen.")
        except Exception as e:
            print(f"WARNUNG: Score-Sound '{sound_path_score}' laden fehlgeschlagen: {e}")
            score_sound = None
        try:
            no_resource_sound = pygame.mixer.Sound(sound_path_no_resource); no_resource_sound.set_volume(0.7)
            print(f"DEBUG: NoResource-Sound '{sound_filename_no_resource}' geladen.")
        except Exception as e:
            print(f"WARNUNG: NoResource-Sound '{sound_path_no_resource}' laden fehlgeschlagen: {e}")
            no_resource_sound = None
    # -------------------------------------

    # --- UI Elemente ---
    # Zurück-Button (Position angepasst: ÜBER dem Balken)
    BACK_BUTTON_WIDTH_PERCENT, BACK_BUTTON_HEIGHT_PERCENT, BASE_BACK_FONT_SIZE = 0.20, 0.08, 24
    back_button_width = int(screen_width * BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(screen_height * BACK_BUTTON_HEIGHT_PERCENT)
    # Zentriert im oberen Randbereich (bar_top_margin)
    back_button_y = max(0, (bar_top_margin // 2) - (back_button_height // 2)) # Vertikal zentriert im oberen Rand
    back_button_rect = pygame.Rect((screen_width - back_button_width) // 2, back_button_y, back_button_width, back_button_height)
    back_button_font = None; back_text_surface = None
    back_font_size = max(16, int(screen_height * (BASE_BACK_FONT_SIZE / FONT_SIZE_REF_H)))
    try:
        back_button_font = pygame.font.SysFont("arial", back_font_size)
        back_text_surface = back_button_font.render("Zurück", True, BLACK)
    except:
        try: back_button_font = pygame.font.Font(None, int(back_font_size*1.1)); back_text_surface = back_button_font.render("Zurück", True, BLACK)
        except: pass # Font laden fehlgeschlagen
    print(f"DEBUG: Zurück Button Rect: {back_button_rect}")

    # --- Spielzustands-Variablen (Interaktion) ---
    game_over_delay_timer = 0.0 # Timer für Reset nach Aktion

    clock = pygame.time.Clock()
    last_time = time.time()

    # --- Spiel-Loop ---
    running = True
    while running:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1) # Delta time capped
        last_time = current_time

        mouse_pos = pygame.mouse.get_pos()

        # --- Event Handling (Angepasst für neue Mechanik) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("WARNUNG (cockCrack V6 Bilder & Anim): QUIT Event empfangen.")
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    # Zurück Button
                    if back_button_rect and back_button_rect.collidepoint(event.pos):
                        running = False
                        continue

                    # Klick auf den Interaktionskreis? -> Startet Pfeilbewegung
                    if interaction_circle_rect.collidepoint(event.pos):
                        print("DEBUG: Klick/Hold auf Interaktionskreis.")
                        if not circle_held_down: # Nur beim ersten Klick starten
                           press_start_time = time.time()
                           arrow_moving_right = True # Starte Rechtsbewegung
                           arrow_momentum_timer = 0.0 # Lösche altes Momentum
                           circle_held_down = True
                           # Optional: Ziel-Status bei neuem Versuch zurücksetzen?
                           # goal_achieved_this_round = False
                           # time_in_green_zone = 0.0

            if event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1:
                     if circle_held_down: # Nur wenn der Kreis losgelassen wird
                         print("DEBUG: Loslassen des Interaktionskreises.")
                         press_duration = time.time() - press_start_time
                         arrow_momentum_timer = press_duration * momentum_factor
                         print(f"DEBUG: Haltedauer: {press_duration:.2f}s, Momentum gesetzt auf: {arrow_momentum_timer:.2f}s")
                         circle_held_down = False
                         # arrow_moving_right bleibt True, bis Momentum abläuft

        # --- Spiel-Logik Update (Pfeilbewegung & Ziel & Animation) ---

        # 1. Pfeilbewegung aktualisieren
        arrow_was_moving = circle_held_down or arrow_momentum_timer > 0 or (not arrow_moving_right and arrow_x > bar_rect.left)

        if circle_held_down:
            # Bewegung nach rechts während gedrückt
            arrow_x += arrow_speed * dt
            # Stopp am rechten Rand
            arrow_x = min(arrow_x, bar_rect.right)
            arrow_moving_right = True # Sicherstellen, dass Richtung stimmt

        elif arrow_momentum_timer > 0:
            # Bewegung nach rechts durch Momentum nach Loslassen
            arrow_momentum_timer -= dt
            arrow_x += arrow_speed * dt
            # Stopp am rechten Rand
            arrow_x = min(arrow_x, bar_rect.right)
            if arrow_x >= bar_rect.right or arrow_momentum_timer <= 0:
                arrow_momentum_timer = 0 # Momentum aufgebraucht/Rand erreicht
                arrow_moving_right = False # Beginnt Rückkehr

        elif not arrow_moving_right and arrow_x > bar_rect.left:
            # Rückkehrbewegung nach links
            arrow_x -= arrow_speed * arrow_return_speed_factor * dt
            # Stopp am linken Rand
            arrow_x = max(arrow_x, bar_rect.left)

        # 1b. Animation steuern
        arrow_is_moving_now = circle_held_down or arrow_momentum_timer > 0 or (not arrow_moving_right and arrow_x > bar_rect.left)
        if arrow_is_moving_now:
            show_animation = True
            animation_timer += dt
            if animation_timer >= animation_frame_duration and len(animation_frames) > 0:
                animation_timer -= animation_frame_duration
                animation_index = (animation_index + 1) % len(animation_frames)
        else: # Pfeil steht still (am linken Rand)
             show_animation = False
             animation_index = 0 # Setze auf Startframe zurück
             animation_timer = 0.0

        # 2. Ziel-Überprüfung (5 Sekunden im grünen Bereich)
        is_in_green = green_area_rect.left <= arrow_x <= green_area_rect.right
        if is_in_green:
            if not goal_achieved_this_round: # Nur Zeit zählen, wenn Ziel noch nicht erreicht
                time_in_green_zone += dt
        else:
            time_in_green_zone = 0 # Timer zurücksetzen, wenn Pfeil draußen ist

        # Ziel erreicht?
        if can_trigger_win and time_in_green_zone >= goal_duration and not goal_achieved_this_round:
            print(f"INFO: Ziel erreicht! {goal_duration}s im grünen Bereich.")
            goal_achieved_this_round = True
            can_trigger_win = False # Verhindert sofortige Mehrfachauslösung
            game_over_delay_timer = 2.0 # Zeit für Anzeige/Reset etwas länger

            # --- Ressourcen prüfen und Part 2 starten ---
            needed_pills = 1
            needed_liquid = 1
            if current_pills >= needed_pills and current_liquid >= needed_liquid:
                print(f"INFO: Genug Ressourcen. Starte cockCrackpart2...")
                if cockCrackpart2:
                    try:
                        points_from_part2 = cockCrackpart2.run_cock_crack_game(
                            screen, current_pills, current_liquid, 0, liquid_name, pills_name
                        )
                        print(f"DEBUG: cockCrackpart2 beendet. Ergebnis: {points_from_part2}")
                        if points_from_part2 > 0:
                            print(f"INFO: {points_from_part2} Punkt(e) erzielt. Verbrauche Ressourcen.")
                            current_pills -= needed_pills
                            current_liquid -= needed_liquid
                            current_crack += points_from_part2
                            print(f"DEBUG: Neue Ressourcen: Pills={current_pills}, Liquid={current_liquid}, Crack={current_crack}")
                            if score_sound: score_sound.play()
                        else:
                            print("INFO: cockCrackpart2 ohne Punkt beendet.")
                            if no_resource_sound: no_resource_sound.play()
                            goal_achieved_this_round = False # Ermöglicht neuen Versuch direkt?
                            can_trigger_win = True
                    except AttributeError:
                         print("FEHLER: Funktion 'run_cock_crack_game' nicht in cockCrackpart2 gefunden!")
                         if no_resource_sound: no_resource_sound.play()
                         goal_achieved_this_round = False; can_trigger_win = True # Reset für neuen Versuch
                    except Exception as e_part2:
                         print(f"FEHLER beim Ausführen von cockCrackpart2: {e_part2}")
                         traceback.print_exc()
                         if no_resource_sound: no_resource_sound.play()
                         goal_achieved_this_round = False; can_trigger_win = True # Reset für neuen Versuch
                else:
                    print("FEHLER: Modul cockCrackpart2 konnte nicht importiert werden!")
                    if no_resource_sound: no_resource_sound.play()
                    goal_achieved_this_round = False; can_trigger_win = True # Reset für neuen Versuch
            else: # Nicht genug Ressourcen, obwohl Ziel erreicht
                print(f"INFO: Ziel erreicht, aber NICHT genug Ressourcen! Benötigt: {needed_pills}P, {needed_liquid}L.")
                if no_resource_sound: no_resource_sound.play()
                goal_achieved_this_round = False # Ziel nicht wirklich "erreicht", da Ressourcen fehlen
                can_trigger_win = True # Erlaube neuen Versuch

        # 3. Reset Timer Logik
        if game_over_delay_timer > 0 and not circle_held_down: # Reset nur, wenn Kreis nicht gedrückt wird
            game_over_delay_timer -= dt
            if game_over_delay_timer <= 0:
                print("DEBUG (cockCrack V6 Bilder & Anim): Reset nach Zielerreichung/Cooldown.")
                # Reset Pfeil und Ziel-Status
                arrow_x = bar_rect.left
                arrow_moving_right = False
                arrow_momentum_timer = 0.0
                time_in_green_zone = 0.0
                goal_achieved_this_round = False
                can_trigger_win = True
                # NEU: Animation zurücksetzen
                show_animation = False
                animation_index = 0
                animation_timer = 0.0


        # --- Zeichnen (Angepasstes Layout mit Bildern & Animation) ---
        # Hintergrund
        if use_background_image and scaled_background_image:
            screen.blit(scaled_background_image, (0, 0))
        else:
            screen.fill(WHITE) # Fallback-Hintergrund

        # Oberer Balken (Bild oder Fallback)
        if use_top_bar_blue_image and scaled_top_bar_blue:
             screen.blit(scaled_top_bar_blue, bar_rect.topleft)
        else:
             pygame.draw.rect(screen, BLUE, bar_rect) # Fallback

        # Grüner Bereich Overlay (Bild oder Fallback)
        if use_green_area_overlay_image and scaled_green_area_overlay:
             screen.blit(scaled_green_area_overlay, green_area_rect.topleft)
        else:
             pygame.draw.rect(screen, GREEN, green_area_rect) # Fallback

        # Roten Pfeil zeichnen (Bild oder Fallback)
        # Sicherstellen, dass der Pfeil nicht über die Balkenränder hinausragt (visuell)
        arrow_draw_x = max(bar_rect.left + arrow_width/2, min(arrow_x, bar_rect.right - arrow_width/2))
        if use_arrow_indicator_image and scaled_arrow_indicator:
            # Positioniere das Bild so, dass seine Mitte unten am Pfeil-X/Y liegt
            arrow_rect = scaled_arrow_indicator.get_rect(midbottom=(int(arrow_draw_x), bar_rect.bottom))
            screen.blit(scaled_arrow_indicator, arrow_rect)
        else:
            # Fallback: Polygon zeichnen
            arrow_center_y = bar_rect.bottom
            arrow_points_clamped = [
                (int(arrow_draw_x), arrow_center_y - arrow_height),
                (int(arrow_draw_x - arrow_width / 2), arrow_center_y),
                (int(arrow_draw_x + arrow_width / 2), arrow_center_y)
            ]
            pygame.draw.polygon(screen, RED, arrow_points_clamped)


        # Zielzeit anzeigen (bleibt gleich)
        if info_font:
             time_text_str = f"In Grün: {time_in_green_zone:.1f}s / {goal_duration:.1f}s"
             # Farbe ändert sich, wenn Ziel erreicht (bis Reset)
             time_text_color = GREEN if goal_achieved_this_round else BLACK
             time_text = info_font.render(time_text_str, True, time_text_color)
             # Position z.B. rechts neben dem Balken
             time_text_rect = time_text.get_rect(midleft=(bar_rect.right + 10, bar_rect.centery))
             # Verhindere Überlappung mit Bildschirmrand rechts
             if time_text_rect.right > screen_width - 5:
                 time_text_rect.right = screen_width - 5
             screen.blit(time_text, time_text_rect)


        # Unteres Rechteck (Bild oder Fallback)
        if use_lower_panel_bg_image and scaled_lower_panel_bg:
             screen.blit(scaled_lower_panel_bg, center_rect.topleft)
        else:
             pygame.draw.rect(screen, CENTER_RECT_COLOR, center_rect) # Fallback

        # NEU: Animation zeichnen (wenn aktiv)
        if show_animation and animation_frames: # Nur zeichnen, wenn Frames geladen wurden
            current_frame_image = animation_frames[animation_index]
            # Positioniere mittig über dem unteren Rechteck mit Abstand
            anim_padding_bottom = 10
            frame_rect = current_frame_image.get_rect(midbottom=(center_rect.centerx, center_rect.top - anim_padding_bottom))
            screen.blit(current_frame_image, frame_rect)

        # Interaktionskreis (Bild oder Fallback)
        if use_interaction_button_images and scaled_interaction_button_up and scaled_interaction_button_down:
            current_button_image = scaled_interaction_button_down if circle_held_down else scaled_interaction_button_up
            button_rect = current_button_image.get_rect(center=interaction_circle_pos)
            screen.blit(current_button_image, button_rect)
        else:
            # Fallback: Kreis zeichnen
            circle_color_to_draw = INTERACTION_CIRCLE_COLOR # Keine Farbänderung mehr bei Cooldown
            pygame.draw.circle(screen, circle_color_to_draw, interaction_circle_pos, interaction_circle_radius)
            if circle_held_down: # Visuelles Feedback für Drücken
                 pygame.draw.circle(screen, WHITE, interaction_circle_pos, interaction_circle_radius, 2)


        # Statusanzeige (unterhalb des Balkens)
        if font:
            crack_text = font.render(f"Crack: {current_crack}", True, RED)
            screen.blit(crack_text, (status_pos_x, status_pos_y))
        if info_font:
            pills_text_str = f"Pillen: {current_pills}"
            liquid_text_str = f"Liquid: {current_liquid}"
            pills_text = info_font.render(pills_text_str, True, BLACK)
            liquid_text = info_font.render(liquid_text_str, True, BLACK)
            screen.blit(pills_text, (status_pos_x, resource_pos_y))
            screen.blit(liquid_text, (status_pos_x, resource_pos_y + info_font_size + 5))

        # Zurück Button (Bild oder Fallback)
        if back_button_rect:
            current_back_img = scaled_back_button_bg # Standard
            is_hovering = back_button_rect.collidepoint(mouse_pos)
            if is_hovering and use_back_button_images and scaled_back_button_hover:
                 current_back_img = scaled_back_button_hover
            elif not use_back_button_images: # Fallback Zeichnung
                 btn_color = DARK_GRAY if is_hovering else GRAY
                 pygame.draw.rect(screen, btn_color, back_button_rect)
                 pygame.draw.rect(screen, BLACK, back_button_rect, 2)

            if use_back_button_images and current_back_img:
                 screen.blit(current_back_img, back_button_rect.topleft)

            # Text immer noch zeichnen (über das Bild/Fallback)
            if back_text_surface and back_button_font:
                text_rect = back_text_surface.get_rect(center=back_button_rect.center)
                screen.blit(back_text_surface, text_rect)


        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Spiel-Schleife ---
    print("INFO (cockCrack V6 Bilder & Anim): Minispiel-Schleife beendet.")

    # Gebe die finalen Werte zurück an das Hauptspiel
    return current_pills, current_liquid, current_crack

# --- Ende der run_cock_crack_game Funktion ---

# --- Standalone Code (Angepasst für neues Layout) ---
if __name__ == "__main__":
    print("INFO: cockCrack.py (V6 Bilder & Anim) wird eigenständig ausgeführt.")
    print("      Ersetzt Formen durch PNGs, fügt Animation hinzu.")
    print("      Benötigte Dummy-Bilder: bar_blue_bg.png, bar_green_overlay.png, ")
    print("          arrow_indicator.png, lower_panel_bg.png, interaction_button_up.png, ")
    print("          interaction_button_down.png, back_button_bg.png, back_button_hover.png, ")
    print("          anim_frame_1.png, anim_frame_2.png, anim_frame_3.png ...")

    pygame.init()
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (Standalone Init): Mixer fehlgeschlagen: {e}")

    try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
    except Exception: _sw = 800; _sh = 600
    standalone_screen = pygame.display.set_mode((_sw, _sh), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("CockCrack Minispiel (V6 Bilder & Anim - Standalone)")

    start_pills_sa = 5 # Mehr zum Testen
    start_liquid_sa = 5 # Mehr zum Testen
    start_crack_sa = 0
    liquid_name_sa = "WasserID"
    pills_name_sa = "TafelganID"

    print(f"\n--- Starte Standalone mit: Pills={start_pills_sa}, Liquid={start_liquid_sa}, Crack={start_crack_sa} ---\n")

    try:
        final_pills, final_liquid, final_crack = run_cock_crack_game(
            standalone_screen, start_pills_sa, start_liquid_sa, start_crack_sa, liquid_name_sa, pills_name_sa
        )
        print(f"\n--- Standalone Beendet. Ergebnis: ---")
        print(f"  Verbleibende Pillen: {final_pills}")
        print(f"  Verbleibende Flüssigkeit: {final_liquid}")
        print(f"  Erzeugtes Crack: {final_crack}")
        print("-------------------------------------\n")

    except Exception as e_main:
        print(f"FEHLER in Standalone: {e_main}")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()
# --- Ende Standalone-Code ---