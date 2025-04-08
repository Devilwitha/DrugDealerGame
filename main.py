# -*- coding: utf-8 -*-
import pygame
import sys
import math
import os # os wird jetzt für die Pfadkorrektur benötigt

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
    # Versuche, ein Modul zu importieren, das typischerweise nur
    # in einer Android-Verpackungsumgebung vorhanden ist (wie Kivy/Buildozer)
    # ACHTUNG: Dies ist eine Heuristik und nicht 100% sicher.
    # Wenn du eine andere Methode zur Android-Erkennung hast, nutze diese.
    import android # Diese Zeile kann einen ImportError auslösen, wenn nicht auf Android
    is_android = True
    print("Android-Plattform erkannt (basierend auf 'import android').")
except ImportError:
    print("Nicht-Android-Plattform erkannt.")
    # Prüfe alternativ über os.environ, was bei Kivy oft gesetzt wird
    if "ANDROID_ARGUMENT" in os.environ:
        is_android = True
        print("Android-Plattform erkannt (basierend auf Umgebungsvariable).")


if is_android and detected_height > detected_width:
    print(f"Android im Portrait-Modus erkannt. Tausche Breite({detected_width}) und Höhe({detected_height}) für interne Landscape-Berechnung.")
    # Behalte die ursprünglichen erkannten Werte für set_mode
    # Tausche nur die Werte für die *Berechnung* der Elemente
    CALC_WIDTH = detected_width
    CALC_HEIGHT = detected_height
else:
    # Auf Desktop oder Android im Landscape-Modus
    CALC_WIDTH = detected_width
    CALC_HEIGHT = detected_height

# --- Fenstermodus wählen ---
# Verwende IMMER die *original* erkannten Dimensionen für die Fenstererstellung
screen = pygame.display.set_mode((detected_width, detected_height), pygame.SCALED) # Mit SCALED empfohlen

pygame.display.set_caption("Viereck Packer V11.6 - Cross-Platform Path") # Versionsnummer erhöht

# Farben (RGB)
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)

# --- Proportionale Berechnung (nutzt CALC_WIDTH/HEIGHT) ---
target_width = max(1, int(CALC_WIDTH * (150 / ref_w)))
target_height = max(1, int(CALC_HEIGHT * (200 / ref_h)))
target_padding_right = max(1, int(CALC_WIDTH * (50 / ref_w)))
target_padding_bottom = max(1, int(CALC_HEIGHT * (100 / ref_h)))
target_x = CALC_WIDTH - target_width - target_padding_right
target_y = CALC_HEIGHT - target_height - target_padding_bottom
target_rect = pygame.Rect(target_x, target_y, target_width, target_height)

# --- Swipe-Linien-Höhe berechnen (mit Android-Anpassung, nutzt CALC_HEIGHT) ---
base_swipe_line_height = max(1, int(CALC_HEIGHT * (12 / ref_h)))
if is_android:
    swipe_line_height = base_swipe_line_height * 3
    print(f"Android: Erhöhe Swipe-Linien-Höhe auf {swipe_line_height} (Basis: {base_swipe_line_height})")
else:
    swipe_line_height = base_swipe_line_height
# Erstelle das Swipe-Rechteck mit der (ggf. angepassten) Höhe
# Wichtig: Position basiert auf target_rect, das bereits auf CALC_WIDTH/HEIGHT basiert
swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height)
min_swipe_distance = swipe_line_rect.width * 0.85 # Basiert auf Breite, die von CALC_WIDTH abhängt

# Restliche proportionale Berechnungen (nutzen CALC_WIDTH/HEIGHT)
small_size = max(1, int(CALC_WIDTH * (80 / ref_w)))
start_padding_left = max(1, int(CALC_WIDTH * (100 / ref_w)))
start_padding_top = max(1, int(CALC_HEIGHT * (400 / ref_h)))
start_pos = [start_padding_left, start_padding_top]
small_rect = pygame.Rect(start_pos[0], start_pos[1], small_size, small_size)

gravity = max(1, int(CALC_HEIGHT * (6 / ref_h)))
font_size = max(12, int(CALC_HEIGHT * (36 / ref_h)))
try:
    font = pygame.font.SysFont("arial", font_size)
except pygame.error:
    font = pygame.font.Font(None, font_size)

score_pos_x = max(1, int(CALC_WIDTH * (10 / ref_w)))
score_pos_y = max(1, int(CALC_HEIGHT * (10 / ref_h)))
# --- Ende Proportionale Berechnung ---

# --- Bild laden (mit plattformunabhängiger Pfadermittlung) ---
small_image = None
use_image = False
image_filename = "butt.png"
image_datafolder = "data"
image_folder = "bilder"

# --- KORREKTUR START: Plattformunabhängiger Pfad ---
try:
    # Ermittle den Pfad des Verzeichnisses, in dem das aktuelle Skript liegt
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback, wenn __file__ nicht definiert ist (z.B. bei interaktiver Nutzung oder speziellen Bundlern)
    script_dir = os.path.abspath(".")
    print("WARNUNG: '__file__' nicht gefunden, nutze aktuelles Arbeitsverzeichnis als Basis.")

