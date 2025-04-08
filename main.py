# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os

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

# --- Plattform prüfen und ggf. H/W für Berechnungen tauschen ---
SCREEN_WIDTH = detected_width
SCREEN_HEIGHT = detected_height
is_android = False
try:
    import android
    is_android = True
    print("Android-Plattform erkannt.")
except ImportError:
    print("Nicht-Android-Plattform erkannt.")

if is_android and detected_height > detected_width:
    print(f"Tausche Breite({detected_width}) und Höhe({detected_height}) für Landscape-Berechnung.")
    SCREEN_WIDTH = detected_height
    SCREEN_HEIGHT = detected_width
else:
    SCREEN_WIDTH = detected_width
    SCREEN_HEIGHT = detected_height
# --- Ende Plattformprüfung ---


# --- Fenstermodus wählen ---
# Verwende die original erkannten oder für die Berechnung getauschten Dimensionen.
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED) # Mit SCALED empfohlen

pygame.display.set_caption("Viereck Packer V11.5 - Dickere Android Swipe-Linie")

# Farben (RGB)
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)

# --- Proportionale Berechnung ---
target_width = max(1, int(SCREEN_WIDTH * (150 / ref_w)))
target_height = max(1, int(SCREEN_HEIGHT * (200 / ref_h)))
target_padding_right = max(1, int(SCREEN_WIDTH * (50 / ref_w)))
target_padding_bottom = max(1, int(SCREEN_HEIGHT * (100 / ref_h)))
target_x = SCREEN_WIDTH - target_width - target_padding_right
target_y = SCREEN_HEIGHT - target_height - target_padding_bottom
target_rect = pygame.Rect(target_x, target_y, target_width, target_height)

# --- Swipe-Linien-Höhe berechnen (mit Android-Anpassung) ---
# 1. Berechne die normale proportionale Höhe
base_swipe_line_height = max(1, int(SCREEN_HEIGHT * (12 / ref_h)))
# 2. Verdreifache die Höhe, wenn es Android ist
if is_android:
    swipe_line_height = base_swipe_line_height * 3
    print(f"Android: Erhöhe Swipe-Linien-Höhe auf {swipe_line_height} (Basis: {base_swipe_line_height})")
else:
    swipe_line_height = base_swipe_line_height # Normale Höhe für andere Systeme
# --- Ende Swipe-Höhe ---

# Erstelle das Swipe-Rechteck mit der (ggf. angepassten) Höhe
swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height)
min_swipe_distance = swipe_line_rect.width * 0.85 # Unverändert (basiert auf Breite)

# Restliche proportionale Berechnungen...
small_size = max(1, int(SCREEN_WIDTH * (80 / ref_w)))
start_padding_left = max(1, int(SCREEN_WIDTH * (100 / ref_w)))
start_padding_top = max(1, int(SCREEN_HEIGHT * (400 / ref_h)))
start_pos = [start_padding_left, start_padding_top]
small_rect = pygame.Rect(start_pos[0], start_pos[1], small_size, small_size)

gravity = max(1, int(SCREEN_HEIGHT * (6 / ref_h)))
font_size = max(12, int(SCREEN_HEIGHT * (36 / ref_h)))
try: font = pygame.font.SysFont("arial", font_size)
except pygame.error: font = pygame.font.Font(None, font_size)

score_pos_x = max(1, int(SCREEN_WIDTH * (10 / ref_w)))
score_pos_y = max(1, int(SCREEN_HEIGHT * (10 / ref_h)))
# --- Ende Proportionale Berechnung ---

# --- Bild laden ---
# (Code unverändert von V11.4)
small_image = None
use_image = False
image_filename = "butt.png"
image_datafolder = "data"
image_folder = "bilder"
image_path = os.path.join(image_datafolder, image_folder, image_filename)
print(f"Versuche Bild zu laden von: {image_path}")
try:
    original_small_image = pygame.image.load(image_path).convert_alpha()
    original_size = original_small_image.get_size()
    print(f"DEBUG: Originalbild '{image_path}' geladen. Grösse: {original_size}")
    small_image = pygame.transform.smoothscale(original_small_image, (small_size, small_size))
    scaled_size = small_image.get_size()
    print(f"DEBUG: Bild skaliert auf: {scaled_size}")
    if abs(scaled_size[0] - small_size) <= 1 and abs(scaled_size[1] - small_size) <= 1:
         use_image = True
         print(f"Bild '{image_path}' erfolgreich geladen und Skalierung scheint OK.")
    else:
         print(f"WARNUNG: Skalierung fehlgeschlagen ({scaled_size}). Nutze Fallback.")
         use_image = False
except (pygame.error, FileNotFoundError) as e:
    print(f"WARNUNG: Fehler beim Laden/Skalieren des Bildes '{image_path}': {e}")
    print("-> Zeichne stattdessen rotes Viereck.")
    use_image = False
# --- Ende Bild laden ---

# Spielzustands-Variablen
dragging, is_falling, offset_x, offset_y, score = False, False, 0, 0, 0
ready_for_swipe, is_swiping, swipe_start_x, swipe_current_x = False, False, None, None
clock = pygame.time.Clock()

