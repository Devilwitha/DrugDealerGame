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
if detected_height > detected_width:
     print(f"WARNUNG: Erkannte Dimensionen ({detected_width}x{detected_height}) scheinen Hochformat zu sein. Tausche für Landscape-Berechnungen.")
     CALC_WIDTH = detected_height
     CALC_HEIGHT = detected_width
else:
     CALC_WIDTH = detected_width
     CALC_HEIGHT = detected_height
print(f"Nutze Dimensionen für proportionale Berechnungen (erzwinge Landscape-Ratio): {CALC_WIDTH}x{CALC_HEIGHT}")

# --- Fenstermodus wählen ---
print(f"Versuche set_mode mit erkannten Dimensionen: {detected_width}x{detected_height}")
screen = pygame.display.set_mode((detected_width, detected_height), pygame.SCALED)
actual_screen_size = screen.get_size()
print(f"Pygame screen initialisiert. Tatsächliche Größe laut screen.get_size(): {actual_screen_size}")
if actual_screen_size != (detected_width, detected_height):
    print(f"WARNUNG: Tatsächliche Screen-Größe weicht von ursprünglich erkannter Größe ab!")
pygame.display.set_caption("Viereck Packer V11.8 - Target Image")

# Farben (RGB)
WHITE, BLACK, RED, BLUE, GREEN, ORANGE = (255,)*3, (0,)*3, (255,0,0), (0,0,255), (0,255,0), (255,165,0)

# --- Proportionale Berechnung (basiert auf CALC_WIDTH/HEIGHT) ---
target_width = max(1, int(CALC_WIDTH * (150 / ref_w)))
target_height = max(1, int(CALC_HEIGHT * (200 / ref_h)))
target_padding_right = max(1, int(CALC_WIDTH * (50 / ref_w)))
target_padding_bottom = max(1, int(CALC_HEIGHT * (100 / ref_h)))
target_x = actual_screen_size[0] - target_width - target_padding_right
target_y = actual_screen_size[1] - target_height - target_padding_bottom
target_rect = pygame.Rect(target_x, target_y, target_width, target_height)

base_swipe_line_height = max(1, int(CALC_HEIGHT * (12 / ref_h)))
if is_android:
    swipe_line_height = max(1, int(base_swipe_line_height * 4.5))
    print(f"Android: Erhöhe Swipe-Linien-Höhe auf {swipe_line_height} (Basis: {base_swipe_line_height}, Faktor 4.5)")
else:
    swipe_line_height = base_swipe_line_height
swipe_line_rect = pygame.Rect(target_rect.x, target_rect.y, target_rect.width, swipe_line_height)
min_swipe_distance = swipe_line_rect.width * 0.85

small_size = max(1, int(CALC_WIDTH * (80 / ref_w)))
start_padding_left = max(1, int(CALC_WIDTH * (100 / ref_w)))
start_padding_top = max(1, int(CALC_HEIGHT * (400 / ref_h)))
start_pos = [start_padding_left, start_padding_top]
if small_size <= 0:
     print(f"WARNUNG: Berechnete small_size ({small_size}) ist <= 0. Setze auf 1.")
     small_size = 1
small_rect = pygame.Rect(start_pos[0], start_pos[1], small_size, small_size)

gravity = max(1, int(CALC_HEIGHT * (6 / ref_h)))
font_size = max(12, int(CALC_HEIGHT * (36 / ref_h)))
try:
    font = pygame.font.SysFont("arial", font_size)
except pygame.error:
    font = pygame.font.Font(None, font_size)

