# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os # os wird für Pfadkorrektur und Android-Check benötigt

# Initialisierung von Pygame
pygame.init()

# --- Referenz-Dimensionen ---
ref_w = 800.0
ref_h = 600.0

# --- Bildschirmgrösse automatisch erkennen ---
try:
    display_info = pygame.display.Info()
    detected_width = display_info.current_w
    detected_height = display_info.current_h
    print(f"Erkannte Bildschirmgröße: {detected_width}x{detected_height}")
except pygame.error as e:
    print(f"Fehler beim Abrufen der Bildschirmgröße: {e}. Nutze Standardwerte 800x600.")
    detected_width = 800
    detected_height = 600

# --- Plattform prüfen ---
is_android = False
try:
    import android
    is_android = True
    print("Android-Plattform erkannt (basierend auf 'import android').")
except ImportError:
    print("Nicht-Android-Plattform erkannt.")
    if "ANDROID_ARGUMENT" in os.environ:
        is_android = True
        print("Android-Plattform erkannt (basierend auf Umgebungsvariable).")

# --- Breite/Höhe für Berechnungen festlegen ---
# WICHTIG: Geht davon aus, dass Orientierung extern auf Landscape gesetzt ist.
CALC_WIDTH = detected_width
CALC_HEIGHT = detected_height
print(f"Nutze Bildschirmgröße für Berechnungen (erwartet Landscape): {CALC_WIDTH}x{CALC_HEIGHT}")

# --- Fenstermodus wählen ---
screen = pygame.display.set_mode((detected_width, detected_height), pygame.SCALED)
pygame.display.set_caption("Viereck Packer V11.8 - Target Image") # Versionsnummer erhöht

# Farben (RGB)
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)

# --- Proportionale Berechnung ---
# Ziel-Rechteck (Position und Größe)
target_width = max(1, int(CALC_WIDTH * (150 / ref_w)))
target_height = max(1, int(CALC_HEIGHT * (200 / ref_h)))
target_padding_right = max(1, int(CALC_WIDTH * (50 / ref_w)))
target_padding_bottom = max(1, int(CALC_HEIGHT * (100 / ref_h)))
target_x = CALC_WIDTH - target_width - target_padding_right
target_y = CALC_HEIGHT - target_height - target_padding_bottom
target_rect = pygame.Rect(target_x, target_y, target_width, target_height)

# Swipe-Linie
base_swipe_line_height = max(1, int(CALC_HEIGHT * (12 / ref_h)))
if is_android:
    swipe_line_height = base_swipe_line_height * 3
    print(f"Android: Erhöhe Swipe-Linien-Höhe auf {swipe_line_height} (Basis: {base_swipe_line_height})")
else:
    swipe_line_height = base_swipe_line_height
swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height)
min_swipe_distance = swipe_line_rect.width * 0.85

# Kleines (rotes) Viereck
small_size = max(1, int(CALC_WIDTH * (80 / ref_w)))
start_padding_left = max(1, int(CALC_WIDTH * (100 / ref_w)))
start_padding_top = max(1, int(CALC_HEIGHT * (400 / ref_h)))
start_pos = [start_padding_left, start_padding_top]
if small_size <= 0:
     print(f"WARNUNG: Berechnete small_size ({small_size}) ist <= 0. Setze auf 1.")
     small_size = 1
small_rect = pygame.Rect(start_pos[0], start_pos[1], small_size, small_size)

# Physik und Schrift
gravity = max(1, int(CALC_HEIGHT * (6 / ref_h)))
font_size = max(12, int(CALC_HEIGHT * (36 / ref_h)))
try:
    font = pygame.font.SysFont("arial", font_size)
except pygame.error:
    font = pygame.font.Font(None, font_size)

score_pos_x = max(1, int(CALC_WIDTH * (10 / ref_w)))
score_pos_y = max(1, int(CALC_HEIGHT * (10 / ref_h)))
# --- Ende Proportionale Berechnung ---

# --- Gemeinsamer Pfad für Bilder ---
image_datafolder = "data"
image_folder = "bilder"
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.path.abspath(".")
    print("WARNUNG: '__file__' nicht gefunden, nutze aktuelles Arbeitsverzeichnis als Basis.")

# --- Bild für kleines Viereck laden (butt.png) ---
small_image = None
use_small_image = False # Umbenannt von use_image zur Klarheit
small_image_filename = "butt.png"
small_image_path = os.path.join(script_dir, image_datafolder, image_folder, small_image_filename)

