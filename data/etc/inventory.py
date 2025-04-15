# inventory.py (Komplett, Korrigiert: get_item_count, display mit Skalierung)
# Stand: 2025-04-15

import pygame
import logging
import os # Nur für potentialle Pfadoperationen in Zukunft, aktuell nicht direkt genutzt
from persistence import load_data, save_data # Nutzt die zentralen Speicherfunktionen

logger = logging.getLogger(__name__) # Logger für dieses Modul

# --- Konstanten für die ursprünglichen Größen (werden jetzt weniger direkt genutzt) ---
BOX_SIZE = 48  # Basisgröße, wird in game.py skaliert
PADDING = 5    # Basisabstand, wird in game.py skaliert
BORDER_WIDTH = 2
MAX_SLOTS = 10 # Maximale Anzahl sichtbarer Slots (ohne Geld)

# --- Farben für die Anzeige ---
BORDER_COLOR = (200, 200, 200)
BG_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)
QUANTITY_COLOR = (200, 200, 0)
FALLBACK_FONT_SIZE = 16 # Feste Größe für Fallback-Itemnamen (könnte auch skaliert werden)

class Inventory:
    """
    Verwaltet Items des Spielers, nutzt persistence.py zum Speichern/Laden
    und stellt das Inventar grafisch dar (mit Icons und korrekter Skalierung).
    """
    def __init__(self, filepath, max_slots=MAX_SLOTS):
        """
        Initialisiert das Inventar, lädt Daten und Schriftarten.

        Args:
            filepath (str): Pfad zur Speicherdatei.
            max_slots (int): Maximale Anzahl verschiedener Item-Slots (reine Datenhaltung).
                             Die Anzeige ist auf MAX_SLOTS (Konstante oben) begrenzt.
        """
        self._items = {} # Internes Dictionary für Item-Namen und Mengen
        self.max_slots = max_slots # Limit für *unterschiedliche* Item-Typen
        self.filepath = filepath   # Pfad für Speichern/Laden
        self.font_quantity = None  # Schrift für Mengenanzeige
        self.font_fallback = None  # Schrift für Item-Namen, falls Icon fehlt

        # Lade Schriftarten für die Anzeige (Menge & Fallback)
        try:
            # Feste Größen hier, könnten theoretisch auch skaliert übergeben werden
            self.font_quantity = pygame.font.Font(None, 16)
            self.font_fallback = pygame.font.Font(None, FALLBACK_FONT_SIZE)
            logger.debug(f"Inventar {id(self)}: Schriftarten geladen.")
        except Exception as e:
            logger.error(f"Inventar {id(self)}: Schriftarten nicht geladen: {e}.")
            # Das Spiel kann ohne Schriften für das Inventar weiterlaufen,
            # aber die Anzeige wird unvollständig sein.

        logger.info(f"Inventar {id(self)} wird initialisiert (max. {self.max_slots} Item-Typen). Anzeige limitiert auf {MAX_SLOTS} Slots.")
        # --- Lade Logik ---
        logger.debug(f"Inventar {id(self)}: Rufe persistence.load_data für '{self.filepath}' auf.")
        loaded_data = load_data(self.filepath, default_data={}) # Standard = leeres Dict

        # --- Inventar-spezifische Validierung der geladenen Daten ---
        if isinstance(loaded_data, dict):
            self._items = {} # Beginne mit leerem Dict für validierte Items
            valid_items_count = 0
            invalid_items_count = 0
            loaded_item_types = 0
            for key, value in loaded_data.items():
                if isinstance(key, str) and key and isinstance(value, int) and value > 0:
                    # Prüfe nicht mehr gegen self.max_slots beim Laden,
                    # lade alle gültigen Items. Das Limit gilt eher beim Hinzufügen neuer Typen.
                    self._items[key] = value
                    valid_items_count += 1
                    loaded_item_types += 1
                    # Optional: Warnung, wenn mehr Typen geladen als vorgesehen
                    if loaded_item_types > self.max_slots:
                         logger.warning(f"Inventar {id(self)}: Mehr als {self.max_slots} Item-Typen geladen ('{key}').")
                else:
                    logger.warning(f"Inventar {id(self)}: Ungültiger Eintrag ignoriert: '{key}': {value}")
                    invalid_items_count += 1

            if valid_items_count > 0: logger.info(f"Inventar {id(self)}: {valid_items_count} Items ({loaded_item_types} Typen) übernommen.")
            if invalid_items_count > 0: logger.warning(f"Inventar {id(self)}: {invalid_items_count} ungültige Einträge ignoriert.")
        else:
            logger.warning(f"Inventar {id(self)}: Geladene Daten waren kein Dict ({type(loaded_data)}). Inventar bleibt leer.")
            self._items = {} # Sicherstellen, dass es ein Dict ist

        if not self._items: logger.info(f"Inventar {id(self)} ist nach Laden leer.")
        else: logger.debug(f"Inventar {id(self)} Inhalt nach Laden: {self._items}")


    def save_inventory(self):
        """Speichert das aktuelle Inventar mit der allgemeinen save_data Funktion."""
        logger.debug(f"Inventar {id(self)}: Rufe persistence.save_data auf für Pfad '{self.filepath}'.")
        # Filtere Items mit Menge 0 vor dem Speichern heraus
        items_to_save = {name: qty for name, qty in self._items.items() if qty > 0}
        logger.debug(f"Inventar {id(self)}: Zu speichernde Items: {items_to_save}")
        success = save_data(items_to_save, self.filepath)
        if not success: logger.error(f"Inventar {id(self)}: Speichern fehlgeschlagen.")
        return success

    # --- Methoden zur Item-Verwaltung ---
    def add_item(self, item_name, quantity=1):
        """Fügt Items hinzu. Beachtet das Limit für unterschiedliche Item-Typen."""
        if not isinstance(item_name, str) or not item_name:
            logger.warning(f"Inv {id(self)} Add: Ungültiger Name: '{item_name}'")
            return False
        if not isinstance(quantity, int) or quantity < 1:
            logger.warning(f"Inv {id(self)} Add: Ungültige Anzahl {quantity} für '{item_name}'")
            return False

        # Prüfe, ob ein *neuer* Item-Typ hinzugefügt wird und ob Platz dafür ist
        if item_name not in self._items and len(self._items) >= self.max_slots:
            logger.warning(f"Inv {id(self)} Add: Voll für neue Item-Typen ({len(self._items)}/{self.max_slots}). Kann '{item_name}' nicht hinzufügen.")
            return False

        current_quantity = self._items.get(item_name, 0)
        self._items[item_name] = current_quantity + quantity
        logger.info(f"Inv {id(self)}: {quantity}x '{item_name}' hinzugefügt. Gesamt: {self._items[item_name]}")
        return True

    def remove_item(self, item_name, quantity=1):
        """Entfernt Items. Gibt True zurück, wenn erfolgreich."""
        if not isinstance(item_name, str) or not item_name:
            logger.warning(f"Inv {id(self)} Remove: Ungültiger Name: '{item_name}'")
            return False
        if not isinstance(quantity, int) or quantity < 1:
            logger.warning(f"Inv {id(self)} Remove: Ungültige Anzahl {quantity} für '{item_name}'")
            return False

        current_quantity = self._items.get(item_name, 0)
        if current_quantity >= quantity:
            new_quantity = current_quantity - quantity
            self._items[item_name] = new_quantity
            logger.info(f"Inv {id(self)}: {quantity}x '{item_name}' entfernt. Verbleibend: {new_quantity}")
            # Entferne den Eintrag komplett, wenn Menge 0 ist
            if new_quantity == 0:
                del self._items[item_name]
                logger.debug(f"Inv {id(self)}: Item-Typ '{item_name}' komplett entfernt.")
            return True
        else:
            logger.warning(f"Inv {id(self)} Remove: Nicht genug von '{item_name}' (hat {current_quantity}, braucht {quantity}).")
            return False

    def has_item(self, item_name, quantity=1):
        """Prüft, ob eine bestimmte Menge eines Items vorhanden ist."""
        if not isinstance(item_name, str) or not item_name: return False
        if not isinstance(quantity, int) or quantity < 1: return False
        return self._items.get(item_name, 0) >= quantity

    def get_items(self):
        """Gibt eine Kopie des internen Item-Dictionaries zurück."""
        return self._items.copy()

    def get_item_list_for_display(self):
        """Gibt eine Liste von (name, menge) Tupeln zurück, limitiert auf MAX_SLOTS für die Anzeige."""
        # Gibt nur die ersten MAX_SLOTS Items zurück, sortiert nach Namen (optional)
        # oder in der Reihenfolge des Dictionaries (Python 3.7+)
        sorted_items = sorted(self._items.items()) # Sortiert nach Namen für konsistente Reihenfolge
        return sorted_items[:MAX_SLOTS]

    def get_item_count(self, item_name):
        """Gibt die Anzahl eines bestimmten Items zurück."""
        if not isinstance(item_name, str):
            return 0
        return self._items.get(item_name, 0)

    # --- Display Methode (KORRIGIERT für Skalierung) ---
    def display(self, screen, position, item_icons, scaled_box_size, scaled_padding):
        """
        Zeichnet das Inventar als Kastenreihe, bevorzugt mit Icons, unter
        Verwendung der übergebenen skalierten Größen.

        Args:
            screen (pygame.Surface): Die Oberfläche zum Zeichnen.
            position (tuple): (x, y) der linken oberen Ecke des ersten Slots.
            item_icons (dict): Ein Dictionary, das Item-Namen auf geladene
                                pygame.Surface Objekte (Icons) abbildet.
            scaled_box_size (int): Die BEREITS SKALIERTE Größe eines Slots.
            scaled_padding (int): Der BEREITS SKALIERTE Abstand zwischen Slots.
        """
        # Prüfe ob benötigte Schriften geladen wurden
        fonts_ok = self.font_quantity is not None and self.font_fallback is not None
        if not fonts_ok:
            # Nur einmal warnen, wenn eine der Schriften fehlt
            if not hasattr(self, '_warned_font_missing'):
                 logger.warning(f"Inventar {id(self)}: Kann nicht korrekt zeichnen, Schriftart(en) fehlen.")
                 self._warned_font_missing = True # Verhindert wiederholte Warnung
            # Ohne font_quantity können wir die Menge nicht zeichnen
            if not self.font_quantity: return

        start_x, start_y = position
        items_to_display = self.get_item_list_for_display() # Holt max MAX_SLOTS Items

        # Zeichne für jeden ANZEIGE-Slot (MAX_SLOTS) einen Kasten.
        for i in range(MAX_SLOTS):
            # --- VERWENDE SKALIERTE WERTE ---
            box_x = start_x + i * (scaled_box_size + scaled_padding)
            box_rect = pygame.Rect(box_x, start_y, scaled_box_size, scaled_box_size)
            # ---------------------------------

            # Hintergrund und Rand zeichnen
            pygame.draw.rect(screen, BG_COLOR, box_rect)
            pygame.draw.rect(screen, BORDER_COLOR, box_rect, BORDER_WIDTH)

            # Wenn für diesen Slot ein Item existiert (basierend auf der limitierten Liste)
            if i < len(items_to_display):
                item_name, quantity = items_to_display[i]

                # --- Icon zeichnen ---
                icon_surface = item_icons.get(item_name) # Icons sind bereits skaliert geladen

                if icon_surface:
                    # Zeichne das (bereits skalierte) Icon zentriert in die (skalierte) Box
                    try:
                        icon_rect = icon_surface.get_rect(center=box_rect.center)
                        screen.blit(icon_surface, icon_rect)
                    except Exception as e:
                        logger.error(f"Inv {id(self)} Display: Fehler beim Zeichnen des Icons für '{item_name}': {e}")
                        icon_surface = None # Fallback

                if not icon_surface:
                    # Fallback: Zeichne Textnamen (zentriert in der skalierten Box)
                    if self.font_fallback:
                        try:
                            max_name_len = 7 # Ggf. anpassen je nach Fontgröße/Boxgröße
                            display_name = item_name if len(item_name) <= max_name_len else item_name[:max_name_len-1] + "."
                            name_surf = self.font_fallback.render(display_name, True, TEXT_COLOR)
                            name_rect = name_surf.get_rect(center=box_rect.center)
                            screen.blit(name_surf, name_rect)
                        except Exception as e:
                            logger.error(f"Inv {id(self)} Display: Fehler Render Fallback-Name '{item_name}': {e}")
                    # else: # Keine Aktion nötig, wenn Fallback-Font fehlt

                # Zeichne Item-Anzahl (wenn > 0)
                if quantity > 0:
                    if self.font_quantity: # Nur zeichnen, wenn Font vorhanden ist
                        try:
                            quantity_str = str(quantity)
                            quantity_surf = self.font_quantity.render(quantity_str, True, QUANTITY_COLOR)
                            # --- VERWENDE SKALIERTEN ABSTAND ---
                            # Positioniere rechts unten innerhalb der Box mit Padding
                            quantity_rect = quantity_surf.get_rect(
                                bottomright=box_rect.bottomright - pygame.Vector2(scaled_padding // 2, scaled_padding // 2)
                            )
                            # -----------------------------------
                            screen.blit(quantity_surf, quantity_rect)
                        except Exception as e:
                            logger.error(f"Inv {id(self)} Display: Fehler Render Anzahl '{item_name}': {e}")
                    # else: # Keine Aktion nötig, wenn Mengen-Font fehlt