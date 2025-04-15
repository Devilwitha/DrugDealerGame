# data/etc/inventory.py
# Stand: 2025-04-15 (Refaktorierte Version)
# Formatiert für maximale Lesbarkeit

import pygame
import json
import os
import logging
import locale # Für Währungsformatierung

# Logging für dieses Modul
logger = logging.getLogger(__name__)

# ========= BASIS-KONSTANTEN (Schon vorhanden, zur Klarheit hier gezeigt) =========
# Basisgröße eines Inventar-Slots in Pixeln (vor Skalierung)
BOX_SIZE = 32
# Abstand zwischen Inventar-Slots in Pixeln (vor Skalierung)
PADDING = 5
# Maximale Anzahl von Slots, die gleichzeitig angezeigt werden
MAX_SLOTS = 10 # Beispielwert, passe ihn an dein Spiel an!

# ========= UI-SKALIERUNG & LAYOUT (Neu/verschoben aus game.py) =========
# Faktor zur Vergrößerung des Inventars für bessere Sichtbarkeit
INVENTORY_SCALE_FACTOR = 2.0
# Zusätzlicher Abstand des Inventars vom unteren Bildschirmrand
INVENTORY_BOTTOM_PADDING = 20
# Dateiname für das Geld-Icon
MONEY_ICON_FILENAME = "money_icon.png"

# --- Berechnete Skalierungs-Getter ---
# Diese Funktionen erlauben es, die skalierten Werte abzurufen,
# ohne globale Variablen oder direkte Berechnungen in game.py zu benötigen.

_scaled_box_size = None
_scaled_padding = None
_scaled_icon_size = None

def calculate_scaled_dimensions():
    """Berechnet die skalierten Dimensionen einmalig."""
    global _scaled_box_size, _scaled_padding, _scaled_icon_size
    if _scaled_box_size is None: # Nur beim ersten Mal berechnen
        _scaled_box_size = int(BOX_SIZE * INVENTORY_SCALE_FACTOR)
        _scaled_padding = int(PADDING * INVENTORY_SCALE_FACTOR)
        scaled_icon_w = max(1, _scaled_box_size - _scaled_padding * 2)
        scaled_icon_h = max(1, _scaled_box_size - _scaled_padding * 2)
        _scaled_icon_size = (scaled_icon_w, scaled_icon_h)
        logger.debug(f"Inventar-Dimensionen berechnet: Scaled Box={_scaled_box_size}, "
                     f"Scaled Padding={_scaled_padding}, Scaled Icon={_scaled_icon_size}")

def get_scaled_box_size():
    """Gibt die berechnete skalierte Slot-Größe zurück."""
    if _scaled_box_size is None: calculate_scaled_dimensions()
    return _scaled_box_size

def get_scaled_padding():
    """Gibt den berechneten skalierten Abstand zurück."""
    if _scaled_padding is None: calculate_scaled_dimensions()
    return _scaled_padding

def get_scaled_icon_size():
    """Gibt die berechnete skalierte Icon-Größe (width, height) zurück."""
    if _scaled_icon_size is None: calculate_scaled_dimensions()
    return _scaled_icon_size

def get_inventory_display_width():
    """Berechnet die Gesamtbreite des angezeigten Inventarbereichs."""
    s_box = get_scaled_box_size()
    s_pad = get_scaled_padding()
    return MAX_SLOTS * s_box + (MAX_SLOTS - 1) * s_pad

def get_required_bottom_padding():
    """Gibt den gesamten benötigten Platz am unteren Rand zurück."""
    return get_scaled_box_size() + INVENTORY_BOTTOM_PADDING