print(f"Versuche kleines Bild zu laden von: {small_image_path}")
try:
    original_small_image = pygame.image.load(small_image_path).convert_alpha()
    print(f"DEBUG: Originalbild '{small_image_path}' geladen.")
    if small_size > 0:
        small_image = pygame.transform.smoothscale(original_small_image, (small_size, small_size))
        use_small_image = True
        print(f"Kleines Bild erfolgreich skaliert auf {small_size}x{small_size}.")
    else:
         print(f"WARNUNG: small_size ({small_size}) ungültig. Kein kleines Bild geladen.")
         use_small_image = False
except (pygame.error, FileNotFoundError) as e:
    print(f"WARNUNG: Fehler beim Laden/Skalieren des kleinen Bildes '{small_image_path}': {e}")
    print("-> Zeichne stattdessen rotes Viereck.")
    use_small_image = False
    small_image = None
# --- Ende Bild für kleines Viereck ---

# --- Bild für Ziel-Viereck laden (grip.png) ---
target_image = None
use_target_image = False
target_image_filename = "grip.png"
target_image_path = os.path.join(script_dir, image_datafolder, image_folder, target_image_filename)

print(f"Versuche Ziel-Bild zu laden von: {target_image_path}")
try:
    original_target_image = pygame.image.load(target_image_path).convert_alpha()
    print(f"DEBUG: Originalbild '{target_image_path}' geladen.")
    # Skaliere auf die Größe des target_rect
    if target_rect.width > 0 and target_rect.height > 0:
        target_image = pygame.transform.smoothscale(original_target_image, (target_rect.width, target_rect.height))
        use_target_image = True
        print(f"Ziel-Bild erfolgreich skaliert auf {target_rect.width}x{target_rect.height}.")
    else:
         print(f"WARNUNG: target size ({target_rect.width}x{target_rect.height}) ungültig. Kein Ziel-Bild geladen.")
         use_target_image = False
except (pygame.error, FileNotFoundError) as e:
    print(f"WARNUNG: Fehler beim Laden/Skalieren des Ziel-Bildes '{target_image_path}': {e}")
    print("-> Zeichne stattdessen blaues Viereck.")
    use_target_image = False
    target_image = None
# --- Ende Bild für Ziel-Viereck ---


# Spielzustands-Variablen
dragging, is_falling, offset_x, offset_y, score = False, False, 0, 0, 0
ready_for_swipe, is_swiping, swipe_start_x, swipe_current_x = False, False, None, None
clock = pygame.time.Clock()

