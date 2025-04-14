import pygame
import logging
import os
import time # Needed for PlacedItem interaction timer logic

logger = logging.getLogger(__name__)

# --- Item Definitions ---
ICON_FILES = {
    "Blumentopf": "blumentopf_icon.png",
    "Sack Erde": "sack_erde_icon.png",
    "Weed Seeds": "weed_seeds_icon.png"
}

PLACED_ITEM_STATE_FILES = {
    "Blumentopf": {
        'ohneErde': "blumentopf_ohneErde.png",
        'ohneSeed': "blumentopf_ohneSeed.png",
        'giessen': "blumentopf_giessen.png",
        'growing': "blumentopf_growing.png",
        'readyToEarn': "blumentopf_ready.png"
    }
    # Add other placeable items here
}

MAGENTA = (255, 0, 255) # Fallback color

# --- PlacedItem Class ---
class PlacedItem(pygame.sprite.Sprite):
    STATES = ['ohneErde', 'ohneSeed', 'giessen', 'growing', 'readyToEarn']

    def __init__(self, world_x, world_y, item_type, images_for_states, fallback_image, grow_time_seconds, state='ohneErde', timer_end_timestamp=None): # Added grow_time_seconds
        super().__init__()
        self.item_type = item_type
        self.images_for_states = images_for_states
        self.fallback_image = fallback_image if fallback_image else pygame.Surface((32, 32)) # Default fallback size? Or pass size? Passed fallback is better.
        if not fallback_image: self.fallback_image.fill(MAGENTA)
        self.state = state if state in self.STATES else 'ohneErde'
        self.grow_time_seconds = grow_time_seconds # Store grow time

        try:
            self.timer_end_timestamp = float(timer_end_timestamp) if timer_end_timestamp else None
        except (ValueError, TypeError):
            self.timer_end_timestamp = None
            logger.warning(f"Ungültiger Timer-TS '{timer_end_timestamp}' für {item_type}")

        self.image = None
        self.rect = None
        self.update_appearance() # Setzt initiales Bild und Rect

        if self.rect:
            self.rect.center = (world_x, world_y) # Position setzen
        else:
            logger.error(f"Konnte Rect für PlacedItem {item_type} nicht initial setzen!")
            self.kill()

    def update_appearance(self):
        """Updates the item's image based on its current state."""
        center = self.rect.center if hasattr(self, 'rect') and self.rect else None
        self.image = self.images_for_states.get(self.state, self.fallback_image)
        if not self.image:
            logger.critical(f"Kein Bild für State '{self.state}' in {self.item_type} ODER Fallback!")
            # Create a noticeable error surface if everything fails
            self.image = pygame.Surface((self.fallback_image.get_width() if self.fallback_image else 32, self.fallback_image.get_height() if self.fallback_image else 32))
            self.image.fill(RED)
            pygame.draw.line(self.image, BLACK, (0, 0), self.image.get_size(), 2)
            pygame.draw.line(self.image, BLACK, (0, self.image.get_height()), (self.image.get_width(), 0), 2)

        self.rect = self.image.get_rect()
        if center:
            self.rect.center = center # Restore previous center

    def update(self, dt):
        """Updates the item, e.g., checking growth timer."""
        if self.state == 'growing' and self.timer_end_timestamp is not None:
            if time.time() >= self.timer_end_timestamp:
                logger.info(f"Item '{self.item_type}' fertig gewachsen!")
                self.state = 'readyToEarn'
                self.timer_end_timestamp = None
                self.update_appearance()

    def interact(self):
        """Handles interaction with the item, changing its state."""
        initial_state = self.state
        action_taken = False
        if self.state == 'ohneErde':
            self.state = 'ohneSeed'
            action_taken = True
        elif self.state == 'ohneSeed':
            self.state = 'giessen'
            action_taken = True
        elif self.state == 'giessen':
            self.state = 'growing'
            self.timer_end_timestamp = time.time() + self.grow_time_seconds # Use stored grow time
            logger.info(f"{self.item_type} Wachsen gestartet (Dauer: {self.grow_time_seconds}s).")
            action_taken = True
        elif self.state == 'growing':
            if self.timer_end_timestamp:
                remaining = self.timer_end_timestamp - time.time()
                logger.info(f"{self.item_type} wächst noch (ca. {max(0, remaining):.0f}s).")
            else:
                 logger.warning(f"{self.item_type} im Zustand 'growing' ohne Timer?")
            action_taken = False # No state change just by interacting while growing
        elif self.state == 'readyToEarn':
            logger.info(f"{self.item_type} Ernte-Interaktion.")
            # TODO: Implement actual earning/harvesting logic here
            self.state = 'ohneErde' # Reset state after harvest
            logger.info(f"{self.item_type} -> 'ohneErde'.")
            action_taken = True # Reset state
        else:
            logger.warning(f"Unbekannter Interaktionszustand '{self.state}' für {self.item_type}")
            action_taken = False

        if self.state != initial_state:
            self.update_appearance()
            logger.info(f"{self.item_type} Zustand geändert: '{initial_state}' -> '{self.state}'.")
        return action_taken


# --- Asset Loading Function ---
def load_item_assets(image_folder_path, placed_item_size, icon_size, load_image_func):
    """
    Loads all item icons and placed item state images.

    Args:
        image_folder_path (str): Path to the main image directory.
        placed_item_size (int): The size (width/height) for placed item state images.
        icon_size (tuple): The (width, height) for inventory icons.
        load_image_func (function): The function to use for loading images (e.g., game.load_image_asset).

    Returns:
        tuple: (item_icons_dict, placed_item_images_dict, fallback_placed_image_surface)
    """
    logger.info("Lade Item-Assets...")
    item_icons = {}
    placed_item_images = {}

    # --- Lade Inventar-Icons ---
    logger.debug(f"Lade Inventar-Icons (Zielgröße: {icon_size})...")
    for name, filename in ICON_FILES.items():
        icon = load_image_func(filename, alpha=True, scale_to=icon_size)
        if icon:
            item_icons[name] = icon
        else:
            logger.warning(f"Konnte Icon für '{name}' nicht laden: {filename}")
            item_icons[name] = None # Explicitly store None if loading failed

    # --- Lade platzierte Item Bilder ---
    logger.debug(f"Lade platzierte Item-Zustandsbilder (Zielgröße: {(placed_item_size, placed_item_size)})...")
    # Erstelle generisches Fallback-Bild
    fallback_placed_image = pygame.Surface((placed_item_size, placed_item_size))
    fallback_placed_image.fill(MAGENTA)
    fallback_placed_image.set_colorkey(MAGENTA) # Make magenta transparent if needed later

    for item_type, state_files in PLACED_ITEM_STATE_FILES.items():
        placed_item_images[item_type] = {}
        logger.debug(f"  Lade Zustände für: {item_type}")
        for state_name, filename in state_files.items():
            img = load_image_func(filename, alpha=True, scale_to=(placed_item_size, placed_item_size))
            if img:
                placed_item_images[item_type][state_name] = img
            else:
                logger.warning(f"  Fehlendes Zustandsbild für {item_type} -> {state_name} ({filename})")
                # Optional: Use the generic fallback here? Or let PlacedItem handle it?
                # placed_item_images[item_type][state_name] = fallback_placed_image

    logger.info("Item-Assets Ladevorgang abgeschlossen.")
    return item_icons, placed_item_images, fallback_placed_image