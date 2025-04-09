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
    import data.miniGame.zipWeed.zipWeed as zipWeedGame
    print(f"DEBUG: Import von {zipWeedGame.__name__} erfolgreich.")
except ImportError as e_imp_zw:
    print(f"FEHLER: Konnte das ZipWeed-Modul nicht importieren: {e_imp_zw}")
    traceback.print_exc()
except Exception as e_zw:
    print(f"FEHLER beim Import von ZipWeed: {e_zw}")
    traceback.print_exc()

# CockCrack Minispiel
cockCrackGame = None
try:
    print(f"DEBUG: Versuche Import von: data.miniGame.cockCrack.cockCrack")
    import data.miniGame.cockCrack.cockCrack as cockCrackGame
    print(f"DEBUG: Import von {cockCrackGame.__name__} erfolgreich.")
except ImportError as e_imp_cc:
    print(f"FEHLER: Konnte das CockCrack-Modul nicht importieren: {e_imp_cc}")
    traceback.print_exc()
except Exception as e_cc:
    print(f"FEHLER beim Import von CockCrack: {e_cc}")
    traceback.print_exc()

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
GREEN = (0, 128, 0)
RED = (200, 0, 0) # Für Text, falls benötigt

# --- Inventarvariablen ---
# ZipWeed / Allgemein
weed = 20
grips = 20
sorte = "Normal"
packed_weed_total = 0
# NEU: Variablen für CockCrack
pills = 3
liquid = 3
Crack = 0  # Startwert für Crack
liquidName = "Wasser"
pillsName = "Tafelgan"
# --- Ende neue Variablen ---

# --- Button Definition (Proportional) ---
BUTTON_WIDTH_PERCENT = 0.40
BUTTON_HEIGHT_PERCENT = 0.12
BUTTON_SPACING_PERCENT = 0.05
FONT_SIZE_REF_H = 600.0
BASE_FONT_SIZE = 40

button_width = int(SCREEN_WIDTH * BUTTON_WIDTH_PERCENT)
button_height = int(SCREEN_HEIGHT * BUTTON_HEIGHT_PERCENT)
button_spacing = int(SCREEN_HEIGHT * BUTTON_SPACING_PERCENT)
button_x = (SCREEN_WIDTH - button_width) // 2

total_buttons_height = 2 * button_height + button_spacing
button1_y = (SCREEN_HEIGHT - total_buttons_height) // 2
button2_y = button1_y + button_height + button_spacing

button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height) # ZipWeed Button
button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height) # CockCrack Button

# Proportionale Schriftgröße Button
button_font_size = max(20, int(SCREEN_HEIGHT * (BASE_FONT_SIZE / FONT_SIZE_REF_H)))
button_font = None
text1_surface = None
text2_surface = None
button1_text = "Starte ZipWeed Minispiel"
button2_text = "Starte CockCrack Minispiel" # Angepasster Text

try:
    button_font = pygame.font.SysFont("arial", button_font_size)
    if button_font:
        text1_surface = button_font.render(button1_text, True, BLACK)
        text2_surface = button_font.render(button2_text, True, BLACK)
except Exception as e_font:
    print(f"FEHLER beim Laden/Rendern der Button-Schriftart: {e_font}")
    try:
        button_font = pygame.font.Font(None, int(button_font_size * 1.2))
        if button_font:
             text1_surface = button_font.render(button1_text, True, BLACK)
             text2_surface = button_font.render(button2_text, True, BLACK)
    except Exception as e_font_fallback:
        print(f"FEHLER: Konnte auch Fallback-Button-Schriftart nicht laden: {e_font_fallback}")

# Schriftart und Position für Statusanzeige (Inventar)
STATUS_FONT_SIZE_REF_H = 600.0
BASE_STATUS_FONT_SIZE = 22 # Evtl. noch etwas kleiner wegen mehr Zeilen
status_font_size = max(12, int(SCREEN_HEIGHT * (BASE_STATUS_FONT_SIZE / STATUS_FONT_SIZE_REF_H)))
status_font = None
try:
    status_font = pygame.font.SysFont("arial", status_font_size)
    print(f"DEBUG: Status-Schriftart geladen (Größe {status_font_size}).")
except Exception as e_sfont:
    print(f"WARNUNG: Konnte Status-Schriftart 'arial' nicht laden: {e_sfont}. Nutze Fallback.")
    try:
        status_font = pygame.font.Font(None, status_font_size)
        print(f"DEBUG: Fallback-Status-Schriftart geladen (Größe {status_font_size}).")
    except Exception as e_sfont_fallback:
        print(f"FEHLER: Konnte auch Fallback-Status-Schriftart nicht laden: {e_sfont_fallback}")