# Baue den Pfad zum Bild relativ zum Skriptverzeichnis (oder Fallback) auf
image_path = os.path.join(script_dir, image_datafolder, image_folder, image_filename)
# --- KORREKTUR ENDE ---

print(f"Versuche Bild zu laden von: {image_path}") # Gibt den vollständigen Pfad aus
try:
    original_small_image = pygame.image.load(image_path).convert_alpha()
    original_size = original_small_image.get_size()
    print(f"DEBUG: Originalbild '{image_path}' geladen. Grösse: {original_size}")

    # Skaliere das Bild auf die berechnete small_size
    # Stelle sicher, dass small_size > 0 ist in beiden Dimensionen
    if small_size > 0:
        small_image = pygame.transform.smoothscale(original_small_image, (small_size, small_size))
        scaled_size = small_image.get_size()
        print(f"DEBUG: Bild skaliert auf: {scaled_size}")

        # Toleranzprüfung für die Skalierung
        if abs(scaled_size[0] - small_size) <= 1 and abs(scaled_size[1] - small_size) <= 1:
            use_image = True
            print(f"Bild '{image_path}' erfolgreich geladen und Skalierung scheint OK.")
        else:
            print(f"WARNUNG: Skalierung ungenau (Ziel: {small_size}x{small_size}, Ergebnis: {scaled_size}). Nutze Fallback.")
            use_image = False
            small_image = None # Setze Bild zurück, um Fallback sicherzustellen
    else:
         print(f"WARNUNG: Berechnete small_size ({small_size}) ist ungültig für Skalierung. Nutze Fallback.")
         use_image = False

except (pygame.error, FileNotFoundError) as e:
    print(f"WARNUNG: Fehler beim Laden/Skalieren des Bildes '{image_path}': {e}")
    print("-> Zeichne stattdessen rotes Viereck.")
    use_image = False
    small_image = None # Sicherstellen, dass kein Bild verwendet wird
