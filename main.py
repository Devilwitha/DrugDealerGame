# -*- coding: utf-8 -*-
import pygame
import sys
import os
import traceback

# Importiere das Minispiel-Skript
zipWeedGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.zipWeed.zipWeed")
    import data.miniGame.zipWeed.zipWeed as zipWeedGame # KORREKTER IMPORTPFAD
    print(f"DEBUG: Import von {zipWeedGame.__name__} erfolgreich.")
except ImportError as e_imp:
    print(f"FEHLER: Konnte das Minispiel-Modul nicht importieren: {e_imp}")
    print("Stelle sicher, dass die Pfade korrekt sind und __init__.py Dateien in 'data', 'data/miniGame' UND 'data/miniGame/zipWeed' existieren.")
    traceback.print_exc()
    sys.exit()
except Exception as e:
    print(f"FEHLER beim Import: {e}")
    traceback.print_exc()
    sys.exit()

# --- Grundlegende Pygame Initialisierung ---
pygame.init()

# Bildschirmgröße
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
try:
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
    print(f"Hauptmenü Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
except Exception:
    print(f"Hauptmenü nutzt Standardgröße: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
pygame.display.set_caption("Hauptmenü - DrugsDealerGame")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)

# --- Button Definition (Proportional) ---
BUTTON_WIDTH_PERCENT = 0.40 # 40% der Bildschirmbreite
BUTTON_HEIGHT_PERCENT = 0.15 # 15% der Bildschirmhöhe
FONT_SIZE_REF_H = 600.0 # Referenzhöhe für Schriftgröße
BASE_FONT_SIZE = 40 # Schriftgröße bei Referenzhöhe

button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2
button_y = (SCREEN_HEIGHT - button_height) // 2
button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

# Proportionale Schriftgröße
button_font_size = max(20, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text_surface = None
try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    button_text = "Starte ZipWeed Minispiel"
    text_surface = button_font.render(button_text, True, BLACK)
except Exception as e_font:
    print(f"FEHLER beim Laden/Rendern der Button-Schriftart: {e_font}")
    # Fallback, falls Font nicht geht
    try:
        button_font = pygame.font.Font(None, int(button_font_size * 1.2)) # Fallback Font etwas größer
        text_surface = button_font.render(button_text, True, BLACK)
    except Exception as e_font_fallback:
         print(f"FEHLER: Konnte auch Fallback-Schriftart nicht laden: {e_font_fallback}")
         text_surface = None


clock = pygame.time.Clock()

# --- Hauptschleife des Menüs ---
menu_running = True
while menu_running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            menu_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                 menu_running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if button_rect.collidepoint(event.pos):
                    print("INFO: Starte ZipWeed Minispiel...")
                    if zipWeedGame:
                        try:
                            zipWeedGame.run_zip_weed_game(screen)
                            print("INFO: Zurück im Hauptmenü.")
                        except AttributeError as e_attr:
                             print(f"FEHLER (AttributeError): {e_attr}")
                             print(">>> Funktion 'run_zip_weed_game' immer noch nicht gefunden!")
                             print(">>> Bitte PRÜFE den Inhalt von data/miniGame/zipWeed/zipWeed.py!")
                             traceback.print_exc()
                        except Exception as e_game:
                            print(f"FEHLER beim Ausführen des Minispiels: {e_game}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: Minispiel-Modul (zipWeedGame) wurde nicht erfolgreich importiert.")

    # Zeichnen
    screen.fill(WHITE)

    # Button zeichnen
    button_color = GRAY
    if button_rect.collidepoint(mouse_pos):
        button_color = DARK_GRAY

    pygame.draw.rect(screen, button_color, button_rect)
    pygame.draw.rect(screen, BLACK, button_rect, 3)
    if text_surface:
        # Text im Button zentrieren
        text_rect = text_surface.get_rect(center=button_rect.center)
        screen.blit(text_surface, text_rect.topleft)

    pygame.display.flip()
    clock.tick(30)

# Pygame beenden
pygame.quit()
sys.exit()