score_pos_x = max(1, int(actual_screen_size[0] * (10 / ref_w)))
score_pos_y = max(1, int(actual_screen_size[1] * (10 / ref_h)))
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
use_small_image = False
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
swipe_min_x, swipe_max_x = None, None
display_persistent_swipe_bar = False
persistent_bar_rect = None
# *** NEU: Variable für "Vorsprung" durch alten Balken ***
resumed_swipe_initial_width = 0
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
                    # --- ANGEPASSTE SWIPE START LOGIK ---
                    print("Swipe gestartet/fortgesetzt (Finger auf Linie)") # Debug
                    is_swiping = True
                    current_click_x = event.pos[0]
                    swipe_current_x = current_click_x
                    swipe_start_x = current_click_x # Startpunkt für *neue* Distanzmessung

                    if display_persistent_swipe_bar and persistent_bar_rect is not None:
                        print(f"-> Setze Swipe fort. Alter Balken: {persistent_bar_rect.width}px")
                        # Behalte/Erweitere Min/Max basierend auf altem Balken und Klick
                        swipe_min_x = min(persistent_bar_rect.left, current_click_x)
                        swipe_max_x = max(persistent_bar_rect.right, current_click_x)
                        # Speichere die Breite des alten Balkens als "Vorsprung"
                        resumed_swipe_initial_width = persistent_bar_rect.width
                        # Schalte persistenten Balken aus (visuell), da wir jetzt aktiv swipen
                        display_persistent_swipe_bar = False
                        persistent_bar_rect = None
                    else:
                        print("-> Starte neuen Swipe.")
                        # Kein persistenter Balken, starte normal
                        swipe_min_x = current_click_x
                        swipe_max_x = current_click_x
                        resumed_swipe_initial_width = 0 # Kein Vorsprung

                    dragging = False # Sicherstellen, dass nicht gleichzeitig gedraggt wird

                elif small_rect.collidepoint(event.pos) and not is_swiping:
                    print("Dragging gestartet") # Debug
                    dragging = True
                    is_falling = False
                    ready_for_swipe = False
                    is_swiping = False
                    swipe_start_x = None
                    swipe_current_x = None
                    swipe_min_x = None
                    swipe_max_x = None
                    # Wenn Dragging startet, verschwindet der persistente Balken & Vorsprung
                    display_persistent_swipe_bar = False
                    persistent_bar_rect = None
                    resumed_swipe_initial_width = 0
                    offset_x = small_rect.x - event.pos[0]
                    offset_y = small_rect.y - event.pos[1]
                    # print(f" Drag Start: rect=({small_rect.x},{small_rect.y}), pos=({event.pos[0]},{event.pos[1]}), offset=({offset_x},{offset_y})")

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if is_swiping:
                    print("Swipe beendet (Finger hoch)") # Debug
                    is_swiping = False # Aktives Swipen ist beendet

                    # --- Logik für persistierenden Balken ---
                    # Erfolg wird nur in MOUSEMOTION festgestellt. Wenn wir hier sind, war es NICHT erfolgreich.
                    final_width = 0
                    final_rect = None
                    if swipe_min_x is not None and swipe_max_x is not None:
                         clamped_orange_x = max(swipe_line_rect.left, swipe_min_x)
                         clamped_orange_right = min(swipe_line_rect.right, swipe_max_x)
                         final_width = max(0, clamped_orange_right - clamped_orange_x)
                         if final_width > 0:
                            final_rect = pygame.Rect(clamped_orange_x, swipe_line_rect.y, final_width, swipe_line_rect.height)

                    # Persistieren, wenn ein Balken vorhanden ist (Erfolg wurde ja schon ausgeschlossen)
                    if final_rect:
                        persistent_bar_rect = final_rect
                        display_persistent_swipe_bar = True
                        print(f"-> Swipe erfolglos beendet. Persistierender Balken wird angezeigt: {persistent_bar_rect}")
                    # else: Kein Balken zum Persistieren

                    # Reset der temporären Swipe-Tracking-Variablen
                    swipe_start_x = None
                    swipe_current_x = None
                    swipe_min_x = None
                    swipe_max_x = None
                    resumed_swipe_initial_width = 0 # WICHTIG: Vorsprung zurücksetzen

                    # Prüfen ob nach Swipe-Ende das Viereck noch im Ziel ist
                    if not target_rect.contains(small_rect):
                        print("-> Nach Swipe nicht mehr im Ziel -> Fallen")
                        ready_for_swipe = False
                        is_falling = True
                    else:
                         print("-> Nach Swipe immer noch im Ziel")
                         ready_for_swipe = True
                         is_falling = False

                elif dragging:
                    # ... (unveränderte Logik für Dragging-Ende) ...
                    print("Dragging beendet") # Debug
                    dragging = False
                    if target_rect.contains(small_rect):
                        print("-> Im Ziel gelandet, bereit für Swipe")
                        ready_for_swipe = True
                        is_falling = False
                    else:
                        print("-> Außerhalb des Ziels gelandet, fällt runter")
                        ready_for_swipe = False
                        is_falling = True


        elif event.type == pygame.MOUSEMOTION:
            if is_swiping:
                swipe_current_x = event.pos[0]
                if swipe_min_x is not None and swipe_max_x is not None:
                    # Aktualisiere Min/Max für die *visuelle* Darstellung des Balkens
                    swipe_min_x = min(swipe_min_x, swipe_current_x)
                    swipe_max_x = max(swipe_max_x, swipe_current_x)

                # --- ANGEPASSTE ERFOLGSBEDINGUNG ---
                if swipe_start_x is not None:
                    # Distanz seit dem letzten Klick/Startpunkt
                    current_added_distance = abs(swipe_current_x - swipe_start_x)
                    # Gesamt-effektive Distanz = Alter Balken (Vorsprung) + neue Bewegung
                    total_effective_distance = resumed_swipe_initial_width + current_added_distance

                    # Erfolg wenn Gesamtdistanz reicht
                    if total_effective_distance >= min_swipe_distance:
                        print(f"Swipe erfolgreich erkannt! Gesamt: {total_effective_distance:.2f} (Vorsprung: {resumed_swipe_initial_width:.2f} + Neu: {current_added_distance:.2f}) >= {min_swipe_distance:.2f}")
                        score += 1
                        small_rect.topleft = tuple(start_pos) # Zurück zum Start
                        ready_for_swipe = False
                        is_falling = False
                        is_swiping = False # Stoppt aktives Swipen
                        dragging = False

                        # WICHTIG: Persistierenden Balken bei Erfolg entfernen & Vorsprung resetten
                        display_persistent_swipe_bar = False
                        persistent_bar_rect = None
                        resumed_swipe_initial_width = 0

                        # Reset der Tracking-Variablen
                        swipe_start_x = None
                        swipe_current_x = None
                        swipe_min_x = None
                        swipe_max_x = None
                        # Kein Reset von resumed_swipe_initial_width hier, wurde oben schon gemacht

            elif dragging:
                # ... (unveränderte Dragging-Logik) ...
                old_rect = small_rect.copy()
                potential_x = event.pos[0] + offset_x
                potential_y = event.pos[1] + offset_y
                small_rect.topleft = (potential_x, potential_y)
                collided_target = False
                if not target_rect.contains(old_rect) and small_rect.colliderect(target_rect):
                    collided_target = True
                    if old_rect.right <= target_rect.left and small_rect.right > target_rect.left:
                        small_rect.right = target_rect.left
                    elif old_rect.left >= target_rect.right and small_rect.left < target_rect.right:
                        small_rect.left = target_rect.right
                    elif old_rect.top >= target_rect.bottom and small_rect.top < target_rect.bottom:
                        small_rect.top = target_rect.bottom
                screen_rect = pygame.Rect(0, 0, actual_screen_size[0], actual_screen_size[1])
                small_rect.clamp_ip(screen_rect) # clamp_ip direkt verwenden


    # Spiel-Logik / Physik (Fallen)
    if is_falling and not dragging and not ready_for_swipe and not is_swiping:
        # ... (unveränderte Fall-Logik) ...
        potential_y = small_rect.y + gravity
        potential_rect = small_rect.copy()
        potential_rect.y = potential_y
        screen_height = actual_screen_size[1]
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
                 print("Gefallen und im Ziel gelandet -> Bereit für Swipe")
                 ready_for_swipe = True
             else:
                  print("Gefallen und auf Zielkante (unten) gelandet, aber nicht drin.")
                  ready_for_swipe = False
        else:
            if potential_rect.bottom >= screen_height:
                print("Am unteren Rand angekommen -> Stopp")
                small_rect.bottom = screen_height
                is_falling = False
                ready_for_swipe = False
            else:
                small_rect.y = potential_y


    # Zustandskorrektur: Wenn bereit zum Swipen, aber Objekt nicht mehr im Ziel
    if ready_for_swipe and not is_swiping and not target_rect.contains(small_rect):
        if not dragging:
            print("War bereit zum Swipen, ist aber nicht mehr im Ziel -> Fallen")
            ready_for_swipe = False
            is_falling = True
            # Implizit wird auch der persistente Balken + Vorsprung verschwinden (siehe Zeichnen-Logik)

    # --- Zeichnen ---
    screen.fill(WHITE)

    # Ziel zeichnen
    if use_target_image and target_image is not None:
        screen.blit(target_image, target_rect.topleft)
    else:
        pygame.draw.rect(screen, BLUE, target_rect)

    # Swipe-Linie zeichnen (Grün) und evtl. Fortschritt (Orange)
    if ready_for_swipe:
        pygame.draw.rect(screen, GREEN, swipe_line_rect)

        # Logik zum Zeichnen des orangen Balkens (unverändert)
        bar_to_draw = None
        if is_swiping and swipe_min_x is not None and swipe_max_x is not None:
            # Aktiver Swipe: Berechne aktuellen Balken basierend auf Min/Max
            clamped_orange_x = max(swipe_line_rect.left, swipe_min_x)
            clamped_orange_right = min(swipe_line_rect.right, swipe_max_x)
            clamped_orange_width = max(0, clamped_orange_right - clamped_orange_x)
            if clamped_orange_width > 0:
                 bar_to_draw = pygame.Rect(clamped_orange_x, swipe_line_rect.y, clamped_orange_width, swipe_line_rect.height)
        elif display_persistent_swipe_bar and persistent_bar_rect is not None:
            # Kein aktiver Swipe, aber persistenter Balken soll angezeigt werden
            bar_to_draw = persistent_bar_rect

        # Zeichne den ausgewählten Balken, falls vorhanden
        if bar_to_draw:
            pygame.draw.rect(screen, ORANGE, bar_to_draw)

    else:
        # Wenn nicht bereit für Swipe, alle Swipe-relevanten Zustände zurücksetzen
        display_persistent_swipe_bar = False
        persistent_bar_rect = None
        resumed_swipe_initial_width = 0 # WICHTIG: Vorsprung auch hier zurücksetzen


    # Kleines Viereck zeichnen
    if use_small_image and small_image is not None:
        screen.blit(small_image, small_rect.topleft)
    else:
        if small_rect:
             pygame.draw.rect(screen, RED, small_rect)

    # Score zeichnen
    score_text = font.render(f"Punkte: {score}", True, BLACK)
    screen.blit(score_text, (score_pos_x, score_pos_y))

    # Bildschirm aktualisieren
    pygame.display.flip()

    # Framerate begrenzen
    clock.tick(60)

# Pygame beenden
pygame.quit()
sys.exit()