# items.py (Korrektur: Robuster Fallback im Konstruktor, Workaround entfernt)
import pygame
import logging
import os
import time

logger = logging.getLogger(__name__)

# --- Farbdefinitionen ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREEN = (0, 200, 0)
RED = (255, 0, 0); BLUE = (0, 0, 255); MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)

# --- Item Definitions ---
ICON_FILES = {
    "Blumentopf": "blumentopf_icon.png", "Sack Erde": "sack_erde_icon.png",
    "Weed Seeds": "weed_seeds_icon.png", "Weed": "butt_icon.png",
    "Verpackstation": "verpackstation_icon.png"
}

PLACED_ITEM_STATE_FILES = {
    "Blumentopf": {
        'ohneErde': "blumentopf_ohneErde.png", 'ohneSeed': "blumentopf_ohneSeed.png",
        'giessen': "blumentopf_giessen.png", 'growing': "blumentopf_growing.png",
        'readyToEarn': "blumentopf_ready.png"
    },
    "Verpackstation": {'default': "verpackstation.png"}
}

# --- Item Konstanten (Modulebene) ---
PLACEABLE_ITEMS = ["Blumentopf", "Verpackstation"]
COMPLEX_ITEMS = ["Blumentopf"]

# --- PlacedItem Class ---
class PlacedItem(pygame.sprite.Sprite):
    STATES = ['ohneErde', 'ohneSeed', 'giessen', 'growing', 'readyToEarn', 'default']

    def __init__(self, world_x, world_y, item_type, images_for_states, fallback_image, grow_time_seconds=0, state=None, timer_end_timestamp=None):
        logger.debug(f"--- PlacedItem.__init__ start for {item_type} ---")
        # Explizit eine leere Sequenz von Gruppen übergeben
        super().__init__(*[])
        # Alive Check hier entfernt, da es immer False sein wird, bis es zu Gruppen hinzugefügt wird.

        self.item_type = item_type
        self.images_for_states = images_for_states
        # Behalte das übergebene Fallback-Bild ODER erstelle ein neues, falls keins da ist
        self.fallback_image = fallback_image if fallback_image else pygame.Surface((32, 32))
        if not fallback_image:
             try:
                 self.fallback_image.fill(MAGENTA)
             except Exception as e_fill: # Fange Fehler ab, falls Surface ungültig
                 logger.error(f"Konnte Fallback-Surface nicht füllen: {e_fill}. Erstelle neues.")
                 self.fallback_image = pygame.Surface((32, 32)); self.fallback_image.fill(MAGENTA)

        logger.debug(f"  Init: Fallback image used/created: {self.fallback_image}")

        # Bestimme initialen Zustand
        initial_state_provided = state # Merken, ob Zustand übergeben wurde
        if state is None:
            if self.item_type == "Verpackstation": self.state = 'default'
            elif self.item_type == "Blumentopf": self.state = 'ohneErde'
            else: self.state = 'default'; logger.warning(f"Kein expliziter Startzustand für {item_type} definiert, nutze 'default'.")
            logger.debug(f"  Init: No state provided, determined state: {self.state}")
        elif state in self.STATES:
             self.state = state
             logger.debug(f"  Init: Valid state provided: {self.state}")
        else:
             logger.warning(f"Ungültiger Startzustand '{state}' für {item_type}. Nutze Fallback.")
             self.state = 'default' if item_type not in COMPLEX_ITEMS else 'ohneErde'
             logger.debug(f"  Init: Invalid state provided, fallback state: {self.state}")

        self.grow_time_seconds = grow_time_seconds if self.item_type in COMPLEX_ITEMS else 0
        logger.debug(f"  Init: Grow time set to: {self.grow_time_seconds}")

        self.timer_end_timestamp = None
        if self.item_type in COMPLEX_ITEMS and timer_end_timestamp:
            try:
                self.timer_end_timestamp = float(timer_end_timestamp)
                logger.debug(f"  Init: Timer loaded: {self.timer_end_timestamp}")
            except (ValueError, TypeError):
                logger.warning(f"Ungültiger Timer-TS '{timer_end_timestamp}' für {item_type}, ignoriere.")
                self.timer_end_timestamp = None

        # Initialisiere Bild und Rect, dann rufe update_appearance auf
        self.image = None
        self.rect = None
        logger.debug(f"  Init: Calling update_appearance() for state '{self.state}'...")
        self.update_appearance() # Versucht self.image und self.rect zu setzen
        logger.debug(f"  Init: After update_appearance(), self.image={self.image}, self.rect={self.rect}")

        # Prüfe, ob Bild ODER Rect nach update_appearance ungültig sind
        if not self.rect or not self.image:
            logger.warning(f"!!! Init: Bild/Rect für {item_type} (State: {self.state}) nach update_appearance() ungültig ({self.image}, {self.rect}). Erzeuge Notfall-Fallback (Farbiges Rechteck).")
            # Erzeuge IMMER ein Fallback-Rechteck/Bild, wenn etwas schiefging
            fallback_size = 32 # Standardgröße TILE_SIZE
            try:
                # Versuche, Größe vom übergebenen Fallback-Bild zu nehmen, falls vorhanden
                if fallback_image:
                     # Prüfe, ob fallback_image eine gültige Surface ist
                     if isinstance(fallback_image, pygame.Surface):
                         fallback_size = fallback_image.get_width() # Annahme: quadratisch
                     else:
                         logger.warning("Übergebenes fallback_image war keine Surface, nutze Standardgröße 32.")
            except Exception as e_get_fb_size:
                logger.warning(f"Fehler beim Holen der Fallback-Größe: {e_get_fb_size}. Nutze Standardgröße 32.")
                fallback_size = 32

            try:
                self.image = pygame.Surface((fallback_size, fallback_size))
                self.image.fill(MAGENTA) # Standard-Fallback-Farbe
                pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 1) # Optional: Rahmen
                logger.debug(f"!!! Init: Notfall-Fallback Bild erstellt: {self.image}")
                self.rect = self.image.get_rect()
                logger.debug(f"!!! Init: Notfall-Fallback Rect erstellt: {self.rect}")
            except Exception as e_create_fb:
                 logger.critical(f"!!! Init: KRITISCH - Konnte Notfall-Fallback Bild/Rect nicht erstellen: {e_create_fb}")
                 # Absoluter Notfall: Definiere zumindest ein Rect, um Abstürze zu vermeiden
                 self.image = None # Kein Bild verfügbar
                 self.rect = pygame.Rect(0, 0, fallback_size, fallback_size)

        # Setze den Mittelpunkt des (jetzt hoffentlich immer) vorhandenen Rects
        if self.rect:
             self.rect.center = (world_x, world_y)
        else:
             # Dies sollte nach der obigen Logik eigentlich nie passieren
             logger.critical(f"!!! Init: KRITISCH - self.rect ist am Ende des Konstruktors immer noch None für {item_type}!")
             # Erstelle einen Notfall-Rect, um Totalabsturz zu verhindern
             self.rect = pygame.Rect(world_x - 16, world_y - 16, 32, 32)


        # Der explizite self.kill() Aufruf bleibt entfernt.
        # Der Workaround (add/remove group) wird entfernt, da das Problem woanders lag.

        # Die alive() Prüfung am Ende wird immer False ergeben, bis das Objekt zu einer Gruppe hinzugefügt wird.
        logger.debug(f"--- PlacedItem.__init__ end for {item_type}. Final rect: {self.rect}, Alive (expect False until added to group): {self.alive()} ---")


    def update_appearance(self):
        """Updates the item's image based on its current state."""
        logger.debug(f"--- update_appearance for {self.item_type} (State: {self.state}) ---")
        center = self.rect.center if hasattr(self, 'rect') and self.rect else None
        logger.debug(f"  Center before: {center}")

        # Versuche spezifisches Bild zu laden
        img = self.images_for_states.get(self.state)
        logger.debug(f"  Image found for state '{self.state}' in provided dict: {img is not None}")

        # Wenn nicht gefunden, nutze Fallback
        if not img:
            logger.warning(f"  Bild für Zustand '{self.state}' nicht im Dict gefunden/geladen.")
            # Spezielles Fallback für Verpackstation (Gelb)
            if self.item_type == "Verpackstation":
                logger.warning(f"  Erstelle gelbes Fallback für Verpackstation.")
                fb_width = 32; fb_height = 32
                if self.fallback_image: # Nutze Größe des generischen Fallbacks, falls vorhanden
                    try: fb_width = self.fallback_image.get_width(); fb_height = self.fallback_image.get_height()
                    except: pass
                self.image = pygame.Surface((fb_width, fb_height))
                self.image.fill(YELLOW)
                pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 1)
            # Generisches Fallback (Magenta) für andere Items
            else:
                logger.warning(f"  Nutze generisches Fallback (Magenta) für {self.item_type}.")
                self.image = self.fallback_image # Sollte im Konstruktor sichergestellt worden sein
                if not self.image: # Absolute Notfallsicherung
                    logger.critical(f"  KATALER FEHLER: Generisches Fallback ist None in update_appearance für {self.item_type}!")
                    fb_width = 32; fb_height = 32
                    if hasattr(self, 'rect') and self.rect: fb_width = self.rect.width; fb_height = self.rect.height
                    self.image = pygame.Surface((fb_width, fb_height)); self.image.fill(RED)
                    pygame.draw.line(self.image, BLACK, (0, 0), self.image.get_size(), 2)
                    pygame.draw.line(self.image, BLACK, (0, self.image.get_height()), (self.image.get_width(), 0), 2)
            logger.debug(f"  Using fallback image: {self.image}")
        # Wenn spezifisches Bild gefunden wurde
        else:
            self.image = img
            logger.debug(f"  Using specific image: {self.image}")

        # Aktualisiere Rect basierend auf dem (neuen) Bild
        current_rect_temp = None
        if self.image and isinstance(self.image, pygame.Surface): # Prüfe ob Bild gültig ist
             try:
                 current_rect_temp = self.image.get_rect()
                 logger.debug(f"  Got rect from image: {current_rect_temp}")
                 if center: # Stelle alten Mittelpunkt wieder her, falls vorhanden
                     current_rect_temp.center = center
                     logger.debug(f"  Restored center: {current_rect_temp.center}")
             except Exception as e_getrect:
                   logger.error(f"  Error calling get_rect() on image {self.image}: {e_getrect}")
                   current_rect_temp = None
        else:
             logger.error(f"  self.image is None or invalid, cannot get rect! Image: {self.image}")

        self.rect = current_rect_temp # Setze self.rect (kann None sein, wenn alles fehlschlägt)
        logger.debug(f"  --- end update_appearance. self.rect is now: {self.rect} ---")


    def update(self, dt):
        """Updates the item, e.g., checking growth timer."""
        if self.item_type in COMPLEX_ITEMS and self.state == 'growing' and self.timer_end_timestamp is not None:
            if time.time() >= self.timer_end_timestamp:
                logger.info(f"Item '{self.item_type}' fertig gewachsen!")
                self.state = 'readyToEarn'
                self.timer_end_timestamp = None
                self.update_appearance()

    def interact(self):
        """Handles interaction with the item, changing its state or logging."""
        initial_state = self.state
        action_taken = False

        if self.item_type == "Verpackstation":
            logger.info(f"Interaktion mit {self.item_type}. Aktuell keine Aktion implementiert.")
            action_taken = False

        elif self.item_type == "Blumentopf":
            if self.state == 'giessen':
                 self.state = 'growing'
                 self.timer_end_timestamp = time.time() + self.grow_time_seconds
                 logger.info(f"{self.item_type} Wachsen gestartet (Dauer: {self.grow_time_seconds}s). Ende: {self.timer_end_timestamp}")
                 action_taken = True
            elif self.state == 'growing':
                 if self.timer_end_timestamp:
                     remaining = self.timer_end_timestamp - time.time()
                     logger.info(f"{self.item_type} wächst noch (ca. {max(0, remaining):.0f}s).")
                 else: logger.warning(f"{self.item_type} im Zustand 'growing' ohne Timer?")
                 action_taken = False
            elif self.state in ['ohneErde', 'ohneSeed', 'readyToEarn']:
                 logger.debug(f"{self.item_type}.interact() im Zustand '{self.state}' aufgerufen (Aktion in game.py).")
                 action_taken = False
            else:
                 logger.warning(f"Unbekannter Interaktionszustand '{self.state}' für {self.item_type}")
                 action_taken = False
        else:
            logger.warning(f"Interaktion für unbekannten Item-Typ '{self.item_type}' nicht definiert.")
            action_taken = False

        if action_taken and self.state != initial_state:
            self.update_appearance()
            logger.info(f"{self.item_type} Zustand geändert: '{initial_state}' -> '{self.state}'.")
        return action_taken

