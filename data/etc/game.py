# main.py
import pygame
import sys
import logging # Logging Modul importieren

# --- Logging Konfiguration (am besten ganz am Anfang) ---
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
log_level = logging.DEBUG # Zeigt alle Level von DEBUG bis CRITICAL an. Für weniger Details: logging.INFO
logging.basicConfig(level=log_level, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
# Optional: Logging in eine Datei schreiben
# file_handler = logging.FileHandler("game.log", mode='w') # 'w' überschreibt bei jedem Start
# file_handler.setFormatter(logging.Formatter(log_format))
# logging.getLogger().addHandler(file_handler)

# Logger für dieses Hauptmodul holen
logger = logging.getLogger(__name__) # __name__ wird zu "__main__"

logger.info("Spiel wird initialisiert...") # Beispiel für eine Info-Nachricht

# --- Importiere eigene Module NACH der Logging-Konfiguration ---
# Damit stellen wir sicher, dass sie die Konfiguration übernehmen
from player import Player
from npc import NPC
from camera import Camera
from inventory import Inventory

# --- Konstanten ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60
WORLD_WIDTH = SCREEN_WIDTH * 3
WORLD_HEIGHT = SCREEN_HEIGHT * 2
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# --- Initialisierung ---
try:
    pygame.init()
    logger.info("Pygame erfolgreich initialisiert.")
except Exception as e:
    logger.critical(f"Pygame konnte nicht initialisiert werden: {e}")
    sys.exit()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Top-Down Zelda-Like")
clock = pygame.time.Clock()
logger.debug("Screen und Clock erstellt.")

# --- Spielobjekte erstellen ---
player_start_x = SCREEN_WIDTH // 2
player_start_y = SCREEN_HEIGHT // 2
player = Player(player_start_x, player_start_y, TILE_SIZE // 2, RED)

inventory = Inventory()
inventory.add_item("Schlüssel")
inventory.add_item("Trank", 3)
inventory.add_item("Ungültig", quantity=0) # Testet Fehlerfall im Logging

all_sprites = pygame.sprite.Group()
npcs = pygame.sprite.Group()

npc1 = NPC(TILE_SIZE * 5, TILE_SIZE * 5, TILE_SIZE // 2, BLUE)
npc2 = NPC(SCREEN_WIDTH + TILE_SIZE * 3, TILE_SIZE * 8, TILE_SIZE // 2, GREEN)
all_sprites.add(player, npc1, npc2)
npcs.add(npc1, npc2)
logger.info(f"{len(all_sprites)} Sprites insgesamt erstellt.")

camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)

# --- Spiel-Loop ---
running = True
logger.info("Spiel-Loop startet.")
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            logger.info("QUIT Event empfangen. Spiel wird beendet.")
            running = False
        if event.type == pygame.KEYDOWN:
            logger.debug(f"KeyDown Event: {event.key} ({pygame.key.name(event.key)})")
            if event.key == pygame.K_i:
                logger.info("Inventar-Ansicht angefordert (Konsole).")
                print("--- Inventar ---")
                items = inventory.get_items()
                if items:
                    for item, count in items.items():
                        print(f"{item}: {count}")
                else:
                    print("(Leer)")
                print("----------------")
            # Beispiel: Item entfernen zum Testen
            if event.key == pygame.K_r:
                 if inventory.remove_item("Trank"):
                     logger.info("Trank manuell entfernt.")
                 else:
                     logger.warning("Konnte Trank nicht manuell entfernen (nicht genug?).")


    # --- Update ---
    keys = pygame.key.get_pressed()
    player.update(keys, camera.get_current_screen_rect())

    reposition_player = camera.update(player)
    if reposition_player:
         player.prevent_immediate_exit()

    npcs.update()

    # --- Draw ---
    screen.fill(BLACK)

    world_rect_on_screen = camera.apply_rect(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
    pygame.draw.rect(screen, WHITE, world_rect_on_screen, 1)

    visible_sprites = 0
    for sprite in all_sprites:
        if camera.get_current_screen_rect().colliderect(sprite.rect):
            screen.blit(sprite.image, camera.apply(sprite))
            visible_sprites += 1
    # logger.debug(f"{visible_sprites}/{len(all_sprites)} Sprites sichtbar.") # Kann sehr 'noisy' sein

    # UI Zeichnen
    try:
        font = pygame.font.Font(None, 30)
        pos_text = font.render(f"Pos: ({int(player.rect.centerx)}, {int(player.rect.centery)}) Cam: ({camera.camera_rect.x}, {camera.camera_rect.y})", True, WHITE)
        screen.blit(pos_text, (10, 10))
    except Exception as e:
        logger.error(f"Fehler beim Rendern des UI-Textes: {e}")


    pygame.display.flip()
    clock.tick(FPS)

# --- Spiel beenden ---
logger.info("Spiel-Loop beendet.")
pygame.quit()
logger.info("Pygame beendet.")
sys.exit()