# inventory.py
import pygame # Momentan nicht genutzt, aber ggf. für UI später

class Inventory:
    def __init__(self):
        # Ein Dictionary eignet sich gut, um Items und ihre Anzahl zu speichern
        self._items = {} # Format: {"item_name": count}

    def add_item(self, item_name, quantity=1):
        """Fügt ein Item zum Inventar hinzu oder erhöht die Anzahl."""
        if not isinstance(item_name, str) or not item_name:
            print("Error: Ungültiger Item-Name.")
            return
        if not isinstance(quantity, int) or quantity < 1:
            print(f"Error: Ungültige Anzahl ({quantity}) für {item_name}.")
            return

        self._items[item_name] = self._items.get(item_name, 0) + quantity
        print(f"{quantity}x {item_name} zum Inventar hinzugefügt.")

    def remove_item(self, item_name, quantity=1):
        """Entfernt ein Item oder verringert die Anzahl. Gibt True zurück bei Erfolg."""
        if not isinstance(item_name, str) or not item_name:
            print("Error: Ungültiger Item-Name.")
            return False
        if not isinstance(quantity, int) or quantity < 1:
            print(f"Error: Ungültige Anzahl ({quantity}) für {item_name}.")
            return False

        if item_name in self._items:
            if self._items[item_name] >= quantity:
                self._items[item_name] -= quantity
                print(f"{quantity}x {item_name} aus Inventar entfernt.")
                # Wenn Anzahl auf 0 fällt, entferne den Eintrag komplett
                if self._items[item_name] == 0:
                    del self._items[item_name]
                return True
            else:
                print(f"Error: Nicht genug {item_name} im Inventar (benötigt: {quantity}, vorhanden: {self._items[item_name]}).")
                return False
        else:
            print(f"Error: Item {item_name} nicht im Inventar.")
            return False

    def has_item(self, item_name, quantity=1):
        """Prüft, ob eine bestimmte Menge eines Items vorhanden ist."""
        return self._items.get(item_name, 0) >= quantity

    def get_items(self):
        """Gibt eine Kopie des Item-Dictionaries zurück."""
        return self._items.copy()

    def display(self, screen, position):
        """Zeichnet das Inventar auf den Screen (sehr einfache Textversion)."""
        # Diese Funktion müsstest du erweitern, um eine schöne UI zu erstellen.
        font = pygame.font.Font(None, 24)
        y_offset = 0
        for item, count in self._items.items():
            text = f"{item}: {count}"
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (position[0], position[1] + y_offset))
            y_offset += 25 # Nächste Zeile