# --- Asset Loading Function ---
def load_item_assets(image_folder_path, placed_item_size, icon_size, load_image_func):
    """Loads all item icons and placed item state images."""
    logger.info("Lade Item-Assets...")
    item_icons = {}
    placed_item_images = {}

    logger.debug(f"Lade Inventar-Icons (Zielgröße: {icon_size})...")
    for name, filename in ICON_FILES.items():
        icon = load_image_func(filename, alpha=True, scale_to=icon_size)
        if icon: item_icons[name] = icon; logger.debug(f"  -> Icon '{name}' geladen: {filename}")
        else: item_icons[name] = None; logger.warning(f"Icon '{name}' konnte nicht geladen werden ({filename}).") # Warning hinzugefügt

    logger.debug(f"Lade platzierte Item-Zustandsbilder (Zielgröße: {(placed_item_size, placed_item_size)})...")
    # Erstelle Fallback sicher
    try:
        fallback_placed_image = pygame.Surface((placed_item_size, placed_item_size)); fallback_placed_image.fill(MAGENTA)
        logger.debug(f"  Generisches Fallback erstellt: {fallback_placed_image}")
    except Exception as e_fb_create:
        logger.critical(f"KRITISCH: Konnte generisches Fallback-Bild nicht erstellen: {e_fb_create}")
        fallback_placed_image = None # Signalisiert Problem

    for item_type, state_files in PLACED_ITEM_STATE_FILES.items():
        placed_item_images[item_type] = {}
        logger.debug(f"  Lade Zustände für: {item_type}")
        all_states_loaded_for_type = True
        for state_name, filename in state_files.items():
            img = load_image_func(filename, alpha=True, scale_to=(placed_item_size, placed_item_size))
            if img:
                placed_item_images[item_type][state_name] = img
                logger.debug(f"    -> Bild für Zustand '{state_name}' geladen: {filename} -> {img}")
            else:
                all_states_loaded_for_type = False
                logger.warning(f"    -> Zustand '{state_name}' für '{item_type}' konnte nicht geladen werden ({filename}).")
        if not all_states_loaded_for_type:
             logger.warning(f"  -> Nicht alle Zustandsbilder für '{item_type}' konnten geladen werden.")

    logger.info("Item-Assets Ladevorgang abgeschlossen.")
    # Gebe Assets zurück, auch wenn Fallback-Erstellung fehlschlug (Konstruktor hat eigenen Fallback)
    return item_icons, placed_item_images, fallback_placed_image