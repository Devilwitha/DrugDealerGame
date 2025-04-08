# -*- coding: utf-8 -*-
import pygame
import sys
import os
import traceback

# --- Importiere die Minispiel-Skripte ---

# ZipWeed Minispiel
zipWeedGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.zipWeed.zipWeed")
    # KORREKTER IMPORTPFAD FÜR ZIPWEED
    import data.miniGame.zipWeed.zipWeed as zipWeedGame
    print(f"DEBUG: Import von {zipWeedGame.__name__} erfolgreich.")
except ImportError as e_imp_zw:
    print(f"FEHLER: Konnte das ZipWeed-Modul nicht importieren: {e_imp_zw}")
    print("Stelle sicher, dass die Pfade korrekt sind und __init__.py Dateien existieren.")
    traceback.print_exc()
    # Optional: sys.exit() hier, wenn ZipWeed essentiell ist
except Exception as e_zw:
    print(f"FEHLER beim Import von ZipWeed: {e_zw}")
    traceback.print_exc()
    # Optional: sys.exit()

# CockCrack Minispiel
cockCrackGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.cockCrack.cockCrack")
    # KORREKTER IMPORTPFAD FÜR COCKCRACK
    import data.miniGame.cockCrack.cockCrack as cockCrackGame
    print(f"DEBUG: Import von {cockCrackGame.__name__} erfolgreich.")
except ImportError as e_imp_cc:
    print(f"FEHLER: Konnte das CockCrack-Modul nicht importieren: {e_imp_cc}")
    print("Stelle sicher, dass die Pfade korrekt sind und __init__.py Dateien existieren.")
    traceback.print_exc()
    # Hier kein sys.exit(), damit das Menü auch ohne dieses Spiel startet
except Exception as e_cc:
    print(f"FEHLER beim Import von CockCrack: {e_cc}")
    traceback.print_exc()
    # Hier kein sys.exit()

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
BUTTON_WIDTH_PERCENT = 0.40  # 40% der Bildschirmbreite
BUTTON_HEIGHT_PERCENT = 0.12 # 12% der Bildschirmhöhe (etwas kleiner für zwei Buttons)
BUTTON_SPACING_PERCENT = 0.05 # 5% Abstand zwischen Buttons
FONT_SIZE_REF_H = 600.0      # Referenzhöhe für Schriftgröße
BASE_FONT_SIZE = 40          # Schriftgröße bei Referenzhöhe

button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_spacing = int(SCREEN_HEIGHT * BUTTON_SPACING_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2

# Berechne Y-Positionen für zwei Buttons
total_buttons_height = 2 * button_height + button_spacing
button1_y = (SCREEN_HEIGHT - total_buttons_height) // 2
button2_y = button1_y + button_height + button_spacing

button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height) # ZipWeed Button
button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height) # CockCrack Button

# Proportionale Schriftgröße
button_font_size = max(20, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text1_surface = None # Für Button 1
text2_surface = None # Für Button 2
button1_text = "Starte ZipWeed Minispiel"
button2_text = "Starte CockCrack Minispiel"

try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    if button_font:
        text1_surface = button_font.render(button1_text, True, BLACK)
        text2_surface = button_font.render(button2_text, True, BLACK)
except Exception as e_font:
    print(f"FEHLER beim Laden/Rendern der Button-Schriftart: {e_font}")
    # Fallback, falls Font nicht geht
    try:
        # Fallback Font etwas größer
        button_font = pygame.font.Font(None, int(button_font_size * 1.2))
        if button_font:
             text1_surface = button_font.render(button1_text, True, BLACK)
             text2_surface = button_font.render(button2_text, True, BLACK)
    except Exception as e_font_fallback:
        print(f"FEHLER: Konnte auch Fallback-Schriftart nicht laden: {e_font_fallback}")
        text1_surface = None
        text2_surface = None

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
                # Prüfen, ob Button 1 (ZipWeed) geklickt wurde
                if button1_rect.collidepoint(event.pos):
                    print("INFO: Starte ZipWeed Minispiel...")
                    if zipWeedGame:
                        try:
                            # Starte das ZipWeed Spiel
                            zipWeedGame.run_zip_weed_game(screen)
                            print("INFO: Zurück im Hauptmenü.")
                        except AttributeError as e_attr_zw:
                            print(f"FEHLER (AttributeError ZipWeed): {e_attr_zw}")
                            print(">>> Funktion 'run_zip_weed_game' nicht in zipWeedGame gefunden!")
                            print(">>> Bitte PRÜFE den Inhalt von data/miniGame/zipWeed/zipWeed.py!")
                            traceback.print_exc()
                        except Exception as e_game_zw:
                            print(f"FEHLER beim Ausführen des ZipWeed Minispiels: {e_game_zw}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: ZipWeed-Modul (zipWeedGame) wurde nicht erfolgreich importiert.")

                # Prüfen, ob Button 2 (CockCrack) geklickt wurde
                elif button2_rect.collidepoint(event.pos):
                    print("INFO: Starte CockCrack Minispiel...")
                    if cockCrackGame:
                        try:
                            # Starte das CockCrack Spiel
                            # ACHTUNG: Der Funktionsname ist derselbe wie bei ZipWeed laut deinem Skript!
                            # Falls die Funktion in cockCrack.py anders heißt, hier anpassen.
                            cockCrackGame.run_zip_weed_game(screen)
                            print("INFO: Zurück im Hauptmenü.")
                        except AttributeError as e_attr_cc:
                            print(f"FEHLER (AttributeError CockCrack): {e_attr_cc}")
                            print(">>> Funktion 'run_zip_weed_game' NICHT in cockCrackGame gefunden!")
                            print(">>> Bitte PRÜFE den Inhalt von data/miniGame/cockCrack/cockCrack.py!")
                            traceback.print_exc()
                        except Exception as e_game_cc:
                            print(f"FEHLER beim Ausführen des CockCrack Minispiels: {e_game_cc}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: CockCrack-Modul (cockCrackGame) wurde nicht erfolgreich importiert.")


    # Zeichnen
    screen.fill(WHITE)

    # Button 1 (ZipWeed) zeichnen
    button1_color = GRAY
    if button1_rect.collidepoint(mouse_pos):
        button1_color = DARK_GRAY
    pygame.draw.rect(screen, button1_color, button1_rect)
    pygame.draw.rect(screen, BLACK, button1_rect, 3)
    if text1_surface:
        # Text im Button zentrieren
        text1_rect = text1_surface.get_rect(center=button1_rect.center)
        screen.blit(text1_surface, text1_rect.topleft)

    # Button 2 (CockCrack) zeichnen
    button2_color = GRAY
    if button2_rect.collidepoint(mouse_pos):
        button2_color = DARK_GRAY
    pygame.draw.rect(screen, button2_color, button2_rect)
    pygame.draw.rect(screen, BLACK, button2_rect, 3)
    if text2_surface:
        # Text im Button zentrieren
        text2_rect = text2_surface.get_rect(center=button2_rect.center)
        screen.blit(text2_surface, text2_rect.topleft)


    pygame.display.flip()
    clock.tick(30)

# Pygame beenden
pygame.quit()
sys.exit()