# --- Ende Bild laden ---

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
                # Priorität 1: Ist der Klick im Swipe-Bereich, wenn bereit?
                if ready_for_swipe and swipe_line_rect.collidepoint(event.pos):
                    is_swiping = True
                    swipe_start_x = event.pos[0]
                    swipe_current_x = event.pos[0]
                    dragging = False # Sicherstellen, dass nicht gleichzeitig gedraggt wird
                # Priorität 2: Ist der Klick auf dem kleinen Viereck/Bild?
                elif small_rect.collidepoint(event.pos):
                    dragging = True
                    is_falling = False
                    ready_for_swipe = False
                    is_swiping = False # Sicherstellen, dass Swiping beendet wird
                    swipe_start_x = None
                    swipe_current_x = None
                    # Berechne Offset relativ zur oberen linken Ecke des Vierecks
                    offset_x = small_rect.x - event.pos[0]
                    offset_y = small_rect.y - event.pos[1]
                # Priorität 3: Klick irgendwo anders (ignoriert für Drag/Swipe)
                else:
                    pass # Kein relevantes Objekt geklickt

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Linke Maustaste / Touch losgelassen
                if is_swiping:
                    # Swipe beendet (egal ob erfolgreich oder nicht)
                    is_swiping = False
                    swipe_start_x = None
                    swipe_current_x = None
                    # WICHTIG: Prüfe *nach* dem Loslassen, ob das Viereck noch im Ziel ist
                    if not target_rect.contains(small_rect):
                         ready_for_swipe = False # War vielleicht drin, wurde aber rausgezogen
                         is_falling = True      # Sollte wieder fallen
                    # Kein else nötig, wenn es noch drin ist, bleibt ready_for_swipe=True

                elif dragging:
                    # Dragging beendet
                    dragging = False
                    # Prüfe, ob das Viereck *vollständig* im Zielbereich ist
                    if target_rect.contains(small_rect):
                        ready_for_swipe = True
                        is_falling = False
                    else:
                        # Nicht (mehr) im Ziel -> fallen lassen
                        ready_for_swipe = False
                        is_falling = True

        elif event.type == pygame.MOUSEMOTION:
            if is_swiping:
                swipe_current_x = event.pos[0]
                # Prüfe, ob die Mausbewegung *innerhalb* der Swipe-Linie stattfindet
                # (Verhindert versehentliches Swipen ausserhalb)
                if swipe_line_rect.collidepoint(event.pos):
                    if swipe_start_x is not None: # Sicherheitshalber prüfen
                        swiped_distance = abs(swipe_current_x - swipe_start_x)
                        # Prüfe, ob die Distanz ausreicht
                        if swiped_distance >= min_swipe_distance:
                            score += 1
                            small_rect.topleft = tuple(start_pos) # Zurück zum Start
                            # Zustand zurücksetzen
                            ready_for_swipe = False
                            is_falling = False # Nicht fallen lassen nach erfolgreichem Swipe
                            is_swiping = False
                            swipe_start_x = None
                            swipe_current_x = None
                else:
                    # Maus hat Swipe-Bereich verlassen -> Swipe abbrechen
                    is_swiping = False
                    swipe_start_x = None
                    swipe_current_x = None
                    # Zustand muss hier nicht geändert werden, da MOUSEBUTTONUP das regelt

            elif dragging:
                old_rect = small_rect.copy() # Kopie der alten Position für Kollisionslogik
                # Neue potentielle Position berechnen
                potential_x = event.pos[0] + offset_x
                potential_y = event.pos[1] + offset_y
                small_rect.topleft = (potential_x, potential_y)

                # --- Kollisionsbehandlung mit dem ZIEL-Rechteck ---
                # Verhindert, dass das kleine Viereck in das Ziel hineingezogen wird
                # (Nur relevant, wenn es *von aussen* kommt)
                if not target_rect.contains(old_rect) and small_rect.colliderect(target_rect):
                    # Von LINKS kommend in Ziel eingedrungen?
                    if old_rect.right <= target_rect.left and small_rect.right > target_rect.left:
                        small_rect.right = target_rect.left
                    # Von RECHTS kommend in Ziel eingedrungen?
                    elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right:
                        small_rect.left = target_rect.right
                    # Von OBEN kommend in Ziel eingedrungen?
                    elif old_rect.bottom <= target_rect.top and small_rect.bottom > target_rect.top:
                         small_rect.bottom = target_rect.top
                    # Von UNTEN kommend in Ziel eingedrungen?
                    # (Sollte durch Schwerkraft eigentlich nicht passieren, aber sicher ist sicher)
                    elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom:
                         small_rect.top = target_rect.bottom

                # --- Begrenzung auf den Bildschirm ---
                if small_rect.left < 0: small_rect.left = 0
                if small_rect.right > CALC_WIDTH: small_rect.right = CALC_WIDTH
                if small_rect.top < 0: small_rect.top = 0
                if small_rect.bottom > CALC_HEIGHT: small_rect.bottom = CALC_HEIGHT


    # Spiel-Logik / Physik (Fallen)
    if is_falling and not dragging and not ready_for_swipe and not is_swiping:
        potential_y = small_rect.y + gravity
        potential_rect = small_rect.copy()
        potential_rect.y = potential_y

        # Prüfe Kollision mit UNTERKANTE des Ziels
        collides_with_target_bottom = (
            potential_rect.bottom > target_rect.bottom and  # Potentiell tiefer als Ziel-Unten
            small_rect.bottom <= target_rect.bottom and     # Aktuell noch drüber oder bündig
            potential_rect.right > target_rect.left and     # Horizontal überlappend
            potential_rect.left < target_rect.right
        )

        if collides_with_target_bottom:
            # Auf Unterkante des Ziels aufsetzen
            small_rect.bottom = target_rect.bottom
            is_falling = False
            # Ist es jetzt *im* Ziel? (Kann sein, wenn es von oben drauf fällt)
            if target_rect.contains(small_rect):
                ready_for_swipe = True
            else:
                # Auf Kante gelandet, aber nicht drin -> nicht bereit
                ready_for_swipe = False
        else:
            # Keine Kollision mit Zielboden, prüfe Bildschirmrand
            if potential_rect.bottom >= CALC_HEIGHT:
                # Am Boden angekommen -> zurück zum Start
                small_rect.topleft = tuple(start_pos)
                is_falling = False
                ready_for_swipe = False # Sicherstellen
            else:
                # Einfach weiter fallen
                small_rect.y = potential_y

    # Wenn 'ready_for_swipe' war, aber Objekt aus Ziel gezogen wurde (ohne Loslassen)
    if ready_for_swipe and not target_rect.contains(small_rect) and not dragging and not is_swiping:
         ready_for_swipe = False
         is_falling = True # Soll wieder fallen

    # --- Zeichnen ---
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, target_rect) # Ziel

    # Swipe-Linie und Fortschritt zeichnen
    if ready_for_swipe:
        # Zeichne die grüne Linie (Basis für Swipe)
        pygame.draw.rect(screen, GREEN, swipe_line_rect)

        # Zeichne orangen Fortschrittsbalken, wenn geswiped wird
        if is_swiping and swipe_start_x is not None and swipe_current_x is not None:
            # Berechne Start und Breite des orangen Balkens
            orange_rect_x = min(swipe_start_x, swipe_current_x)
            orange_rect_width = abs(swipe_current_x - swipe_start_x)

            # Begrenze den orangen Balken auf die Breite der grünen Linie
            orange_rect_x = max(swipe_line_rect.left, orange_rect_x)
            orange_rect_right = min(swipe_line_rect.right, orange_rect_x + orange_rect_width)
            orange_rect_width = orange_rect_right - orange_rect_x # Effektive Breite

            if orange_rect_width > 0:
                # Nutzt swipe_line_rect.height (kann auf Android höher sein)
                orange_progress_rect = pygame.Rect(orange_rect_x, swipe_line_rect.y, orange_rect_width, swipe_line_rect.height)
                pygame.draw.rect(screen, ORANGE, orange_progress_rect)

    # Kleines Viereck: Bild oder Fallback (rotes Viereck) zeichnen
    if use_image and small_image is not None:
        screen.blit(small_image, small_rect.topleft)
    else:
        # Stelle sicher, dass auch small_rect existiert
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