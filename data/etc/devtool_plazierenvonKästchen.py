import pygame
import sys
import tkinter as tk
from tkinter import filedialog
import os

# --- Konstanten ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BOX_WIDTH = 50
BOX_HEIGHT = 150
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (150, 150, 220)
BUTTON_TEXT_COLOR = WHITE
SAVE_FILENAME = "box_positions.txt"

# --- Hilfsfunktionen ---

def select_file(title="Datei auswählen", filetypes=(("PNG-Bilder", "*.png"), ("Alle Dateien", "*.*"))):
    """Öffnet einen Datei-Explorer zur Auswahl einer Datei."""
    root = tk.Tk()
    root.withdraw()  # Versteckt das leere Tkinter-Hauptfenster
    root.attributes('-topmost', True) # Stellt sicher, dass der Dialog im Vordergrund ist
    filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy() # Schließt das Tkinter-Fenster nach der Auswahl
    return filepath

def load_image(filepath, size=None, convert_alpha=True):
    """Lädt ein Bild, skaliert es optional und konvertiert es."""
    if not filepath or not os.path.exists(filepath):
        print(f"Fehler: Bilddatei nicht gefunden oder ausgewählt: {filepath}")
        return None, None
    try:
        image = pygame.image.load(filepath)
        if convert_alpha:
            image = image.convert_alpha() # Behält Transparenz bei
        else:
            image = image.convert() # Für Bilder ohne Transparenz (schneller)

        original_size = image.get_size()
        if size:
            image = pygame.transform.scale(image, size)
        return image, image.get_rect(topleft=(0,0)) # Gibt Bild und Rect zurück
    except pygame.error as e:
        print(f"Fehler beim Laden des Bildes '{filepath}': {e}")
        return None, None
    except Exception as e:
        print(f"Ein unerwarteter Fehler trat beim Laden von '{filepath}' auf: {e}")
        return None, None

def save_positions(boxes, filename):
    """Speichert die Positionen (obere linke Ecke) der Boxen in einer Datei."""
    try:
        with open(filename, "w") as f:
            for box_rect in boxes:
                f.write(f"{box_rect.left},{box_rect.top}\n")
        print(f"Positionen erfolgreich in '{filename}' gespeichert.")
    except IOError as e:
        print(f"Fehler beim Speichern der Positionen in '{filename}': {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler trat beim Speichern auf: {e}")


# --- Initialisierung ---
pygame.init()

# Bildschirm einrichten
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Box Placer und Verschieber")

# --- Ressourcen laden ---

# Hintergrundbild auswählen und laden
print("Bitte wähle das Hintergrundbild (PNG) aus.")
bg_filepath = select_file(title="Hintergrundbild auswählen (PNG)", filetypes=(("PNG-Bilder", "*.png"),))
background_image, _ = load_image(bg_filepath, size=(SCREEN_WIDTH, SCREEN_HEIGHT), convert_alpha=False)

if background_image is None:
    print("Kein gültiges Hintergrundbild geladen. Beende Programm.")
    pygame.quit()
    sys.exit()

# Kästchenbild auswählen und laden
print("Bitte wähle das Kästchenbild (PNG) aus.")
box_filepath = select_file(title="Kästchenbild auswählen (PNG)", filetypes=(("PNG-Bilder", "*.png"),))
# Lade das Bild und skaliere es auf die gewünschte Größe
box_image_scaled, _ = load_image(box_filepath, size=(BOX_WIDTH, BOX_HEIGHT), convert_alpha=True)

if box_image_scaled is None:
    print("Kein gültiges Kästchenbild geladen. Beende Programm.")
    pygame.quit()
    sys.exit()

# --- Spielvariablen ---
placed_boxes = []  # Liste, um die Rects der platzierten Boxen zu speichern
dragging = False
selected_box_index = None
mouse_offset_x = 0
mouse_offset_y = 0

# --- Button einrichten ---
button_font = pygame.font.Font(None, 30) # Standard-Schriftart, Größe 30
button_text = "Speichern"
button_padding = 10
text_surface = button_font.render(button_text, True, BUTTON_TEXT_COLOR)
text_rect = text_surface.get_rect()
button_width = text_rect.width + 2 * button_padding
button_height = text_rect.height + 2 * button_padding
save_button_rect = pygame.Rect(
    SCREEN_WIDTH - button_width - 10,  # 10px Abstand vom rechten Rand
    SCREEN_HEIGHT - button_height - 10, # 10px Abstand vom unteren Rand
    button_width,
    button_height
)
text_rect.center = save_button_rect.center # Text im Button zentrieren

# --- Spiel-Loop ---
running = True
clock = pygame.time.Clock()

while running:
    mouse_pos = pygame.mouse.get_pos()
    button_current_color = BUTTON_COLOR

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Linksklick: Box platzieren (wenn nicht auf Button geklickt)
            if event.button == 1: # 1 = Linksklick
                # Prüfen, ob auf den Button geklickt wurde
                if save_button_rect.collidepoint(event.pos):
                    save_positions(placed_boxes, SAVE_FILENAME)
                # Nur platzieren, wenn *nicht* auf eine vorhandene Box geklickt wird
                # und *nicht* auf den Button geklickt wird
                elif not any(box.collidepoint(event.pos) for box in placed_boxes):
                     # Neue Box erstellen, Rect zentriert an der Mausposition
                    # new_box_rect = box_image_scaled.get_rect(center=event.pos)
                    # Neue Box erstellen, Rect mit oberer linker Ecke an Mausposition
                    new_box_rect = box_image_scaled.get_rect(topleft=event.pos)
                    placed_boxes.append(new_box_rect)

            # Rechtsklick: Dragging starten
            elif event.button == 3: # 3 = Rechtsklick
                for i, box_rect in enumerate(placed_boxes):
                    if box_rect.collidepoint(event.pos):
                        dragging = True
                        selected_box_index = i
                        # Offset berechnen, damit die Box nicht springt
                        mouse_offset_x = event.pos[0] - box_rect.left
                        mouse_offset_y = event.pos[1] - box_rect.top
                        # Nur die erste gefundene Box greifen
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            # Rechtsklick loslassen: Dragging beenden
            if event.button == 3:
                dragging = False
                selected_box_index = None

        elif event.type == pygame.MOUSEMOTION:
            # Box verschieben, wenn Dragging aktiv ist
            if dragging and selected_box_index is not None:
                # Sicherstellen, dass der Index noch gültig ist (sollte er sein)
                if 0 <= selected_box_index < len(placed_boxes):
                    # Neue Position basierend auf Maus und Offset setzen
                    new_x = event.pos[0] - mouse_offset_x
                    new_y = event.pos[1] - mouse_offset_y
                    placed_boxes[selected_box_index].topleft = (new_x, new_y)

    # --- Rendern / Zeichnen ---

    # Hintergrund zeichnen
    screen.blit(background_image, (0, 0))

    # Platzierte Boxen zeichnen
    for box_rect in placed_boxes:
        screen.blit(box_image_scaled, box_rect.topleft)

    # Button zeichnen
    # Hover-Effekt für Button
    if save_button_rect.collidepoint(mouse_pos):
        button_current_color = BUTTON_HOVER_COLOR
    pygame.draw.rect(screen, button_current_color, save_button_rect, border_radius=5)
    screen.blit(text_surface, text_rect) # Text auf den Button zeichnen

    # Bildschirm aktualisieren
    pygame.display.flip()

    # Framerate begrenzen
    clock.tick(60) # Maximal 60 Frames pro Sekunde

# --- Aufräumen ---
pygame.quit()
sys.exit()