# --- Spiel-Loop ---
running = True
while running:
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Linke Maustaste / Touch
                if ready_for_swipe and swipe_line_rect.collidepoint(event.pos):
                    is_swiping = True
                    swipe_start_x = event.pos[0]
                    swipe_current_x = event.pos[0]
                    dragging = False
                elif small_rect.collidepoint(event.pos) and not is_swiping:
                    dragging = True
                    is_falling = False
                    ready_for_swipe = False
                    is_swiping = False
                    swipe_start_x = None
                    swipe_current_x = None
                    offset_x = small_rect.x - event.pos[0]
                    offset_y = small_rect.y - event.pos[1]
                else:
                    pass

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Linke Maustaste / Touch losgelassen
                if is_swiping:
                    is_swiping = False
                    swipe_start_x = None
                    swipe_current_x = None
                    if not target_rect.contains(small_rect):
                         ready_for_swipe = False
                         is_falling = True

                elif dragging:
                    dragging = False
                    if target_rect.contains(small_rect):
                        ready_for_swipe = True
                        is_falling = False
                    else:
                        ready_for_swipe = False
                        is_falling = True

        elif event.type == pygame.MOUSEMOTION:
            if is_swiping:
                swipe_current_x = event.pos[0]
                if swipe_line_rect.collidepoint(event.pos):
                    if swipe_start_x is not None:
                        swiped_distance = abs(swipe_current_x - swipe_start_x)
                        if swiped_distance >= min_swipe_distance:
                            score += 1
                            small_rect.topleft = tuple(start_pos)
                            ready_for_swipe = False
                            is_falling = False
                            is_swiping = False
                            swipe_start_x = None
                            swipe_current_x = None
                else:
                    is_swiping = False
                    swipe_start_x = None
                    swipe_current_x = None
                    if not target_rect.contains(small_rect):
                         ready_for_swipe = False
                         is_falling = True

            elif dragging:
                old_rect = small_rect.copy()
                potential_x = event.pos[0] + offset_x
                potential_y = event.pos[1] + offset_y
                small_rect.topleft = (potential_x, potential_y)

                # Kollision kleines Viereck mit Ziel-Rechteck (nur von aussen)
                if not target_rect.contains(old_rect) and small_rect.colliderect(target_rect):
                    if old_rect.right <= target_rect.left and small_rect.right > target_rect.left:
                        small_rect.right = target_rect.left
                    elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right:
                        small_rect.left = target_rect.right
                    elif old_rect.bottom <= target_rect.top and small_rect.bottom > target_rect.top:
                         small_rect.bottom = target_rect.top
                    elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom:
                         small_rect.top = target_rect.bottom

                # Begrenzung auf den Bildschirm
                if small_rect.left < 0: small_rect.left = 0
                if small_rect.right > CALC_WIDTH: small_rect.right = CALC_WIDTH
                if small_rect.top < 0: small_rect.top = 0
                if small_rect.bottom > CALC_HEIGHT: small_rect.bottom = CALC_HEIGHT


    # Spiel-Logik / Physik (Fallen)
    if is_falling and not dragging and not ready_for_swipe and not is_swiping:
        potential_y = small_rect.y + gravity
        potential_rect = small_rect.copy()
        potential_rect.y = potential_y

        collides_with_target_bottom = (
            potential_rect.bottom > target_rect.bottom and
            small_rect.bottom <= target_rect.bottom and
            potential_rect.right > target_rect.left and
            potential_rect.left < target_rect.right
        )

        if collides_with_target_bottom:
            small_rect.bottom = target_rect.bottom
            is_falling = False
            if target_rect.contains(small_rect):
                ready_for_swipe = True
            else:
                ready_for_swipe = False
        else:
            if potential_rect.bottom >= CALC_HEIGHT:
                small_rect.topleft = tuple(start_pos)
                is_falling = False
                ready_for_swipe = False
            else:
                small_rect.y = potential_y

    # Zustandskorrektur: Wenn bereit zum Swipen, aber Objekt nicht mehr im Ziel (und nicht gedragged)
    if ready_for_swipe and not target_rect.contains(small_rect) and not is_swiping:
         if not dragging:
              ready_for_swipe = False
              is_falling = True

    # --- Zeichnen ---
    screen.fill(WHITE)

    # Ziel: Bild oder Fallback (blaues Viereck) zeichnen
    if use_target_image and target_image is not None:
        screen.blit(target_image, target_rect.topleft)
    else:
        # Fallback, wenn Bild nicht geladen wurde
        pygame.draw.rect(screen, BLUE, target_rect)

    # Swipe-Linie und Fortschritt zeichnen (nur wenn bereit)
    if ready_for_swipe:
        pygame.draw.rect(screen, GREEN, swipe_line_rect) # Grüne Basislinie
        if is_swiping and swipe_start_x is not None and swipe_current_x is not None:
            # Oranger Fortschrittsbalken
            orange_rect_x = min(swipe_start_x, swipe_current_x)
            orange_rect_width = abs(swipe_current_x - swipe_start_x)
            orange_rect_x = max(swipe_line_rect.left, orange_rect_x)
            orange_rect_right = min(swipe_line_rect.right, orange_rect_x + orange_rect_width)
            orange_rect_width = orange_rect_right - orange_rect_x
            if orange_rect_width > 0:
                orange_progress_rect = pygame.Rect(orange_rect_x, swipe_line_rect.y, orange_rect_width, swipe_line_rect.height)
                pygame.draw.rect(screen, ORANGE, orange_progress_rect)

    # Kleines Viereck: Bild oder Fallback (rotes Viereck) zeichnen
    if use_small_image and small_image is not None:
        screen.blit(small_image, small_rect.topleft)
    else:
        # Fallback, wenn Bild nicht geladen wurde
        if small_rect:
             pygame.draw.rect(screen, RED, small_rect)

    # Punktestand anzeigen
    score_text = font.render(f"Punkte: {score}", True, BLACK)
    screen.blit(score_text, (score_pos_x, score_pos_y))

    # Bildschirm aktualisieren
    pygame.display.flip()

    # Framerate begrenzen
    clock.tick(60)

# Pygame beenden
pygame.quit()
sys.exit()