# ========= INVENTORY KLASSE =========
class Inventory:
    """Verwaltet das Inventar des Spielers (Items und deren Mengen)."""

    def __init__(self, filepath="inventar.json", image_folder="data/bilder", image_loader_func=None):
        """
        Initialisiert das Inventar.

        Args:
            filepath (str): Pfad zur Speicherdatei des Inventars.
            image_folder (str): Pfad zum Ordner mit den Bildern (für Geld-Icon).
            image_loader_func (callable | None): Funktion zum Laden von Bildern
                                                  (erwartet filename, alpha, scale_to).
                                                  Wenn None, wird kein Icon geladen.
        """
        self.filepath = filepath
        self.items = {}  # Dictionary: {item_name: quantity}
        self._money_icon_surface = None # Geladenes Bild für Geld-Slot

        self.load_inventory() # Versucht, gespeichertes Inventar zu laden

        # Lade das Geld-Icon, wenn eine Ladefunktion bereitgestellt wird
        if image_loader_func and MONEY_ICON_FILENAME:
             scaled_size = get_scaled_box_size()
             full_path = os.path.join(image_folder, MONEY_ICON_FILENAME)
             logger.debug(f"Versuche Geld-Icon zu laden: '{full_path}' mit Skalierung auf {scaled_size}x{scaled_size}")
             # Stelle sicher, dass die Ladefunktion existiert und rufbar ist
             if callable(image_loader_func):
                 try:
                    self._money_icon_surface = image_loader_func(
                         MONEY_ICON_FILENAME,
                         alpha=True,
                         scale_to=(scaled_size, scaled_size)
                    )
                    if self._money_icon_surface:
                        logger.info(f"Geld-Icon '{MONEY_ICON_FILENAME}' erfolgreich geladen und skaliert.")
                    else:
                        logger.warning(f"Geld-Icon '{MONEY_ICON_FILENAME}' konnte nicht geladen werden (Funktion gab None zurück).")
                 except Exception as e:
                     logger.error(f"Fehler beim Aufrufen der image_loader_func für Geld-Icon: {e}", exc_info=True)
             else:
                 logger.error("Übergebene image_loader_func ist nicht aufrufbar.")
        elif not image_loader_func:
             logger.warning("Keine image_loader_func übergeben, Geld-Icon wird nicht geladen.")


    def add_item(self, item_name, quantity=1):
        """Fügt ein Item zum Inventar hinzu oder erhöht die Menge."""
        if not isinstance(item_name, str) or not item_name:
            logger.warning(f"Ungültiger Item-Name beim Hinzufügen: {item_name}")
            return False
        if not isinstance(quantity, int) or quantity <= 0:
             logger.warning(f"Ungültige Menge '{quantity}' für Item '{item_name}' beim Hinzufügen.")
             return False

        # Prüfen, ob das Inventar voll ist (optional, falls MAX_SLOTS eine harte Grenze sein soll)
        # if item_name not in self.items and len(self.items) >= MAX_SLOTS:
        #     logger.warning(f"Kann '{item_name}' nicht hinzufügen: Inventar ist voll ({len(self.items)}/{MAX_SLOTS} Slots belegt).")
        #     return False

        self.items[item_name] = self.items.get(item_name, 0) + quantity
        logger.debug(f"Item hinzugefügt/aktualisiert: {item_name}, Menge: {self.items[item_name]}")
        # self.save_inventory() # Optional: Direkt speichern? Oder nur bei Bedarf?
        return True

    def remove_item(self, item_name, quantity=1):
        """Entfernt ein Item aus dem Inventar oder verringert die Menge."""
        if not isinstance(item_name, str) or not item_name:
            logger.warning(f"Ungültiger Item-Name beim Entfernen: {item_name}")
            return False
        if not isinstance(quantity, int) or quantity <= 0:
             logger.warning(f"Ungültige Menge '{quantity}' für Item '{item_name}' beim Entfernen.")
             return False

        if item_name not in self.items:
            logger.warning(f"Versuch, nicht vorhandenes Item '{item_name}' zu entfernen.")
            return False

        if self.items[item_name] >= quantity:
            self.items[item_name] -= quantity
            logger.debug(f"Item entfernt/reduziert: {item_name}, verbleibend: {self.items[item_name]}")
            if self.items[item_name] == 0:
                del self.items[item_name]
                logger.debug(f"Item '{item_name}' komplett entfernt (Menge 0).")
            # self.save_inventory() # Optional: Direkt speichern?
            return True
        else:
            logger.warning(f"Nicht genug von Item '{item_name}' vorhanden zum Entfernen (hat {self.items[item_name]}, braucht {quantity}).")
            return False

    def has_item(self, item_name, quantity=1):
        """Prüft, ob eine bestimmte Menge eines Items im Inventar vorhanden ist."""
        if not isinstance(item_name, str) or not item_name: return False
        if not isinstance(quantity, int) or quantity < 1: return False # Menge 0 prüfen macht keinen Sinn
        return self.items.get(item_name, 0) >= quantity

    def get_item_count(self, item_name):
        """Gibt die Menge eines bestimmten Items im Inventar zurück (0 wenn nicht vorhanden)."""
        if not isinstance(item_name, str): return 0
        return self.items.get(item_name, 0)

    def get_item_list_for_display(self):
        """Gibt eine Liste von (item_name, quantity)-Tupeln zurück, sortiert für die Anzeige."""
        # Einfache Sortierung nach Namen, kann angepasst werden
        return sorted(self.items.items())

    def load_inventory(self):
        """Lädt das Inventar aus der JSON-Datei."""
        if not os.path.exists(self.filepath):
            logger.info(f"Inventar-Speicherdatei '{os.path.basename(self.filepath)}' nicht gefunden. Starte mit leerem Inventar.")
            self.items = {}
            return False

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                loaded_items = json.load(f)
                if isinstance(loaded_items, dict):
                    # Validierung: Stelle sicher, dass Mengen Zahlen sind
                    self.items = {k: int(v) for k, v in loaded_items.items() if isinstance(k, str) and isinstance(v, (int, float)) and int(v) > 0}
                    invalid_items = {k:v for k,v in loaded_items.items() if k not in self.items}
                    if invalid_items:
                         logger.warning(f"Einige ungültige Einträge in '{os.path.basename(self.filepath)}' ignoriert: {invalid_items}")
                    logger.info(f"Inventar erfolgreich aus '{os.path.basename(self.filepath)}' geladen ({len(self.items)} Item-Typen).")
                    return True
                else:
                    logger.warning(f"Ungültiges Format in Inventar-Speicherdatei '{os.path.basename(self.filepath)}' (erwartet Dictionary, bekam {type(loaded_items)}). Starte leer.")
                    self.items = {}
                    return False
        except json.JSONDecodeError:
            logger.error(f"Fehler beim Parsen der Inventar-Speicherdatei '{os.path.basename(self.filepath)}'. Datei könnte korrupt sein. Starte leer.", exc_info=True)
            self.items = {}
            return False
        except Exception as e:
            logger.error(f"Unbekannter Fehler beim Laden des Inventars aus '{os.path.basename(self.filepath)}': {e}", exc_info=True)
            self.items = {}
            return False

    def save_inventory(self):
        """Speichert das aktuelle Inventar in die JSON-Datei."""
        logger.debug(f"Speichere Inventar nach: {self.filepath}")
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            save_dir = os.path.dirname(self.filepath)
            if save_dir: # Nur wenn ein Pfad angegeben ist (nicht nur Dateiname)
                 os.makedirs(save_dir, exist_ok=True)

            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, indent=4, ensure_ascii=False)
            logger.info(f"Inventar erfolgreich in '{os.path.basename(self.filepath)}' gespeichert ({len(self.items)} Item-Typen).")
            return True
        except IOError as e:
            logger.error(f"IO-Fehler beim Speichern des Inventars nach '{os.path.basename(self.filepath)}': {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unbekannter Fehler beim Speichern des Inventars: {e}", exc_info=True)
            return False

    def display(self, surface, position, item_icons, font, player_money, locale_set):
        """
        Zeichnet das Inventar auf die angegebene Oberfläche.

        Args:
            surface (pygame.Surface): Die Oberfläche, auf die gezeichnet wird.
            position (tuple): Die (x, y)-Koordinaten der oberen linken Ecke des Inventars.
            item_icons (dict): Ein Dictionary mit {item_name: pygame.Surface} für die Icons.
            font (pygame.font.Font): Der Font für die Mengenanzeige.
            player_money (float): Das aktuelle Geld des Spielers.
            locale_set (bool): True, wenn das deutsche Locale für Währung gesetzt ist.
        """
        try:
            inventory_x, inventory_y = position
            s_box_size = get_scaled_box_size()
            s_padding = get_scaled_padding()
            s_icon_w, s_icon_h = get_scaled_icon_size()
            inv_items = self.get_item_list_for_display()

            # --- Geld-Slot zeichnen (immer als erster Slot) ---
            money_slot_x = inventory_x
            money_slot_rect = pygame.Rect(money_slot_x, inventory_y, s_box_size, s_box_size)

            # Hintergrundbild für Geld, falls geladen
            if self._money_icon_surface:
                surface.blit(self._money_icon_surface, money_slot_rect.topleft)
            else: # Fallback: Farbiger Kasten
                pygame.draw.rect(surface, (50, 50, 80), money_slot_rect) # Dunkelblau-Grau

            pygame.draw.rect(surface, (255, 255, 0), money_slot_rect, 2) # Goldener Rand

            # Geldmenge anzeigen
            if font:
                try:
                    money_text = locale.currency(player_money, grouping=True, symbol=False) + " €" if locale_set else f"{player_money:.0f}$"
                    # Alternative: Kürzen bei großen Zahlen
                    if player_money >= 1000000: money_text = f"{player_money/1000000:.1f}M"
                    elif player_money >= 1000: money_text = f"{player_money/1000:.1f}k"

                except Exception:
                    money_text = f"{player_money:.0f}" # Fallback ohne Formatierung

                money_surf = font.render(money_text, True, (255, 255, 0)) # Gelb
                # Positionieren: Rechtsbündig unten im Slot
                money_rect = money_surf.get_rect(bottom=money_slot_rect.bottom - s_padding // 2,
                                                  right=money_slot_rect.right - s_padding // 2)
                surface.blit(money_surf, money_rect)

            # --- Item-Slots zeichnen (beginnend nach dem Geld-Slot) ---
            start_slot_index = 1 # Slot 0 ist Geld
            for i in range(MAX_SLOTS - start_slot_index): # MAX_SLOTS beinhaltet den Geldslot
                slot_index_actual = start_slot_index + i # Index für die Positionierung
                slot_x = inventory_x + slot_index_actual * (s_box_size + s_padding)
                slot_rect = pygame.Rect(slot_x, inventory_y, s_box_size, s_box_size)

                # Hintergrund für den Slot
                pygame.draw.rect(surface, (80, 80, 80), slot_rect) # Grau
                pygame.draw.rect(surface, (200, 200, 200), slot_rect, 1) # Heller Rand

                # Item in diesem Slot anzeigen (Index i für die Item-Liste)
                if i < len(inv_items):
                    item_name, quantity = inv_items[i]
                    icon = item_icons.get(item_name)

                    if icon:
                        # Icon zentriert im Slot zeichnen
                        icon_rect = icon.get_rect(center=slot_rect.center)
                        # Ggf. sicherstellen, dass Icon nicht über Slot hinausragt (sollte durch Skalierung passen)
                        icon_rect.width = min(icon_rect.width, s_icon_w)
                        icon_rect.height = min(icon_rect.height, s_icon_h)
                        icon_rect.center = slot_rect.center # Neu zentrieren nach Größenanpassung

                        surface.blit(icon, icon_rect)
                    else:
                         # Fallback: Item-Namen schreiben, wenn kein Icon da ist
                         if font:
                              name_surf = font.render(item_name[:3], True, (200, 200, 200)) # Erste 3 Buchstaben
                              name_rect = name_surf.get_rect(center=slot_rect.center)
                              surface.blit(name_surf, name_rect)

                    # Menge anzeigen (rechts unten im Slot), nur wenn > 1
                    if quantity > 1 and font:
                        qty_surf = font.render(str(quantity), True, (255, 255, 255)) # Weiß
                        qty_rect = qty_surf.get_rect(bottom=slot_rect.bottom - s_padding // 2,
                                                      right=slot_rect.right - s_padding // 2)
                        # Kleiner Hintergrund für bessere Lesbarkeit der Menge
                        bg_rect = qty_rect.inflate(4, 2)
                        bg_rect.bottomright = slot_rect.bottomright # Exakt in die Ecke
                        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect, border_radius=3) # Halbtransp. Schwarz

                        surface.blit(qty_surf, qty_rect)

        except Exception as e:
            logger.exception("Fehler beim Zeichnen des Inventars:")
            # Zeichne Fehlermeldung auf Screen?
            if font:
                 err_surf = font.render("INV ERR!", True, (255,0,0))
                 surface.blit(err_surf, position)