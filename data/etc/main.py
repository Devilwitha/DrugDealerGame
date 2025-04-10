# main.py
import pygame
import sys
from player import Player
from npc import NPC
from camera import Camera
from inventory import Inventory

# --- Konstanten ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32 # Beispiel-Grösse für Kacheln/Raster
FPS = 60

# Beispiel-Weltgrösse (in Pixeln) - grösser als der Bildschirm
WORLD_WIDTH = SCREEN_WIDTH * 3
WORLD_HEIGHT = SCREEN_HEIGHT * 2

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# --- Initialisierung ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Top-Down Zelda-Like")
clock = pygame.time.Clock()

# --- Spielobjekte erstellen ---
# Spieler starten etwa in der Mitte des ersten Bildschirms
player_start_x = SCREEN_WIDTH // 2
player_start_y = SCREEN_HEIGHT // 2
player = Player(player_start_x, player_start_y, TILE_SIZE // 2, RED) # Roter Kreis als Spieler

inventory = Inventory()
# Füge zum Testen ein Item hinzu
inventory.add_item("Schlüssel")
inventory.add_item("Trank", 3)

# Gruppen für Sprites
all_sprites = pygame.sprite.Group()
npcs = pygame.sprite.Group()

# Erstelle ein paar NPCs an verschiedenen Stellen der Welt
npc1 = NPC(TILE_SIZE * 5, TILE_SIZE * 5, TILE_SIZE // 2, BLUE) # Blauer Kreis als NPC
npc2 = NPC(SCREEN_WIDTH + TILE_SIZE * 3, TILE_SIZE * 8, TILE_SIZE // 2, GREEN) # Grüner Kreis auf einem anderen "Bildschirm"
all_sprites.add(player, npc1, npc2)
npcs.add(npc1, npc2)

# Kamera erstellen
camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)

# --- Spiel-Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # Beispiel: Inventar öffnen/schliessen (sehr einfach)
            if event.key == pygame.K_i:
                print("--- Inventar ---")
                for item, count in inventory.get_items().items():
                    print(f"{item}: {count}")
                print("----------------")


    # --- Update ---
    keys = pygame.key.get_pressed()
    player.update(keys, camera.get_current_screen_rect()) # Spieler bewegt sich nur innerhalb des aktuellen Kamerabereichs

    # Kamera aktualisieren (prüft, ob Bildschirm gewechselt werden muss)
    # reposition_player ist eine Flag, die sagt ob der Spieler nach dem Screenwechsel neu positioniert wurde
    reposition_player = camera.update(player)
    if reposition_player:
         # Wenn der Spieler neu positioniert wurde, sorge dafür, dass er nicht sofort wieder den Screen wechselt
         player.prevent_immediate_exit()


    # NPCs aktualisieren (falls sie Bewegung oder Logik haben)
    # Hier könnten NPCs basierend auf der Kamera-Position aktiviert/deaktiviert werden
    npcs.update() # Momentan tun NPCs nichts im Update

    # --- Draw ---
    screen.fill(BLACK) # Hintergrund löschen (später durch Welt-Grafik ersetzen)

    # --- Zeichne die Spielwelt (relativ zur Kamera) ---
    # Hier würdest du normalerweise deine Karten-Kacheln zeichnen
    # Beispiel: Zeichne einen Rand um die Welt (nur zum Debuggen)
    world_rect_on_screen = camera.apply_rect(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
    pygame.draw.rect(screen, WHITE, world_rect_on_screen, 1)

    # Zeichne alle Sprites relativ zur Kamera
    for sprite in all_sprites:
        # Prüfe, ob der Sprite überhaupt im aktuellen Kamerabereich sichtbar ist
        if camera.get_current_screen_rect().colliderect(sprite.rect):
            screen.blit(sprite.image, camera.apply(sprite))

    # --- Zeichne UI (nicht von Kamera beeinflusst) ---
    # Einfache Anzeige der Spieler-Koordinaten (Weltkoordinaten)
    font = pygame.font.Font(None, 30)
    pos_text = font.render(f"Pos: ({int(player.rect.centerx)}, {int(player.rect.centery)}) Cam: ({camera.camera_rect.x}, {camera.camera_rect.y})", True, WHITE)
    screen.blit(pos_text, (10, 10))

    # --- Display aktualisieren ---
    pygame.display.flip()

    # --- Framerate begrenzen ---
    clock.tick(FPS)

# --- Spiel beenden ---
pygame.quit()
sys.exit()