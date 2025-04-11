# inventory.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "inventory")

class Inventory:
    def __init__(self):
        self._items = {}
        logger.info(f"Inventar {id(self)} erstellt.")

    def add_item(self, item_name, quantity=1):
        if not isinstance(item_name, str) or not item_name:
            logger.warning(f"Inventar {id(self)}: Ungültiger Item-Name beim Hinzufügen versucht: {item_name}")
            return
        if not isinstance(quantity, int) or quantity < 1:
            logger.warning(f"Inventar {id(self)}: Ungültige Anzahl ({quantity}) für Item '{item_name}' beim Hinzufügen versucht.")
            return

        self._items[item_name] = self._items.get(item_name, 0) + quantity
        logger.info(f"Inventar {id(self)}: {quantity}x '{item_name}' hinzugefügt. Gesamt: {self._items[item_name]}")

    def remove_item(self, item_name, quantity=1):
        if not isinstance(item_name, str) or not item_name:
            logger.warning(f"Inventar {id(self)}: Ungültiger Item-Name beim Entfernen versucht: {item_name}")
            return False
        if not isinstance(quantity, int) or quantity < 1:
            logger.warning(f"Inventar {id(self)}: Ungültige Anzahl ({quantity}) für Item '{item_name}' beim Entfernen versucht.")
            return False

        current_quantity = self._items.get(item_name, 0)
        if current_quantity >= quantity:
            self._items[item_name] = current_quantity - quantity
            logger.info(f"Inventar {id(self)}: {quantity}x '{item_name}' entfernt. Verbleibend: {self._items[item_name]}")
            if self._items[item_name] == 0:
                del self._items[item_name]
                logger.debug(f"Inventar {id(self)}: Item '{item_name}' komplett entfernt (Anzahl 0).")
            return True
        else:
            logger.warning(f"Inventar {id(self)}: Nicht genug '{item_name}' zum Entfernen vorhanden (benötigt: {quantity}, vorhanden: {current_quantity}).")
            return False

    def has_item(self, item_name, quantity=1):
        has = self._items.get(item_name, 0) >= quantity
        logger.debug(f"Inventar {id(self)}: Prüfung 'has_item({item_name}, {quantity})' -> {has}")
        return has

    def get_items(self):
        logger.debug(f"Inventar {id(self)}: Abfrage aller Items.")
        return self._items.copy()

    def display(self, screen, position):
        # Hier kein Logging hinzugefügt, da es eine reine Zeichenfunktion ist
        # und potenziell sehr oft aufgerufen wird.
        font = pygame.font.Font(None, 24)
        y_offset = 0
        for item, count in self._items.items():
            text = f"{item}: {count}"
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (position[0], position[1] + y_offset))
            y_offset += 25