STATUS_X = 15
STATUS_Y = 15
STATUS_LINE_HEIGHT = 0
if status_font:
    STATUS_LINE_HEIGHT = status_font.get_height() + 5
else:
    STATUS_LINE_HEIGHT = BASE_STATUS_FONT_SIZE + 5


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
                # --- Button 1: ZipWeed ---
                if button1_rect.collidepoint(event.pos):
                    print("INFO: Starte ZipWeed Minispiel...")
                    if zipWeedGame:
                        try:
                            print(f"DEBUG: Rufe zipWeedGame.run_zip_weed_game mit screen, weed={weed}, grips={grips}, sorte='{sorte}' auf")
                            result_tuple = zipWeedGame.run_zip_weed_game(screen, weed, grips, sorte)

                            if result_tuple:
                                remaining_weed, remaining_grips, packed_count, returned_sorte = result_tuple
                                print(f"DEBUG: ZipWeed Ergebnis erhalten: Weed={remaining_weed}, Grips={remaining_grips}, Packed in Runde={packed_count}, Sorte='{returned_sorte}'")
                                weed = remaining_weed
                                grips = remaining_grips
                                packed_weed_total += packed_count
                                # sorte = returned_sorte # Optional: Sorte aktualisieren, falls sie sich ändern kann
                                print(f"DEBUG: Inventar aktualisiert: Weed={weed}, Grips={grips}, Gesamt Verpackt={packed_weed_total}")
                            else:
                                print("WARNUNG: ZipWeed hat kein Ergebnis zurückgegeben!")

                            print("INFO: Zurück im Hauptmenü nach ZipWeed.")

                        # ... (Error handling for ZipWeed bleibt gleich) ...
                        except AttributeError as e_attr_zw:
                            print(f"FEHLER (AttributeError ZipWeed): {e_attr_zw}")
                            print(">>> Funktion 'run_zip_weed_game' nicht in zipWeedGame gefunden oder akzeptiert Argumente nicht!")
                            traceback.print_exc()
                        except TypeError as e_type_zw:
                            print(f"FEHLER (TypeError ZipWeed): {e_type_zw}")
                            print(">>> ZipWeed Funktion mit falschen Argumenten aufgerufen/gab kein Tupel zurück.")
                            traceback.print_exc()
                        except Exception as e_game_zw:
                            print(f"FEHLER beim Ausführen/Verarbeiten des ZipWeed Minispiels: {e_game_zw}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: ZipWeed-Modul (zipWeedGame) wurde nicht erfolgreich importiert.")

                # --- Button 2: CockCrack ---
                elif button2_rect.collidepoint(event.pos):
                    print("INFO: Starte CockCrack Minispiel...")
                    if cockCrackGame:
                        try:
                            # NEU: Übergebe die relevanten Variablen an CockCrack
                            # WICHTIG: Passe den Funktionsnamen an deine cockCrack.py an!
                            print(f"DEBUG: Rufe cockCrackGame.run_cock_crack_game mit screen, pills={pills}, liquid={liquid}, Crack={Crack}, liquidName='{liquidName}', pillsName='{pillsName}' auf")

                            # --- ANNAHME: Funktion heißt run_cock_crack_game ---
                            # --- Passe dies ggf. an!                          ---
                            function_to_call_cc = getattr(cockCrackGame, "run_cock_crack_game", None)

                            if function_to_call_cc:
                                # ANNAHME: CockCrack gibt die aktualisierten Werte zurück (pills, liquid, Crack)
                                # Passe dies an, falls es anders ist oder nichts zurückgibt.
                                result_cc = function_to_call_cc(screen, pills, liquid, Crack, liquidName, pillsName)

                                # --- Optional: Verarbeitung der Rückgabewerte von CockCrack ---
                                if result_cc: # Prüfen ob etwas zurückkam
                                    try:
                                        # Beispiel: Annahme, es gibt (rem_pills, rem_liquid, total_crack) zurück
                                        remaining_pills_cc, remaining_liquid_cc, new_crack_total_cc = result_cc
                                        pills = remaining_pills_cc
                                        liquid = remaining_liquid_cc
                                        Crack = new_crack_total_cc # Überschreibe den Crack-Wert mit dem Ergebnis
                                        print(f"DEBUG: CockCrack Ergebnis verarbeitet: Pills={pills}, Liquid={liquid}, Crack={Crack}")
                                    except (TypeError, ValueError) as e_unpack_cc:
                                         print(f"FEHLER: Rückgabewert von CockCrack konnte nicht entpackt werden: {e_unpack_cc}")
                                         print(f"DEBUG: Erhalten: {result_cc}")

                                else:
                                    print("DEBUG: CockCrack hat kein Ergebnis zurückgegeben (oder Verarbeitung nicht implementiert).")
                                # --- Ende Optional ---

                                print("INFO: Zurück im Hauptmenü nach CockCrack.")
                            else:
                                 print(f"FEHLER: Funktion 'run_cock_crack_game' nicht in cockCrackGame Modul gefunden!")


                        except AttributeError as e_attr_cc: # Fängt Fehler ab, wenn Modul da, aber Funktion fehlt (sollte durch getattr abgefangen sein)
                            print(f"FEHLER (AttributeError CockCrack): {e_attr_cc}")
                            print(f">>> Funktion 'run_cock_crack_game' (oder wie sie heißt) NICHT in cockCrackGame gefunden!")
                            traceback.print_exc()
                        except TypeError as e_type_cc:
                            print(f"FEHLER (TypeError CockCrack): {e_type_cc}")
                            print(">>> Die Funktion in cockCrack.py wurde mit der falschen Anzahl/Art von Argumenten aufgerufen oder gab falsches Format zurück.")
                            print(">>> Stelle sicher, dass die Funktion die Argumente (screen, pills, liquid, Crack, liquidName, pillsName) erwartet.") # Nachricht angepasst
                            traceback.print_exc()
                        except Exception as e_game_cc:
                            print(f"FEHLER beim Ausführen/Verarbeiten des CockCrack Minispiels: {e_game_cc}")
                            traceback.print_exc()
                    else:
                        print("FEHLER: CockCrack-Modul (cockCrackGame) wurde nicht erfolgreich importiert.")


    # Zeichnen
    screen.fill(WHITE)

    # --- Buttons zeichnen ---
    # Button 1 (ZipWeed)
    button1_color = GRAY
    if button1_rect.collidepoint(mouse_pos): button1_color = DARK_GRAY
    pygame.draw.rect(screen, button1_color, button1_rect)
    pygame.draw.rect(screen, BLACK, button1_rect, 3)
    if text1_surface and button_font:
        text1_rect = text1_surface.get_rect(center=button1_rect.center)
        screen.blit(text1_surface, text1_rect.topleft)

    # Button 2 (CockCrack)
    button2_color = GRAY
    if button2_rect.collidepoint(mouse_pos): button2_color = DARK_GRAY
    pygame.draw.rect(screen, button2_color, button2_rect)
    pygame.draw.rect(screen, BLACK, button2_rect, 3)
    if text2_surface and button_font:
        text2_rect = text2_surface.get_rect(center=button2_rect.center)
        screen.blit(text2_surface, text2_rect.topleft)

    # --- Statusanzeige (Inventar) zeichnen ---
    if status_font:
        try:
            current_y = STATUS_Y # Start Y für die Anzeige
            # ZipWeed Inventar
            weed_text_surf = status_font.render(f"Weed ({sorte}): {weed}", True, BLACK)
            grips_text_surf = status_font.render(f"Grips: {grips}", True, BLACK)
            packed_text_surf = status_font.render(f"Verpackt: {packed_weed_total}", True, GREEN)

            screen.blit(weed_text_surf, (STATUS_X, current_y))
            current_y += STATUS_LINE_HEIGHT
            screen.blit(grips_text_surf, (STATUS_X, current_y))
            current_y += STATUS_LINE_HEIGHT
            screen.blit(packed_text_surf, (STATUS_X, current_y))

            current_y += STATUS_LINE_HEIGHT * 1.5 # Etwas Abstand

            # NEU: CockCrack Inventar
            pills_text_surf = status_font.render(f"{pillsName}: {pills}", True, BLACK)
            liquid_text_surf = status_font.render(f"{liquidName}: {liquid}", True, BLACK)
            crack_text_surf = status_font.render(f"Crack: {Crack}", True, RED) # Crack in Rot

            screen.blit(pills_text_surf, (STATUS_X, current_y))
            current_y += STATUS_LINE_HEIGHT
            screen.blit(liquid_text_surf, (STATUS_X, current_y))
            current_y += STATUS_LINE_HEIGHT
            screen.blit(crack_text_surf, (STATUS_X, current_y))

        except Exception as e_render_status:
            print(f"FEHLER beim Rendern des Status-Textes: {e_render_status}")
            if status_font: # Nur zeichnen wenn Font da
                 error_surf = status_font.render("Fehler Status", True, RED)
                 screen.blit(error_surf, (STATUS_X, STATUS_Y))
    else:
        pass # Mache nichts, wenn kein Status-Font da ist


    pygame.display.flip()
    clock.tick(30)

# Pygame beenden
print("INFO: Hauptmenü wird beendet.")
pygame.quit()
sys.exit()