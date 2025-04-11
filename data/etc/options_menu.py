# data/etc/options_menu.py
import pygame
import os
import traceback
from . import settings_utils # Importiere aus dem gleichen Verzeichnis

# Farben (könnten auch in eine zentrale Konstanten-Datei)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
BLUE = (0, 0, 200)
RED = (200, 0, 0)

# Konstanten für das Optionsmenü (anpassbar)
OPTIONS_TITLE_FONT_SIZE = 40
OPTIONS_ITEM_FONT_SIZE = 25
SLIDER_WIDTH_PERCENT = 0.6
SLIDER_HEIGHT = 20
SLIDER_HANDLE_WIDTH = 10
SLIDER_HANDLE_HEIGHT = 30
OPTIONS_BACK_BUTTON_WIDTH_PERCENT = 0.35 # Etwas breiter für den Text
OPTIONS_BACK_BUTTON_HEIGHT_PERCENT = 0.08
FONT_SIZE_REF_H = 600.0 # Referenzhöhe für Schriftgrößen-Skalierung
BASE_BUTTON_FONT_SIZE = 30 # Basisschriftgröße für den Zurück-Button

def run_options_menu(screen, current_settings, settings_file_path):
    """
    Zeigt das Optionsmenü an und verarbeitet die Eingaben.
    Gibt das (potenziell geänderte) Einstellungs-Dictionary zurück.
    Gibt None zurück, wenn das Spiel beendet werden soll (z.B. durch Schließen des Fensters).
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    clock = pygame.time.Clock()
    options_running = True
    active_slider = None # Welcher Slider gerade gezogen wird

    # --- Schriftarten laden (mit Fallback) ---
    options_title_font = None
    options_item_font = None
    options_back_button_font = None
    back_button_font_size = max(15, int(SCREEN_HEIGHT * (BASE_BUTTON_FONT_SIZE / FONT_SIZE_REF_H)))

    try:
        options_title_font = pygame.font.SysFont("arial", OPTIONS_TITLE_FONT_SIZE)
        options_item_font = pygame.font.SysFont("arial", OPTIONS_ITEM_FONT_SIZE)
        options_back_button_font = pygame.font.SysFont("arial", back_button_font_size)
        if not options_title_font or not options_item_font or not options_back_button_font:
            raise Exception("Einige Options-Schriftarten (arial) konnten nicht geladen werden.")
        print("INFO (Options): Systemschriftarten ('arial') geladen.")
    except Exception as e_opt_font:
        print(f"WARNUNG (Options): Konnte Systemschriftarten nicht laden: {e_opt_font}. Nutze Fallback.")
        try:
            options_title_font = pygame.font.Font(None, OPTIONS_TITLE_FONT_SIZE + 5)
            options_item_font = pygame.font.Font(None, OPTIONS_ITEM_FONT_SIZE + 5)
            options_back_button_font = pygame.font.Font(None, back_button_font_size + 2)
            if not options_title_font or not options_item_font or not options_back_button_font:
                raise Exception("Fallback Options-Schriftarten fehlgeschlagen.")
            print("INFO (Options): Fallback-Schriftarten geladen.")
        except Exception as e_opt_font_fb:
            print(f"FEHLER (Options): Konnte auch Fallback-Schriftarten nicht laden: {e_opt_font_fb}")
            # Kritisch? Setzen wir sie auf None, Zeichnen wird übersprungen oder zeigt Fehler
            options_title_font = options_item_font = options_back_button_font = None

    # --- Dynamische Rect-Berechnung (nur einmal pro Aufruf nötig) ---
    slider_width = int(SCREEN_WIDTH * SLIDER_WIDTH_PERCENT)
    slider_x = (SCREEN_WIDTH - slider_width) // 2
    slider_start_y = SCREEN_HEIGHT * 0.25
    slider_spacing = SCREEN_HEIGHT * 0.15

    slider_music_y = slider_start_y
    slider_sfx_y = slider_start_y + slider_spacing
    slider_master_y = slider_start_y + 2 * slider_spacing

    slider_music_rect = pygame.Rect(slider_x, slider_music_y, slider_width, SLIDER_HEIGHT)
    slider_sfx_rect = pygame.Rect(slider_x, slider_sfx_y, slider_width, SLIDER_HEIGHT)
    slider_master_rect = pygame.Rect(slider_x, slider_master_y, slider_width, SLIDER_HEIGHT)

    back_button_width = int(SCREEN_WIDTH * OPTIONS_BACK_BUTTON_WIDTH_PERCENT)
    back_button_height = int(SCREEN_HEIGHT * OPTIONS_BACK_BUTTON_HEIGHT_PERCENT)
    back_button_x = (SCREEN_WIDTH - back_button_width) // 2
    back_button_y = SCREEN_HEIGHT * 0.85
    options_back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)

    # --- Options-Schleife ---
    while options_running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                options_running = False
                return None # Signal zum Beenden des gesamten Spiels

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    options_running = False # Verlässt das Menü, speichert unten

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    # Zurück-Button
                    if options_back_button_rect.collidepoint(mouse_pos):
                        options_running = False # Verlässt das Menü, speichert unten
                    # Slider-Klick (Start des Ziehens)
                    elif slider_music_rect.collidepoint(mouse_pos):
                        active_slider = "music"
                    elif slider_sfx_rect.collidepoint(mouse_pos):
                        active_slider = "sfx"
                    elif slider_master_rect.collidepoint(mouse_pos):
                        active_slider = "master"

                    # Wenn auf einen Slider geklickt wurde, direkt Lautstärke anpassen
                    if active_slider:
                        slider_rect = None
                        if active_slider == "music": slider_rect = slider_music_rect
                        elif active_slider == "sfx": slider_rect = slider_sfx_rect
                        elif active_slider == "master": slider_rect = slider_master_rect

                        if slider_rect:
                            relative_x = mouse_pos[0] - slider_rect.left
                            new_volume = max(0.0, min(1.0, relative_x / slider_rect.width))
                            current_settings[f"{active_slider}_volume"] = new_volume
                            print(f"DEBUG (Options): Slider '{active_slider}' Klick/Update auf {new_volume:.2f}")
                            # Musiklautstärke direkt anwenden
                            if active_slider == "music" and pygame.mixer.get_init(): # Prüfen ob Mixer läuft
                                try:
                                    pygame.mixer.music.set_volume(new_volume)
                                except pygame.error as e_set_vol:
                                    print(f"WARNUNG (Options): Konnte Musiklautstärke nicht setzen: {e_set_vol}")
                            # Hier Logik für SFX/Master hinzufügen, falls implementiert

            if event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1:
                     if active_slider:
                         print(f"DEBUG (Options): Slider '{active_slider}' losgelassen.")
                         active_slider = None # Ziehen beenden

        # --- Slider Handling (während Maus gedrückt gehalten wird) ---
        if active_slider and mouse_pressed[0]:
            slider_rect = None
            if active_slider == "music": slider_rect = slider_music_rect
            elif active_slider == "sfx": slider_rect = slider_sfx_rect
            elif active_slider == "master": slider_rect = slider_master_rect

            if slider_rect:
                relative_x = mouse_pos[0] - slider_rect.left
                new_volume = max(0.0, min(1.0, relative_x / slider_rect.width))
                # Nur aktualisieren, wenn sich der Wert tatsächlich ändert (kleine Optimierung)
                if current_settings[f"{active_slider}_volume"] != new_volume:
                    current_settings[f"{active_slider}_volume"] = new_volume
                    # Musiklautstärke direkt anwenden
                    if active_slider == "music" and pygame.mixer.get_init():
                        try:
                            pygame.mixer.music.set_volume(new_volume)
                        except pygame.error as e_set_vol:
                            print(f"WARNUNG (Options): Konnte Musiklautstärke beim Ziehen nicht setzen: {e_set_vol}")
                    # Hier Logik für SFX/Master hinzufügen

        # --- Zeichnen ---
        screen.fill(WHITE) # Hintergrund für Optionen (könnte auch ein Bild sein)

        if options_title_font and options_item_font and options_back_button_font:
            try:
                # Titel
                title_surf = options_title_font.render("Optionen", True, BLACK)
                title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.1))
                screen.blit(title_surf, title_rect)

                # --- Helferfunktion zum Zeichnen eines Sliders ---
                def draw_slider(key, label, rect, font):
                    text_surf = font.render(f"{label}: {int(current_settings[key]*100)}%", True, BLACK)
                    text_rect = text_surf.get_rect(midright=(rect.left - 20, rect.centery))
                    screen.blit(text_surf, text_rect)
                    # Slider Hintergrund
                    pygame.draw.rect(screen, GRAY, rect, border_radius=5)
                    # Slider Griff
                    handle_x = rect.left + int(rect.width * current_settings[key])
                    handle_rect = pygame.Rect(0, 0, SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT)
                    handle_rect.center = (handle_x, rect.centery)
                    pygame.draw.rect(screen, BLUE, handle_rect, border_radius=3)

                # Slider zeichnen
                draw_slider("music_volume", "Musik", slider_music_rect, options_item_font)
                draw_slider("sfx_volume", "Effekte", slider_sfx_rect, options_item_font)
                draw_slider("master_volume", "Gesamt", slider_master_rect, options_item_font)

                # Zurück-Button
                back_button_color = GRAY if not options_back_button_rect.collidepoint(mouse_pos) else DARK_GRAY
                pygame.draw.rect(screen, back_button_color, options_back_button_rect, border_radius=8)
                pygame.draw.rect(screen, BLACK, options_back_button_rect, 2, border_radius=8)
                back_text_surf = options_back_button_font.render("Zurück & Speichern", True, BLACK)
                back_text_rect = back_text_surf.get_rect(center=options_back_button_rect.center)
                screen.blit(back_text_surf, back_text_rect)

            except Exception as e_render_options:
                print(f"FEHLER (Options) beim Rendern: {e_render_options}")
                traceback.print_exc()
                # Fallback-Fehlermeldung
                try:
                    fallback_font = pygame.font.Font(None, 30)
                    error_surf = fallback_font.render("Fehler beim Zeichnen der Optionen!", True, RED)
                    screen.blit(error_surf, (20, 20))
                except: pass # Wenn selbst das fehlschlägt

        else:
             # Fallback, wenn Schriften nicht geladen werden konnten
            try:
                fallback_font = pygame.font.Font(None, 30)
                error_surf = fallback_font.render("Fehler: Options-Schriftarten nicht geladen!", True, RED)
                screen.blit(error_surf, (20, 20))
                 # Minimaler Zurück-Button ohne Text, damit man rauskommt
                back_button_color = GRAY if not options_back_button_rect.collidepoint(mouse_pos) else DARK_GRAY
                pygame.draw.rect(screen, back_button_color, options_back_button_rect, border_radius=8)
                pygame.draw.rect(screen, BLACK, options_back_button_rect, 2, border_radius=8)
            except: pass


        pygame.display.flip()
        clock.tick(60)

    # --- Ende der Options-Schleife ---
    # Einstellungen speichern, bevor das Menü verlassen wird
    print("INFO (Options): Optionen werden geschlossen, speichere Einstellungen...")
    settings_utils.save_settings(settings_file_path, current_settings)

    return current_settings # Gib die (potenziell geänderten) Einstellungen zurück