# --- Spiel-Loop ---
running = True
while running:
    # Event Handling... (unverändert)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if ready_for_swipe and swipe_line_rect.collidepoint(event.pos):
                    is_swiping, swipe_start_x, swipe_current_x, dragging = True, event.pos[0], event.pos[0], False
                elif small_rect.collidepoint(event.pos):
                    dragging, is_falling, ready_for_swipe, is_swiping = True, False, False, False
                    swipe_start_x, swipe_current_x = None, None
                    offset_x, offset_y = small_rect.x - event.pos[0], small_rect.y - event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if is_swiping: is_swiping, swipe_start_x, swipe_current_x = False, None, None
                elif dragging:
                    dragging = False
                    if target_rect.contains(small_rect): ready_for_swipe, is_falling = True, False
                    else: is_falling, ready_for_swipe = True, False
        elif event.type == pygame.MOUSEMOTION:
            if is_swiping:
                swipe_current_x = event.pos[0]
                # Prüfe Kollision mit dem (jetzt ggf. höheren) swipe_line_rect
                if swipe_line_rect.collidepoint(event.pos):
                    if swipe_start_x is not None:
                         swiped_distance = abs(swipe_current_x - swipe_start_x)
                         if swiped_distance >= min_swipe_distance:
                             score += 1; small_rect.topleft = tuple(start_pos)
                             ready_for_swipe, is_falling, is_swiping, swipe_start_x, swipe_current_x = False, False, False, None, None
                elif not swipe_line_rect.collidepoint(event.pos):
                    is_swiping, swipe_start_x, swipe_current_x = False, None, None
            elif dragging:
                old_rect = small_rect.copy()
                potential_x, potential_y = event.pos[0] + offset_x, event.pos[1] + offset_y
                small_rect.topleft = (potential_x, potential_y)
                if small_rect.colliderect(target_rect):
                     # Kollisionslogik unverändert
                     if old_rect.right <= target_rect.left and small_rect.right > target_rect.left and small_rect.bottom > target_rect.top: small_rect.right = target_rect.left
                     elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right and small_rect.bottom > target_rect.top: small_rect.left = target_rect.right
                     elif old_rect.bottom <= target_rect.bottom and small_rect.bottom > target_rect.bottom and small_rect.right > target_rect.left and small_rect.left < target_rect.right: small_rect.bottom = target_rect.bottom
                     elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom and small_rect.right > target_rect.left and small_rect.left < target_rect.right: small_rect.top = target_rect.bottom

    # Spiel-Logik / Physik (Fallen)... (unverändert)
    if is_falling and not dragging and not ready_for_swipe and not is_swiping:
        potential_y = small_rect.y + gravity
        potential_rect = small_rect.copy(); potential_rect.y = potential_y
        collides_with_target_bottom = ( potential_rect.bottom > target_rect.bottom and small_rect.bottom <= target_rect.bottom and potential_rect.right > target_rect.left and potential_rect.left < target_rect.right )
        if collides_with_target_bottom:
            small_rect.bottom = target_rect.bottom; is_falling = False
            if target_rect.contains(small_rect): ready_for_swipe = True
            else: ready_for_swipe = False
        else:
            if potential_rect.bottom >= SCREEN_HEIGHT:
                 small_rect.topleft = tuple(start_pos); is_falling, ready_for_swipe = False, False
            else: small_rect.y = potential_y
    if ready_for_swipe and not target_rect.contains(small_rect) and not dragging and not is_swiping:
        ready_for_swipe, is_falling = False, True

    # --- Zeichnen ---
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, target_rect) # Ziel

    # Swipe-Linie und Fortschritt zeichnen
    if ready_for_swipe:
        # Zeichne die grüne Linie (jetzt ggf. höher auf Android)
        pygame.draw.rect(screen, GREEN, swipe_line_rect)
        if is_swiping and swipe_start_x is not None and swipe_current_x is not None:
            # Fortschrittsbalken (orange) füllt die (ggf. höhere) Linie
            orange_rect_x = min(swipe_start_x, swipe_current_x)
            orange_rect_width = abs(swipe_current_x - swipe_start_x)
            orange_rect_x = max(swipe_line_rect.left, orange_rect_x)
            orange_rect_right = min(swipe_line_rect.right, orange_rect_x + orange_rect_width)
            orange_rect_width = orange_rect_right - orange_rect_x
            if orange_rect_width > 0:
                # Nutzt swipe_line_rect.height, die jetzt auf Android grösser sein kann
                orange_progress_rect = pygame.Rect(orange_rect_x, swipe_line_rect.y, orange_rect_width, swipe_line_rect.height)
                pygame.draw.rect(screen, ORANGE, orange_progress_rect)

    # Bild oder Fallback zeichnen (unverändert)
    if use_image and small_image is not None:
        screen.blit(small_image, small_rect.topleft)
    else:
        pygame.draw.rect(screen, RED, small_rect)

    # Punktestand anzeigen (unverändert)
    score_text = font.render(f"Punkte: {score}", True, BLACK)
    screen.blit(score_text, (score_pos_x, score_pos_y))

    pygame.display.flip()
    clock.tick(60)

# Pygame beenden
pygame.quit()
sys.exit()