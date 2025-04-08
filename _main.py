# main.py
import pygame
import sys
import os

# Versuche, die Fenstergröße basierend auf der Android-Auflösung zu setzen (optional)
try:
    # Dies ist ein Versuch, die Auflösung unter Android zu ermitteln,
    # funktioniert möglicherweise nicht auf allen Geräten/Setups zuverlässig.
    # Standardwerte werden verwendet, wenn dies fehlschlägt.
    import android
    android.init()
    screen_info = pygame.display.Info()
    screen_width, screen_height = screen_info.current_w, screen_info.current_h
except ImportError:
    # Standardgröße, wenn nicht auf Android oder Modul nicht gefunden
    screen_width = 800
    screen_height = 600
except Exception as e:
    # Fange andere mögliche Fehler ab
    print(f"Konnte Android-Auflösung nicht ermitteln: {e}")
    screen_width = 800
    screen_height = 600


# Farben definieren
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0) # Farbe für den Text

# Pygame initialisieren
pygame.init()

# Bildschirm erstellen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Simple Pygame App")

# Schriftart für Text erstellen (optional, aber gut für Debugging)
try:
    font = pygame.font.Font(None, 50) # Standard-Schriftart, Größe 50
except Exception as e:
    print(f"Konnte Schriftart nicht laden: {e}")
    font = None # Fallback, falls Schriftart nicht geladen werden kann

# Haupt-Schleife
running = True
while running:
    # Ereignisse verarbeiten
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Beende die App auch mit der Zurück-Taste auf Android
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_AC_BACK: # Spezieller Keycode für Android Zurück-Taste
                 running = False


    # Zeichnen
    screen.fill(WHITE) # Hintergrund weiß füllen

    # Einen Kreis zeichnen
    circle_radius = 50
    circle_x = screen_width // 2
    circle_y = screen_height // 2
    pygame.draw.circle(screen, BLUE, (circle_x, circle_y), circle_radius)

    # Optional: Text anzeigen, um zu sehen, ob die Schriftart funktioniert
    if font:
        text_surface = font.render("Hallo Android!", True, RED)
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 100))
        screen.blit(text_surface, text_rect)
    else:
        # Fallback, wenn keine Schriftart geladen wurde (z.B. Punkt zeichnen)
         pygame.draw.circle(screen, RED, (10, 10), 5) # Kleiner roter Punkt oben links

    # Bildschirm aktualisieren
    pygame.display.flip()

    # Kurze Pause, um CPU nicht zu überlasten
    pygame.time.Clock().tick(30) # Begrenzt auf 30 FPS

# Pygame beenden
pygame.quit()
sys.exit()