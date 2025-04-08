# -*- coding: utf-8 -*-
import pygame
import sys
import math

# Initialisierung von Pygame
pygame.init()

# --- Referenz-Dimensionen ---
ref_w = 800.0
ref_h = 600.0

# --- Bildschirmgrösse automatisch erkennen ---
# Dieser Block versucht sofort, die Info zu holen. Wenn es fehlschlägt,
# werden sofort die Standardwerte genutzt. Ein Warten ist nicht nötig.
try:
    display_info = pygame.display.Info()
    SCREEN_WIDTH = display_info.current_w
    SCREEN_HEIGHT = display_info.current_h
    print(f"Erkannte Bildschirmgröße: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
except pygame.error as e:
    print(f"Fehler beim Abrufen der Bildschirmgröße: {e}. Nutze Standardwerte 800x600.")
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
# --- Ende Bildschirmgrösse ---

# --- Fenstermodus wählen ---
# Die erkannte/Standard-Grösse wird verwendet.

# !!! WICHTIGER HINWEIS FÜR ANDROID !!!
# Wenn das Spiel auf Android trotz korrekter Auflösungserkennung zu klein ist,
# liegt das an der hohen Pixeldichte (DPI).
# AKTIVIERE DANN DIE NÄCHSTE ZEILE (entferne '#' und das Flag pygame.SCALED):
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT) ) # Momentan OHNE Skalierung
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED) # MIT Skalierung (testen!)
# ODER Vollbild mit Skalierung:
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.SCALED)
# ---------------------------------------

pygame.display.set_caption("Viereck Packer V10.1 - Proportional + DPI Hinweis")

# Farben (RGB)
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)

# --- Proportionale Berechnung ---
# Diese Berechnungen finden *nach* der Ermittlung von SCREEN_WIDTH/HEIGHT statt
# und verwenden diese Werte, um alles proportional zu skalieren.
target_width = max(1, int(SCREEN_WIDTH * (150 / ref_w)))
target_height = max(1, int(SCREEN_HEIGHT * (200 / ref_h)))
# ... (alle anderen proportionalen Berechnungen wie in V10)...
target_padding_right = max(1, int(SCREEN_WIDTH * (50 / ref_w)))
target_padding_bottom = max(1, int(SCREEN_HEIGHT * (100 / ref_h)))
target_x = SCREEN_WIDTH - target_width - target_padding_right
target_y = SCREEN_HEIGHT - target_height - target_padding_bottom
target_rect = pygame.Rect(target_x, target_y, target_width, target_height)

swipe_line_height = max(1, int(SCREEN_HEIGHT * (12 / ref_h)))
swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height)
min_swipe_distance = swipe_line_rect.width * 0.75

small_size = max(1, int(SCREEN_WIDTH * (40 / ref_w)))
start_padding_left = max(1, int(SCREEN_WIDTH * (100 / ref_w)))
start_padding_top = max(1, int(SCREEN_HEIGHT * (50 / ref_h)))
start_pos = [start_padding_left, start_padding_top]
small_rect = pygame.Rect(start_pos[0], start_pos[1], small_size, small_size)

gravity = max(1, int(SCREEN_HEIGHT * (5 / ref_h)))
font_size = max(12, int(SCREEN_HEIGHT * (36 / ref_h)))
try: font = pygame.font.SysFont("arial", font_size)
except pygame.error: font = pygame.font.Font(None, font_size)

score_pos_x = max(1, int(SCREEN_WIDTH * (10 / ref_w)))
score_pos_y = max(1, int(SCREEN_HEIGHT * (10 / ref_h)))
# --- Ende Proportionale Berechnung ---

# Spielzustands-Variablen
dragging, is_falling, offset_x, offset_y, score = False, False, 0, 0, 0
ready_for_swipe, is_swiping, swipe_start_x, swipe_current_x = False, False, None, None
clock = pygame.time.Clock()

# --- Spiel-Loop (Logik unverändert) ---
running = True
while running:
    # Event Handling...
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
                if swipe_line_rect.collidepoint(event.pos):
                    if swipe_start_x is not None:
                         swiped_distance = abs(swipe_current_x - swipe_start_x)
                         if swiped_distance >= min_swipe_distance:
                             score += 1; small_rect.topleft = tuple(start_pos)
                             ready_for_swipe, is_falling, is_swiping, swipe_start_x, swipe_current_x = False, False, False, None, None
                elif not swipe_line_rect.collidepoint(event.pos): is_swiping, swipe_start_x, swipe_current_x = False, None, None
            elif dragging:
                old_rect = small_rect.copy()
                potential_x, potential_y = event.pos[0] + offset_x, event.pos[1] + offset_y
                small_rect.topleft = (potential_x, potential_y)
                if small_rect.colliderect(target_rect):
                     if old_rect.right <= target_rect.left and small_rect.right > target_rect.left and small_rect.bottom > target_rect.top: small_rect.right = target_rect.left
                     elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right and small_rect.bottom > target_rect.top: small_rect.left = target_rect.right
                     elif old_rect.bottom <= target_rect.bottom and small_rect.bottom > target_rect.bottom and small_rect.right > target_rect.left and small_rect.left < target_rect.right: small_rect.bottom = target_rect.bottom
                     elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom and small_rect.right > target_rect.left and small_rect.left < target_rect.right: small_rect.top = target_rect.bottom

    # Spiel-Logik / Physik (Fallen)...
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

    # Zeichnen...
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, target_rect)
    if ready_for_swipe:
        pygame.draw.rect(screen, GREEN, swipe_line_rect)
        if is_swiping and swipe_start_x is not None and swipe_current_x is not None:
            orange_rect_x = min(swipe_start_x, swipe_current_x)
            orange_rect_width = abs(swipe_current_x - swipe_start_x)
            orange_rect_x = max(swipe_line_rect.left, orange_rect_x)
            orange_rect_right = min(swipe_line_rect.right, orange_rect_x + orange_rect_width)
            orange_rect_width = orange_rect_right - orange_rect_x
            if orange_rect_width > 0:
                orange_progress_rect = pygame.Rect(orange_rect_x, swipe_line_rect.y, orange_rect_width, swipe_line_rect.height)
                pygame.draw.rect(screen, ORANGE, orange_progress_rect)
    pygame.draw.rect(screen, RED, small_rect)
    score_text = font.render(f"Punkte: {score}", True, BLACK)
    screen.blit(score_text, (score_pos_x, score_pos_y))
    pygame.display.flip()
    clock.tick(60)

# Pygame beenden
pygame.quit()
sys.exit()
