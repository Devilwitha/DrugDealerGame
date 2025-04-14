# inventory.py (Nutzt persistence.py)
import pygame
import logging
# Importiere die Speicher/Lade-Funktionen
from persistence import load_data, save_data

logger = logging.getLogger(__name__) # Name ist 'inventory'

# --- Konstanten für die Anzeige ---
BOX_SIZE = 48; PADDING = 5; BORDER_WIDTH = 2; MAX_SLOTS = 10
BORDER_COLOR = (200, 200, 200); BG_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255); QUANTITY_COLOR = (200, 200, 0)

class Inventory:
    """
    Verwaltet Items des Spielers, nutzt persistence.py zum Speichern/Laden
    und stellt das Inventar grafisch dar.
    """
    def __init__(self, filepath, max_slots=MAX_SLOTS):
        """
        Initialisiert das Inventar, nutzt persistence.load_data zum Laden.

        Args:
            filepath (str): Pfad zur Speicherdatei.
            max_slots (int): Maximale Anzahl verschiedener Item-Slots.
        """
        self._items = {} # Wird unten nach dem Laden befüllt
        self.max_slots = max_slots
        self.filepath = filepath # Pfad merken für späteres Speichern
        self.font_item = None
        self.font_quantity = None

        # Lade Schriftarten für die Anzeige
        try:
            self.font_item = pygame.font.Font(None, 18)
            self.font_quantity = pygame.font.Font(None, 16)
            logger.debug(f"Inventar {id(self)}: Schriftarten geladen.")
        except Exception as e:
            logger.error(f"Inventar {id(self)}: Schriftarten nicht geladen: {e}.")

        logger.info(f"Inventar {id(self)} wird initialisiert (max. {self.max_slots} Slots).")
        # --- Lade Logik ---
        logger.debug(f"Inventar {id(self)}: Rufe persistence.load_data für '{self.filepath}' auf.")
        loaded_data = load_data(self.filepath, default_data={}) # Standard = leeres Dict

        # --- Inventar-spezifische Validierung der geladenen Daten ---
        if isinstance(loaded_data, dict):
            self._items = {} # Beginne mit leerem Dict für validierte Items
            valid_items_count = 0
            invalid_items_count = 0
            for key, value in loaded_data.items():
                # Prüfe Format (str: positive int) und ob Platz ist
                if isinstance(key, str) and key and isinstance(value, int) and value > 0:
                     if len(self._items) < self.max_slots:
                        self._items[key] = value
                        valid_items_count += 1
                     else:
                        logger.warning(f"Inventar {id(self)}: Geladenes Item '{key}' verworfen (max. {self.max_slots} Slots erreicht).")
                        invalid_items_count += 1
                else:
                    logger.warning(f"Inventar {id(self)}: Ungültiger Eintrag aus Datei '{self.filepath}' ignoriert: '{key}': {value}")
                    invalid_items_count += 1

            if valid_items_count > 0:
                 logger.info(f"Inventar {id(self)}: {valid_items_count} gültige Items nach Validierung übernommen.")
            if invalid_items_count > 0:
                 logger.warning(f"Inventar {id(self)}: {invalid_items_count} ungültige/überzählige Einträge wurden ignoriert.")
        else:
            logger.warning(f"Inventar {id(self)}: Geladene Daten aus '{self.filepath}' waren kein Dictionary. Inventar bleibt leer.")
            self._items = {}

        # Logge abschließenden Zustand
        if not self._items:
            logger.info(f"Inventar {id(self)} ist nach Initialisierung/Laden leer.")
        else:
            logger.debug(f"Inventar {id(self)} Inhalt nach Init/Load: {self._items}")


    def save_inventory(self):
        """Speichert das aktuelle Inventar mit der allgemeinen save_data Funktion."""
        logger.debug(f"Inventar {id(self)}: Rufe persistence.save_data auf für Pfad '{self.filepath}'.")
        success = save_data(self._items, self.filepath)
        if not success:
            logger.error(f"Inventar {id(self)}: Speichern nach '{self.filepath}' fehlgeschlagen.")
        return success


    # --- Methoden zur Item-Verwaltung ---
    def add_item(self, item_name, quantity=1):
        """Fügt Items hinzu. Prüft auf Gültigkeit und Platz."""
        if not isinstance(item_name, str) or not item_name: logger.warning(f"Inv {id(self)} Add: Ungültiger Name: '{item_name}'"); return False
        if not isinstance(quantity, int) or quantity < 1: logger.warning(f"Inv {id(self)} Add: Ungültige Anzahl {quantity} für '{item_name}'"); return False
        if item_name not in self._items and len(self._items) >= self.max_slots: logger.warning(f"Inv {id(self)} Add: Voll ({len(self._items)}/{self.max_slots}). Kann '{item_name}' nicht hinzufügen."); return False
        current_quantity = self._items.get(item_name, 0); self._items[item_name] = current_quantity + quantity
        logger.info(f"Inv {id(self)}: {quantity}x '{item_name}' hinzugefügt. Gesamt: {self._items[item_name]}"); return True

    def remove_item(self, item_name, quantity=1):
        """Entfernt Items. Löscht den Eintrag, wenn Menge 0 erreicht."""
        if not isinstance(item_name, str) or not item_name: logger.warning(f"Inv {id(self)} Remove: Ungültiger Name: '{item_name}'"); return False
        if not isinstance(quantity, int) or quantity < 1: logger.warning(f"Inv {id(self)} Remove: Ungültige Anzahl {quantity} für '{item_name}'"); return False
        current_quantity = self._items.get(item_name, 0)
        if current_quantity >= quantity:
            new_quantity = current_quantity - quantity; self._items[item_name] = new_quantity
            logger.info(f"Inv {id(self)}: {quantity}x '{item_name}' entfernt. Verbleibend: {new_quantity}")
            if new_quantity == 0: del self._items[item_name]; logger.debug(f"Inv {id(self)}: '{item_name}' komplett entfernt.")
            return True
        else: logger.warning(f"Inv {id(self)} Remove: Nicht genug von '{item_name}' (hat {current_quantity}, braucht {quantity})."); return False

    def has_item(self, item_name, quantity=1):
        """Prüft, ob eine Mindestmenge eines Items vorhanden ist."""
        if not isinstance(item_name, str) or not item_name: return False
        if not isinstance(quantity, int) or quantity < 1: return False
        return self._items.get(item_name, 0) >= quantity

    def get_items(self):
        """Gibt eine Kopie des Inventar-Dictionaries zurück."""
        return self._items.copy()

    def get_item_list_for_display(self):
        """Gibt Items als Liste von (Name, Menge)-Tupeln zurück (für die Anzeige)."""
        return list(self._items.items())


    # --- Display Methode ---
    def display(self, screen, position):
        """Zeichnet das Inventar als Kastenreihe auf den Bildschirm."""
        if not self.font_item or not self.font_quantity:
             # logger.warning(f"Inventar {id(self)}: Kann nicht zeichnen, Schriftarten fehlen.")
             return # Frühzeitiger Ausstieg

        start_x, start_y = position
        items_to_display = self.get_item_list_for_display()

        # Zeichne für jeden möglichen Slot einen Kasten.
        for i in range(self.max_slots):
            box_x = start_x + i * (BOX_SIZE + PADDING)
            box_rect = pygame.Rect(box_x, start_y, BOX_SIZE, BOX_SIZE)

            pygame.draw.rect(screen, BG_COLOR, box_rect)
            pygame.draw.rect(screen, BORDER_COLOR, box_rect, BORDER_WIDTH)

            # Wenn für diesen Slot ein Item existiert
            if i < len(items_to_display):
                item_name, quantity = items_to_display[i]

                # Zeichne Item-Namen (gekürzt)
                try:
                    max_name_len = 7
                    display_name = item_name if len(item_name) <= max_name_len else item_name[:max_name_len-1] + "."
                    name_surf = self.font_item.render(display_name, True, TEXT_COLOR)
                    name_rect = name_surf.get_rect(centerx=box_rect.centerx, top=box_rect.top + PADDING)
                    screen.blit(name_surf, name_rect)
                except Exception as e:
                    logger.error(f"Inv {id(self)} Display: Fehler Render Name '{item_name}': {e}")

                # Zeichne Item-Anzahl (wenn > 0)
                if quantity > 0:
                    try:
                        quantity_str = str(quantity)
                        quantity_surf = self.font_quantity.render(quantity_str, True, QUANTITY_COLOR)
                        quantity_rect = quantity_surf.get_rect(bottomright=box_rect.bottomright - pygame.Vector2(PADDING, PADDING))
                        screen.blit(quantity_surf, quantity_rect)
                    except Exception as e:
                         logger.error(f"Inv {id(self)} Display: Fehler Render Anzahl '{item_name}': {e}")