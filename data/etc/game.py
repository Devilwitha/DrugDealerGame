# game.py (Komplett, Korrigiert: inventory.display Aufruf & Geld-Slot Zeichnen)
# Formatiert für maximale Lesbarkeit
# Stand: 2025-04-15

# ========= SYSTEM PATH ANPASSUNG (WICHTIG!) =========
import sys
import os
# Füge das Projekt-Stammverzeichnis zum sys.path hinzu
# Annahme: game.py liegt in data/etc/, Stammverzeichnis ist 2 Ebenen höher
try:
    # Direkter Pfad, wenn __file__ bekannt ist
    script_dir_game = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback, falls __file__ nicht verfügbar (z.B. interaktive Konsole)
    script_dir_game = os.path.abspath(".")
project_root_dir_game = os.path.abspath(os.path.join(script_dir_game, "..", ".."))
if project_root_dir_game not in sys.path:
    sys.path.insert(0, project_root_dir_game)
    # print(f"DEBUG: '{project_root_dir_game}' zum sys.path hinzugefügt.") # Weniger verbose für Release

# =====================================================

# ========= MODULE IMPORTIEREN =========
# Standardbibliothek
import logging
import math
import time
import traceback
import locale
import subprocess # Für Minispiel-Start

# Pygame
import pygame

# ========= LOKALISIERUNG (Währung) =========
try:
    # Versuche deutsches Locale für Währung etc.
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    LOCALE_SET = True
except locale.Error:
    try:
        # Fallback für Windows
        locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
        LOCALE_SET = True
    except locale.Error:
        print("WARNUNG: Locale 'de_DE' oder 'German_Germany.1252' nicht verfügbar für Währung.")
        LOCALE_SET = False

# ========= LOGGING KONFIGURATION =========
log_format = '%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s' # Zeilennummer hinzugefügt
log_level = logging.DEBUG # Sehr ausführlich für Entwicklung/Fehlersuche
date_fmt = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=log_level, format=log_format, datefmt=date_fmt, force=True)
logger = logging.getLogger(__name__) # Logger für dieses Modul (game)

# --- Pfad-Setup (Nutzt project_root_dir_game von oben) ---
data_dir_root = os.path.join(project_root_dir_game, "data")
log_dir = os.path.join(data_dir_root, "logs")
IMAGE_FOLDER = os.path.join(data_dir_root, "bilder")
SOUND_FOLDER = os.path.join(data_dir_root, "sounds")
SAVE_DATA_DIR_ABS = os.path.join(data_dir_root, "savedata")
SETTINGS_DIR = os.path.join(data_dir_root, "settings")
MINIGAME_FOLDER_GROWING = os.path.join(data_dir_root, "miniGame", "Growing")
MINIGAME_FOLDER_ZIPWEED = os.path.join(data_dir_root, "miniGame", "zipWeed") # Pfad zu ZipWeed

# --- Absolute Dateipfade ---
SETTINGS_FILE_PATH = os.path.join(SETTINGS_DIR, "settings.json")
MAIN_SCRIPT_PATH = os.path.join(project_root_dir_game, "main.py") # Annahme: main.py im Root
MINIGAME_GROW1_PATH = os.path.join(MINIGAME_FOLDER_GROWING, "plant_grow1.py")
MINIGAME_GROW2_PATH = os.path.join(MINIGAME_FOLDER_GROWING, "grow_plant2.py")
MINIGAME_EARN_WEED_PATH = os.path.join(MINIGAME_FOLDER_GROWING, "earn_buds.py")
# Pfad zum ZipWeed Minispiel (Python Datei)
# WICHTIG: Stellen Sie sicher, dass diese Datei existiert und die Funktion 'run_zip_weed_game' enthält
ZIPWEED_SCRIPT_PATH = os.path.join(MINIGAME_FOLDER_ZIPWEED, "zipWeed.py")

INVENTORY_SAVE_FILE = os.path.join(SAVE_DATA_DIR_ABS, "inventar.json")
PLAYER_POS_SAVE_FILE = os.path.join(SAVE_DATA_DIR_ABS, "player_position.json")
PLACED_ITEMS_SAVE_FILE = os.path.join(SAVE_DATA_DIR_ABS, "placed_items.json")
PLACED_ITEMS_FILENAME = "placed_items.json" # Nur Dateiname für Logs etc.

# --- File Logging hinzufügen ---
try:
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"game_{timestamp}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_format, datefmt=date_fmt)
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logger.info(f"File logging initialisiert: {log_file_path}")
except Exception as e:
    logger.error(f"Fehler beim Initialisieren des File Logging: {e}", exc_info=True)

logger.info("Spiel wird initialisiert...")
logger.debug(f"Project Root Verzeichnis: {project_root_dir_game}")
logger.debug(f"Pfad Minispiel 1 (Erde): {MINIGAME_GROW1_PATH}")
logger.debug(f"Pfad Minispiel 2 (Samen/Gießen): {MINIGAME_GROW2_PATH}")
logger.debug(f"Pfad Minispiel 3 (Ernten): {MINIGAME_EARN_WEED_PATH}")
logger.debug(f"Pfad Minispiel 4 (ZipWeed): {ZIPWEED_SCRIPT_PATH}")


# Eigene Module (jetzt mit absolutem Import und Fallback)
# HINWEIS: Passe die Pfade an, falls deine Struktur anders ist!
try:
    # Standard-Importe (Annahme: Module sind relativ zum Project Root oder über PYTHONPATH erreichbar)
    from data.etc import platform_utils # Für Android-spezifische Dinge
    from data.etc.player import Player
    from data.etc.npc import NPC
    from data.etc.camera import Camera
    # Importiere zusätzliche Konstanten aus inventory.py für das Zeichnen des Geld-Slots
    from data.etc.inventory import (Inventory, BOX_SIZE, PADDING, MAX_SLOTS,
                                   BG_COLOR, BORDER_COLOR, BORDER_WIDTH, QUANTITY_COLOR)
    from data.etc.persistence import load_data, save_data
    from data.etc import settings_utils
    from data.etc import items # Erwartet PLACEABLE_ITEMS, load_item_assets, etc.
    from data.etc import dialog # Enthält Dialogstruktur
    from data.etc import shop_items # Enthält Shopangebot

    # Importiere die Minispiel-Funktion absolut aus dem ZipWeed Modul
    # Annahme: data/miniGame/zipWeed/zipWeed.py existiert
    from data.miniGame.zipWeed.zipWeed import run_zip_weed_game

except ImportError as e:
    logger.critical(f"FATAL ERROR: Modul '{e.name}' nicht gefunden. Prüfe Pfade und PYTHONPATH. sys.path: {sys.path}. Traceback:\n{traceback.format_exc()}", exc_info=True)
    sys.exit(f"FEHLER: Modul '{e.name}' fehlt. Spiel kann nicht starten.")
except Exception as e:
    logger.critical(f"FATAL ERROR: Unerwarteter Fehler beim Importieren eigener Module. Traceback:\n{traceback.format_exc()}", exc_info=True)
    sys.exit("FEHLER: Unerwarteter Import-Fehler. Spiel kann nicht starten.")


# ========= EINSTELLUNGEN LADEN =========
try:
    current_settings = settings_utils.load_settings(SETTINGS_FILE_PATH)
    logger.info(f"Einstellungen geladen: {current_settings}")
except Exception:
    logger.exception("FEHLER beim Laden der Einstellungen:")
    # Fallback-Einstellungen, wenn das Laden fehlschlägt
    current_settings = {'music_volume': 0.5, 'sfx_volume': 0.5, 'master_volume': 1.0}
    logger.warning(f"Nutze Fallback-Einstellungen: {current_settings}")

# ========= KONSTANTEN =========
# --- Spielwelt & Physik ---
TILE_SIZE = 32
FPS = 60
INTERACTION_RADIUS = TILE_SIZE * 1.5 # Radius um Spieler für Interaktion
LONG_PRESS_THRESHOLD = 1.0 # Sekunden für langes Drücken (Aufheben)
GROW_TIME_SECONDS = 10 # Standard-Wachstumszeit für Pflanzen

# --- Farben (RGB) ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0)
GREEN = (0, 200, 0); DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0); BLUE = (0, 0, 255); MAGENTA = (255, 0, 255)
GREY = (100, 100, 100); LIGHT_GREY = (180, 180, 180); DARK_BLUE = (0, 0, 100)
YELLOW = (255, 255, 0)

# --- Visuelle Elemente ---
PLACED_ITEM_SIZE = TILE_SIZE # Größe platzierter Items in der Welt

# --- Inventar-Skalierung & Layout ---
# (Nutzt Konstanten aus inventory.py als Basis)
INVENTORY_SCALE_FACTOR = 2.0 # Faktor zur Vergrößerung des Inventars
SCALED_BOX_SIZE = int(BOX_SIZE * INVENTORY_SCALE_FACTOR) # Skalierte Slot-Größe
SCALED_PADDING = int(PADDING * INVENTORY_SCALE_FACTOR)  # Skalierter Abstand
SCALED_ICON_W = max(1, SCALED_BOX_SIZE - SCALED_PADDING * 2) # Icon-Größe passt in skalierten Slot
SCALED_ICON_H = max(1, SCALED_BOX_SIZE - SCALED_PADDING * 2)
SCALED_ICON_SIZE = (SCALED_ICON_W, SCALED_ICON_H)
logger.debug(f"Berechnete Icon-Größe (skaliert): {SCALED_ICON_SIZE}")
INVENTORY_BOTTOM_PADDING = 20 # Abstand des Inventars vom unteren Rand

# --- Button (Interaktion auf Android) ---
BUTTON_DEFAULT_WIDTH_PERCENT = 0.08 # Breite als % der Bildschirmbreite
BUTTON_DEFAULT_HEIGHT_PERCENT = 0.13 # Höhe als % der Bildschirmhöhe
BUTTON_PADDING = 15 # Abstand des Buttons von Rändern/anderen Elementen
BUTTON_X = BUTTON_PADDING # X-Position des Buttons (linker Rand)
BUTTON_COLOR_NORMAL = (80, 80, 80) # Fallback-Farbe für Button
BUTTON_BORDER_COLOR = WHITE # Randfarbe für Fallback-Button

# --- Fonts (Basisgrößen, werden skaliert) ---
FONT_SIZE_REF_H = 600.0 # Referenzhöhe für Font-Skalierung
BASE_UI_FONT_SIZE = 28
BASE_BUTTON_FONT_SIZE = 18
BASE_INV_QTY_FONT_SIZE = 16 # Basis für Inventar-Menge
BASE_DIALOG_FONT_SIZE = 24
BASE_SHOP_FONT_SIZE = 18

# --- Asset-Dateinamen ---
BACKGROUND_FILENAME = "background.png"
BUTTON_FILENAME = "interact_button.png" # Bild für Android-Button
MONEY_ICON_FILENAME = "money_icon.png" # Icon für Geld im Inventar
# Icon-Dateinamen für ZipWeed-Interaktion (MÜSSEN EXISTIEREN!)
GRIPS_ICON_FILENAME = "grips_icon.png"
PACKED_WEED_ICON_FILENAME = "packed_weed_icon.png"
# Sound-Dateiname für fehlende Ressourcen (MUSS EXISTIEREN!)
NO_RESOURCE_SOUND_FILENAME = "error.wav"

# --- Spielzustände ---
GAME_STATE_PLAY = "play"
GAME_STATE_DIALOG = "dialog"
GAME_STATE_SHOP = "shop"
GAME_STATE_SELL = "sell"

# --- Gameplay ---
WEED_SELL_PRICE = 15.0 # Verkaufspreis pro Einheit Weed


# ========= HILFSFUNKTIONEN =========
def load_image_asset(filename, alpha=True, scale_to=None):
    """Lädt ein Bild aus dem IMAGE_FOLDER, konvertiert es und skaliert es optional."""
    if not filename:
        logger.warning("Leerer Dateiname in load_image_asset.")
        return None
    path = os.path.join(IMAGE_FOLDER, filename)
    try:
        image = pygame.image.load(path)
        image = image.convert_alpha() if alpha else image.convert()
    except pygame.error as e:
        logger.error(f"Pygame Fehler Laden Bild '{path}': {e}")
        return None
    except FileNotFoundError:
        logger.warning(f"Bilddatei nicht gefunden: '{path}'")
        return None
    except Exception as e:
        logger.error(f"Allg. Fehler Laden Bild '{path}': {e}", exc_info=True)
        return None

    if scale_to:
        if (not isinstance(scale_to, (tuple, list))
                or len(scale_to) != 2
                or not isinstance(scale_to[0], (int, float)) or scale_to[0] <= 0
                or not isinstance(scale_to[1], (int, float)) or scale_to[1] <= 0):
            logger.error(f"Ungültiges scale_to '{scale_to}' für '{filename}'.")
        else:
            scale_to_int = (int(scale_to[0]), int(scale_to[1]))
            try:
                if image.get_width() > 0 and image.get_height() > 0:
                    image = pygame.transform.smoothscale(image, scale_to_int)
                else:
                    logger.warning(f"Ungültige Bilddimensionen für '{filename}' ({image.get_size()}). Überspringe Skalierung.")
            except ValueError:
                logger.error(f"ValueError beim Skalieren von '{filename}' zu {scale_to_int}.", exc_info=False)
            except Exception:
                logger.error(f"Fehler Skalieren '{filename}' zu {scale_to_int}", exc_info=True)
    return image

def load_sound_asset(filename):
    """Lädt eine Sounddatei aus dem SOUND_FOLDER."""
    if not filename:
        logger.warning("Leerer Dateiname in load_sound_asset.")
        return None
    path = os.path.join(SOUND_FOLDER, filename)
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except pygame.error as e:
        logger.error(f"Pygame Fehler Laden Sound '{path}': {e}")
        return None
    except FileNotFoundError:
        logger.warning(f"Sounddatei nicht gefunden: '{path}'")
        return None
    except Exception as e:
        logger.error(f"Allg. Fehler Laden Sound '{path}': {e}", exc_info=True)
        return None

def save_game_state():
    """Speichert alle relevanten Spieldaten in separaten JSON-Dateien."""
    logger.info("Speichere Spielstand...")
    # Inventar
    try:
        if inventory:
            logger.info("  Speichere Inventar...")
            if not inventory.save_inventory(): # Prüfe Rückgabewert der Methode
                logger.error("  Fehler beim Speichern des Inventars (laut save_inventory).")
        else:
            logger.warning("  Inventar nicht initialisiert, kann nicht gespeichert werden.")
    except Exception:
        logger.exception("  Unerwarteter Fehler beim Speichern des Inventars:")

    # Spielerdaten
    try:
        if player:
            logger.info("  Speichere Spielerposition & Geld...")
            player_data = {'x': player.rect.x, 'y': player.rect.y, 'money': player_money}
            if not save_data(player_data, PLAYER_POS_SAVE_FILE):
                logger.error("  Fehler beim Speichern der Spielerdaten (laut save_data).")
        else:
            logger.warning("  Spieler nicht initialisiert, kann nicht gespeichert werden.")
    except Exception:
        logger.exception("  Unerwarteter Fehler beim Speichern der Spielerdaten:")

    # Platzierte Items
    try:
        if placed_items is not None: # Prüfe, ob die Gruppe existiert
            logger.info("  Speichere platzierte Items...")
            items_to_save = []
            for item in placed_items:
                # Stelle sicher, dass das Item die nötigen Attribute hat
                if hasattr(item, 'rect') and item.rect and hasattr(item, 'item_type'):
                    items_to_save.append({
                        'type': item.item_type,
                        'x': item.rect.centerx, # Center speichern ist oft robuster bei Größenänderungen
                        'y': item.rect.centery,
                        'state': getattr(item, 'state', 'default'), # Sicherer Zugriff auf state
                        'timer_end': getattr(item, 'timer_end_timestamp', None), # Sicherer Zugriff
                        'grow_time': getattr(item, 'grow_time_seconds', 0) # Sicherer Zugriff
                    })
                else:
                    logger.warning(f"Überspringe Speichern von Item {item} (Typ: {getattr(item, 'item_type', '?')}), da es kein gültiges Rect oder Typ hat.")

            if not save_data(items_to_save, PLACED_ITEMS_SAVE_FILE):
                logger.error("  Fehler beim Speichern der platzierten Items (laut save_data).")
            else:
                logger.info(f"  {len(items_to_save)} platzierte Items gespeichert.")
        else:
            logger.warning("  Placed_items Gruppe nicht initialisiert, kann nicht gespeichert werden.")
    except Exception:
        logger.exception("  Unerwarteter Fehler beim Speichern der platzierten Items:")

def wrap_text(surface, text, font, color, rect, aa=True):
    """Zeichnet Text mit Zeilenumbruch innerhalb eines Rechtecks."""
    if not font:
        logger.error("wrap_text: Font ist None!")
        return
    lines = []
    words = text.split(' ')
    current_line_words = []

    while words:
        word = words.pop(0)
        current_line_words.append(word)
        try:
            # Prüfen, ob die aktuelle Zeile zu lang wird
            line_width, _ = font.size(' '.join(current_line_words))
            if line_width > rect.width:
                # Wenn mehr als ein Wort in der Zeile ist, letztes Wort zurückschieben
                if len(current_line_words) > 1:
                    last_word = current_line_words.pop()
                    words.insert(0, last_word) # Zurück in die Wortliste
                # Füge die Zeile (ohne das letzte Wort) hinzu
                lines.append(' '.join(current_line_words))
                # Beginne neue Zeile mit dem Wort, das nicht passte
                # (oder leer, falls das einzelne Wort schon zu lang war)
                current_line_words = [last_word] if len(current_line_words) == 1 else []
                if len(current_line_words) == 1: # Wenn das einzelne Wort schon zu lang war
                   word_width, _ = font.size(current_line_words[0])
                   if word_width > rect.width:
                       logger.warning(f"wrap_text: Wort '{current_line_words[0]}' ist breiter als das Rechteck ({rect.width}).")
                       lines.append(current_line_words[0]) # Trotzdem hinzufügen (wird abgeschnitten)
                       current_line_words = []

        except pygame.error:
            logger.exception("Fehler bei font.size() in wrap_text")
            return # Abbruch bei Font-Fehler

    # Füge die letzte Zeile hinzu, falls noch Wörter übrig sind
    if current_line_words:
        lines.append(' '.join(current_line_words))

    # Zeichne die Zeilen
    y = rect.top
    line_spacing = font.get_linesize() * 0.9 # Etwas engerer Zeilenabstand
    line_height = font.get_height()

    for line in lines:
        # Prüfen, ob die nächste Zeile noch ins Rect passt
        if y + line_height > rect.bottom:
            logger.warning("Textumbruch: Nicht alle Zeilen passen ins Rechteck.")
            break
        try:
            img = font.render(line, aa, color)
            surface.blit(img, (rect.left, y))
            y += int(line_spacing) # Zum nächsten Zeilenanfang springen
        except pygame.error:
            logger.exception(f"Fehler bei font.render() für Zeile: '{line}'")
            break # Abbruch bei Render-Fehler


# ========= GLOBALE VARIABLEN (Initialisierung) =========
# Spielobjekte & Zustände
screen: pygame.Surface | None = None
clock: pygame.time.Clock | None = None
player: Player | None = None
camera: Camera | None = None
inventory: Inventory | None = None
all_sprites: pygame.sprite.Group | None = None
npcs: pygame.sprite.Group | None = None
placed_items: pygame.sprite.Group | None = None # Wichtig: Initialisieren!

# UI Elemente & Fonts
ui_font: pygame.font.Font | None = None
button_font: pygame.font.Font | None = None
inventory_font: pygame.font.Font | None = None # Wird für Geld-Anzeige benötigt
dialog_font: pygame.font.Font | None = None
shop_font: pygame.font.Font | None = None
background_image: pygame.Surface | None = None
button_image_normal: pygame.Surface | None = None # Geladenes Bild für Android Button
money_slot_background_img: pygame.Surface | None = None # Icon für Geld-Slot
item_icons: dict = {} # Icons für Inventar/Shop {item_name: Surface}
placed_item_images: dict = {} # Bilder für platzierte Items {item_type: {state: Surface}}
fallback_placed_image: pygame.Surface | None = None # Fallback-Bild für platzierte Items

# Sounds
no_resource_sound: pygame.mixer.Sound | None = None # Sound für fehlende Items

# Spielzustand & Interaktion
current_game_state: str = GAME_STATE_PLAY
player_money: float = 0.0
active_npc: NPC | None = None # Der NPC, mit dem gerade interagiert wird
current_dialog_node_id: str | None = None # Aktueller Knoten im Dialog
dialog_response_rects: list = [] # Rects für Dialog-Antworten (für Klicks)
shop_item_rects: list = [] # Rects für Shop-Items (für Klicks)
shop_exit_button_rect: pygame.Rect | None = None # Rect für Shop-Verlassen Button
sell_item_rect: pygame.Rect | None = None # Bereich für Verkaufsitem
sell_button_rect: pygame.Rect | None = None # Rect für Verkaufen-Button
sell_exit_button_rect: pygame.Rect | None = None # Rect für Verkaufen-Verlassen Button
is_dragging: bool = False # Ob gerade ein Item aus dem Inventar gezogen wird
dragged_item_type: str | None = None # Typ des gezogenen Items
dragged_item_image: pygame.Surface | None = None # Vorschaubild des gezogenen Items
interaction_active: bool = False # Ob gerade Interaktionstaste/Button gedrückt wird
interaction_start_time: float = 0.0 # Zeitstempel, wann Interaktion begann (für Long Press)
potential_interaction_target: pygame.sprite.Sprite | None = None # Nächstes mögliches Interaktionsobjekt
target_type: str | None = None # Typ des Ziels ('item' oder 'npc')

# UI Layout (wird nach Screen-Erstellung berechnet)
CENTERED_INVENTORY_X_POS: int = 0
CENTERED_INVENTORY_Y_POS: int = 0
BUTTON_RECT: pygame.Rect | None = None # Rect für Android Interaktionsbutton


# ========= HAUPT-INITIALISIERUNGSBLOCK =========
try:
    pygame.init()
    try:
        pygame.mixer.init()
        logger.info("Pygame Mixer initialisiert.")
    except pygame.error:
        logger.error("Pygame Mixer Initialisierung fehlgeschlagen.", exc_info=True)

    # Bildschirm initialisieren (versucht Vollbild, Fallback auf 800x600)
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # Fallback-Größe
    try:
        info = pygame.display.Info()
        SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
        logger.info(f"Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        # SCALED erlaubt internes Rendering in logischer Größe, RESIZABLE ist gut für Desktop
        screen_flags = pygame.SCALED | pygame.RESIZABLE
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), screen_flags)
    except Exception:
        logger.warning("Vollbild-Initialisierung fehlgeschlagen. Nutze Fallback 800x600.", exc_info=False)
        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
        try:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        except Exception as e_fallback:
            logger.critical("Fallback-Bildschirm konnte nicht erstellt werden!", exc_info=True)
            pygame.quit()
            sys.exit("FEHLER: Bildschirm konnte nicht initialisiert werden.")

    if screen is None: # Zusätzliche Sicherheitsprüfung
         logger.critical("Bildschirm konnte nicht initialisiert werden (screen is None).")
         pygame.quit()
         sys.exit("FEHLER: Bildschirm ist None.")

    pygame.display.set_caption("Drug Dealer Game") # Fenstertitel
    clock = pygame.time.Clock()
    logger.info("Screen & Clock erfolgreich erstellt.")

    # Weltgröße definieren (Beispiel: 3x Bildschirmbreite, 2x Bildschirmhöhe)
    WORLD_WIDTH = SCREEN_WIDTH * 3
    WORLD_HEIGHT = SCREEN_HEIGHT * 2
    logger.info(f"Weltgröße definiert: {WORLD_WIDTH}x{WORLD_HEIGHT}")

    # Fonts laden und skalieren
    ui_fs = max(12, int(SCREEN_HEIGHT * (BASE_UI_FONT_SIZE / FONT_SIZE_REF_H)))
    btn_fs = max(10, int(SCREEN_HEIGHT * (BASE_BUTTON_FONT_SIZE / FONT_SIZE_REF_H)))
    inv_fs = max(8, int(SCREEN_HEIGHT * (BASE_INV_QTY_FONT_SIZE / FONT_SIZE_REF_H)))
    dlg_fs = max(14, int(SCREEN_HEIGHT * (BASE_DIALOG_FONT_SIZE / FONT_SIZE_REF_H)))
    shp_fs = max(10, int(SCREEN_HEIGHT * (BASE_SHOP_FONT_SIZE / FONT_SIZE_REF_H)))
    try:
        ui_font = pygame.font.Font(None, ui_fs) # Standard Pygame Font
        button_font = pygame.font.Font(None, btn_fs)
        inventory_font = pygame.font.Font(None, inv_fs) # Dieser Font wird für Geld-Anzeige gebraucht
        dialog_font = pygame.font.Font(None, dlg_fs)
        shop_font = pygame.font.Font(None, shp_fs)
        logger.info(f"Fonts erstellt (Größen: UI={ui_fs}, Btn={btn_fs}, Inv={inv_fs}, Dlg={dlg_fs}, Shop={shp_fs}).")
    except Exception:
        logger.exception("Fehler beim Laden der Fonts:")
        pygame.quit()
        sys.exit("FEHLER: Fonts konnten nicht geladen werden.")

    # UI Layout Berechnungen (nutzt SCALED Werte vom Inventar)
    BTN_DEF_W = int(SCREEN_WIDTH * BUTTON_DEFAULT_WIDTH_PERCENT)
    BTN_DEF_H = int(SCREEN_HEIGHT * BUTTON_DEFAULT_HEIGHT_PERCENT)
    BUTTON_RECT = pygame.Rect(BUTTON_X, 0, BTN_DEF_W, BTN_DEF_H) # Y wird später gesetzt
    # Inventarbreite basierend auf Anzahl Slots, skalierter Größe und Abstand
    inv_display_width = MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING
    CENTERED_INVENTORY_X_POS = (SCREEN_WIDTH - inv_display_width) // 2
    # Korrektur Geld-Slot Position: Zentriere Item-Slots und platziere Geld-Slot rechts daneben
    # Neue Berechnung: Breite aller Item-Slots + Geld-Slot + Abstände
    total_inv_width = (MAX_SLOTS + 1) * SCALED_BOX_SIZE + MAX_SLOTS * SCALED_PADDING
    CENTERED_INVENTORY_X_POS = (SCREEN_WIDTH - total_inv_width) // 2 # Neu berechnet für alles
    CENTERED_INVENTORY_Y_POS = SCREEN_HEIGHT - SCALED_BOX_SIZE - INVENTORY_BOTTOM_PADDING
    logger.info(f"Inventar Position berechnet (inkl. Geld): X={CENTERED_INVENTORY_X_POS}, Y={CENTERED_INVENTORY_Y_POS}")

    # Assets laden
    logger.info("Lade Assets...")
    # Item-Assets (Icons für Inventar/Shop, Bilder für platzierte Objekte)
    item_icons, placed_item_images, fallback_placed_image = items.load_item_assets(
        IMAGE_FOLDER, PLACED_ITEM_SIZE, SCALED_ICON_SIZE, load_image_asset
    )
    # Stelle sicher, dass Icons für neue Items (Grips, VerpacktesWeed) geladen werden, falls nicht in items.py definiert
    if "Grips" not in item_icons:
        item_icons['Grips'] = load_image_asset(GRIPS_ICON_FILENAME, alpha=True, scale_to=SCALED_ICON_SIZE)
    if "VerpacktesWeed" not in item_icons:
        item_icons['VerpacktesWeed'] = load_image_asset(PACKED_WEED_ICON_FILENAME, alpha=True, scale_to=SCALED_ICON_SIZE)

    # Logge fehlende Icons nach dem Laden
    for name, icon in item_icons.items():
        if icon is None:
            logger.warning(f"Icon für '{name}' fehlt nach Ladevorgang oder konnte nicht geladen werden!")

    # Hintergrundbild laden und ggf. skalieren
    background_image = load_image_asset(BACKGROUND_FILENAME, alpha=False)
    if background_image and background_image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
        try:
            background_image = pygame.transform.smoothscale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            logger.info("Hintergrundbild erfolgreich skaliert.")
        except Exception:
            logger.exception("Skalierung des Hintergrundbildes fehlgeschlagen:")
            background_image = None # Fallback auf Farbe

    # Button-Bild für Android laden
    button_image_normal = load_image_asset(BUTTON_FILENAME, alpha=True)
    # Geld-Icon für Inventar laden
    money_slot_background_img = load_image_asset(MONEY_ICON_FILENAME, alpha=True, scale_to=(SCALED_BOX_SIZE, SCALED_BOX_SIZE))
    if not money_slot_background_img:
        logger.warning(f"Bild für Geld-Slot ('{MONEY_ICON_FILENAME}') nicht geladen.")

    # Sounds laden
    no_resource_sound = load_sound_asset(NO_RESOURCE_SOUND_FILENAME)
    if no_resource_sound:
        # Lautstärke basierend auf Einstellungen anpassen
        sfx_vol = current_settings.get('sfx_volume', 0.5)
        master_vol = current_settings.get('master_volume', 1.0)
        no_resource_sound.set_volume(sfx_vol * master_vol * 0.5) # Beispiel: Halbe SFX-Lautstärke
    else:
        logger.warning(f"Sound für fehlende Ressourcen ('{NO_RESOURCE_SOUND_FILENAME}') nicht geladen.")

    # Spieler erstellen / laden
    player_start_x = WORLD_WIDTH // 2
    player_start_y = WORLD_HEIGHT // 2
    player_radius = TILE_SIZE // 3
    spawn_x, spawn_y = player_start_x, player_start_y
    player_money = 0.0 # Standard-Geld
    loaded_player_data = load_data(PLAYER_POS_SAVE_FILE)
    if isinstance(loaded_player_data, dict):
        try:
            spawn_x = int(loaded_player_data.get('x', spawn_x))
            spawn_y = int(loaded_player_data.get('y', spawn_y))
            player_money = float(loaded_player_data.get('money', player_money))
            logger.info("Spielerdaten (Position & Geld) erfolgreich geladen.")
        except (ValueError, TypeError) as e:
            logger.warning(f"Ungültige Spielerdaten geladen ({e}). Nutze Standardwerte.", exc_info=False)
            spawn_x, spawn_y = player_start_x, player_start_y # Reset zur Sicherheit
            player_money = 0.0
    else:
        logger.info("Keine Speicherdatei für Spielerdaten gefunden. Nutze Standardwerte.")
    player = Player(spawn_x, spawn_y, player_radius, RED)
    logger.info(f"Spieler erstellt bei ({spawn_x},{spawn_y}), Geld: {player_money:.2f}")

    # Kamera erstellen und initial positionieren
    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
    # Kamera auf Spieler zentrieren (unter Berücksichtigung der Weltgrenzen)
    cam_x = max(0, min(player.rect.centerx - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
    cam_y = max(0, min(player.rect.centery - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))
    camera.camera_rect.topleft = (cam_x, cam_y)
    logger.info("Kamera initialisiert.")

    # Inventar erstellen / laden
    inventory = Inventory(filepath=INVENTORY_SAVE_FILE) # Nutzt Pfad aus Konstanten
    logger.info("Inventar erstellt/geladen.")
    # Start-Items hinzufügen, falls nicht vorhanden (nur beim ersten Start relevant)
    if not inventory.has_item("Blumentopf"): inventory.add_item("Blumentopf", 3)
    if not inventory.has_item("Sack Erde"): inventory.add_item("Sack Erde", 5)
    if not inventory.has_item("Weed Seeds"): inventory.add_item("Weed Seeds", 10)
    if not inventory.has_item("Verpackstation"): inventory.add_item("Verpackstation", 1)
    if not inventory.has_item("Grips"): inventory.add_item("Grips", 20) # Start-Grips hinzufügen

    # Sprite-Gruppen initialisieren
    all_sprites = pygame.sprite.Group()
    npcs = pygame.sprite.Group()
    placed_items = pygame.sprite.Group() # Wichtig!

    # Platzierte Items laden
    logger.debug("Lade platzierte Items...")
    loaded_items_list = load_data(PLACED_ITEMS_SAVE_FILE, default_data=[]) # Gib leere Liste als Default zurück
    loaded_item_count = 0
    if isinstance(loaded_items_list, list):
        for item_data in loaded_items_list:
            if isinstance(item_data, dict):
                try:
                    item_type = item_data.get('type')
                    item_x = item_data.get('x')
                    item_y = item_data.get('y')

                    # Prüfen, ob essentielle Daten vorhanden sind
                    if not item_type or item_x is None or item_y is None:
                        logger.warning(f"Unvollständiger Item-Eintrag übersprungen: {item_data}")
                        continue

                    item_x = int(item_x)
                    item_y = int(item_y)
                    item_state = item_data.get('state') # Kann None sein, wird in PlacedItem behandelt
                    item_timer = item_data.get('timer_end') # Kann None sein
                    item_grow_time = item_data.get('grow_time')

                    # Setze grow_time explizit, falls nicht im Speicherstand (für ältere Speicherstände)
                    if item_grow_time is None:
                        item_grow_time = GROW_TIME_SECONDS if item_type == "Blumentopf" else 0

                    # Bilder für das Item holen (oder Fallback nutzen)
                    images_for_item = placed_item_images.get(item_type, {})
                    fallback_img = fallback_placed_image

                    # Neues PlacedItem Objekt erstellen
                    new_item = items.PlacedItem(
                        item_x, item_y, item_type, images_for_item, fallback_img,
                        item_grow_time, item_state, item_timer
                    )

                    # Zum Spiel hinzufügen, wenn erfolgreich erstellt
                    if new_item and hasattr(new_item, 'rect') and new_item.rect:
                        all_sprites.add(new_item)
                        placed_items.add(new_item)
                        loaded_item_count += 1
                        # logger.debug(f"  -> Geladenes Item '{item_type}' hinzugefügt bei ({item_x},{item_y}).") # Weniger verbose
                    else:
                        logger.error(f"  -> FEHLER: Geladenes PlacedItem {item_type} konnte nicht hinzugefügt werden. Daten: {item_data}")

                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Fehler beim Verarbeiten des gespeicherten Items '{item_data}': {e}", exc_info=False)
                except Exception as e_load:
                    logger.error(f"Allgemeiner Fehler beim Laden eines Items: {item_data}", exc_info=True)
            else:
                logger.warning(f"Ungültiger Typ in Speicherdatei für platzierte Items gefunden: {type(item_data)}")
        logger.info(f"{loaded_item_count} platzierte Items geladen.")
    elif loaded_items_list is not None: # Falls load_data etwas anderes als Liste oder None zurückgibt
        logger.warning(f"Inhalt der Speicherdatei für platzierte Items ('{PLACED_ITEMS_FILENAME}') war keine Liste: {type(loaded_items_list)}.")
    else: # Falls load_data None zurückgibt (Datei nicht gefunden)
        logger.info(f"Keine Speicherdatei für platzierte Items ('{PLACED_ITEMS_FILENAME}') gefunden oder Datei war leer.")

    # NPCs erstellen
    npc_radius = TILE_SIZE // 3
    # Beispiel-NPCs (Positionen anpassen!)
    npc_g = NPC(WORLD_WIDTH - TILE_SIZE * 10, TILE_SIZE * 15, npc_radius, GREY, "generic", "generic_hallo")
    # Händler in der Nähe des Spieler-Spawns
    merchant_x = max(npc_radius, min(spawn_x + TILE_SIZE * 5, WORLD_WIDTH - npc_radius))
    merchant_y = max(npc_radius, min(spawn_y + TILE_SIZE * 3, WORLD_HEIGHT - npc_radius))
    npc_m = NPC(merchant_x, merchant_y, npc_radius, BLUE, "merchant", "händler_start")
    # Kunde etwas neben dem Händler
    client_x = max(npc_radius, min(merchant_x + 200, WORLD_WIDTH - npc_radius))
    client_y = merchant_y # Gleiche Höhe wie Händler
    npc_client = NPC(client_x, client_y, npc_radius, DARK_GREEN, "client", "client_start")

    # Spieler und NPCs zu Sprite-Gruppen hinzufügen
    all_sprites.add(player)
    npcs.add(npc_g, npc_m, npc_client)
    all_sprites.add(npcs) # Füge die NPC-Gruppe zur Haupt-Gruppe hinzu
    logger.info(f"NPCs erstellt. Gesamt Sprites in all_sprites: {len(all_sprites)}")

    # Finale UI-Anpassungen (z.B. Button-Position basierend auf Inventar)
    # Nutze die tatsächliche Größe des geladenen Button-Bildes, falls vorhanden
    if platform_utils.IS_ANDROID and button_image_normal:
        btn_w_actual, btn_h_actual = button_image_normal.get_size()
    else:
        btn_w_actual, btn_h_actual = BTN_DEF_W, BTN_DEF_H # Fallback auf berechnete Größe

    # Y-Position des Buttons über dem Inventar
    BUTTON_Y = CENTERED_INVENTORY_Y_POS - btn_h_actual - BUTTON_PADDING
    BUTTON_RECT.size = (btn_w_actual, btn_h_actual)
    BUTTON_RECT.topleft = (BUTTON_X, BUTTON_Y)
    logger.debug(f"Finale Button Rect berechnet: {BUTTON_RECT}")

    # Android Immersive Mode aktivieren (versteckt Navigations-/Statusleiste)
    if platform_utils.IS_ANDROID:
        platform_utils.set_android_immersive_mode()
        logger.info("Android Immersive Mode aktiviert.")

except Exception as e:
    logger.critical("Kritischer Fehler während der Initialisierung des Spiels.", exc_info=True)
    if pygame.get_init():
        pygame.quit()
    sys.exit("FEHLER: Spielinitialisierung fehlgeschlagen.")

# ========= FUNKTIONEN ZUM ZEICHNEN DER UI-ZUSTÄNDE =========
# WICHTIG: Diese Funktionen müssen definiert sein, BEVOR sie in der Spielschleife aufgerufen werden!

def draw_sell_ui():
    """Zeichnet das Verkaufsfenster für Weed."""
    global sell_item_rect, sell_button_rect, sell_exit_button_rect # Globale Rects für Klick-Erkennung

    margin = 50 # Rand um das UI-Fenster
    sell_ui_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)

    # Hintergrund und Rand des Fensters
    pygame.draw.rect(screen, DARK_GREEN, sell_ui_rect)
    pygame.draw.rect(screen, WHITE, sell_ui_rect, 3) # Rand

    # Titel
    if ui_font:
        title_surf = ui_font.render("Weed Verkaufen", True, YELLOW)
        title_rect = title_surf.get_rect(centerx=sell_ui_rect.centerx, top=sell_ui_rect.top + 15)
        screen.blit(title_surf, title_rect)

    # Aktuelles Geld anzeigen
    if inventory_font: # Benötigt inventory_font
        try:
            # Formatierte Währung (mit Locale) oder einfacher Float
            money_txt_sell = locale.currency(player_money, grouping=True) if LOCALE_SET else f"{player_money:.2f} $"
        except Exception:
            money_txt_sell = f"{player_money:.2f}" # Fallback bei Formatierungsfehler
        money_surf = inventory_font.render(f"Dein Geld: {money_txt_sell}", True, GREEN)
        money_rect = money_surf.get_rect(right=sell_ui_rect.right - 20, top=sell_ui_rect.top + 20)
        screen.blit(money_surf, money_rect)

    # Bereich für das zu verkaufende Item (hier nur Weed)
    item_name_to_sell = "Weed"
    item_price = WEED_SELL_PRICE
    item_icon = item_icons.get(item_name_to_sell) # Icon aus geladenen Assets holen
    item_qty = 0
    try:
        if inventory:
             item_qty = inventory.get_item_count(item_name_to_sell)
        else:
             logger.warning("draw_sell_ui: Inventar ist None bei Abfrage der Menge!")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Item-Menge für '{item_name_to_sell}' in draw_sell_ui: {e}")

    item_area_x = sell_ui_rect.left + 30
    item_area_y = sell_ui_rect.top + 70
    item_area_w = sell_ui_rect.width - 60
    item_area_h = 100
    sell_item_rect = pygame.Rect(item_area_x, item_area_y, item_area_w, item_area_h)
    pygame.draw.rect(screen, GREY, sell_item_rect) # Hintergrund für Item-Bereich
    pygame.draw.rect(screen, WHITE, sell_item_rect, 1) # Rand für Item-Bereich

    # Item-Icon und Text zeichnen
    text_start_x = sell_item_rect.left + 15
    if item_icon:
        icon_rect = item_icon.get_rect(centery=sell_item_rect.centery, left=sell_item_rect.left + 15)
        screen.blit(item_icon, icon_rect)
        text_start_x = icon_rect.right + 20 # Text rechts neben dem Icon
    else:
        logger.warning(f"Kein Icon für '{item_name_to_sell}' im Verkaufs-UI gefunden.")

    if shop_font:
        name_surf = shop_font.render(f"{item_name_to_sell} (Du hast: {item_qty})", True, WHITE)
        name_rect = name_surf.get_rect(left=text_start_x, top=sell_item_rect.top + 15)
        screen.blit(name_surf, name_rect)

        try:
            price_txt_sell = locale.currency(item_price, grouping=True) if LOCALE_SET else f"{item_price:.2f} $"
        except Exception:
            price_txt_sell = f"{item_price:.2f}"
        price_surf = shop_font.render(f"Preis pro Stück: {price_txt_sell}", True, YELLOW)
        price_rect = price_surf.get_rect(left=text_start_x, top=name_rect.bottom + 10)
        screen.blit(price_surf, price_rect)

    # Verkaufen-Button
    button_w = 150
    button_h = 40
    button_y = sell_item_rect.bottom + 20
    button_x = sell_item_rect.centerx - button_w // 2
    sell_button_rect_instance = pygame.Rect(button_x, button_y, button_w, button_h)

    if item_qty > 0: # Button nur aktiv, wenn man etwas hat
        hover = sell_button_rect_instance.collidepoint(pygame.mouse.get_pos())
        btn_col = LIGHT_GREY if hover else GREY
        pygame.draw.rect(screen, btn_col, sell_button_rect_instance)
        pygame.draw.rect(screen, WHITE, sell_button_rect_instance, 1) # Rand
        if button_font:
            sell_text_surf = button_font.render("1 Verkaufen", True, BLACK)
            sell_text_rect = sell_text_surf.get_rect(center=sell_button_rect_instance.center)
            screen.blit(sell_text_surf, sell_text_rect)
        sell_button_rect = sell_button_rect_instance # Rect für Klick-Erkennung speichern
    else: # Button inaktiv
        pygame.draw.rect(screen, (50, 50, 50), sell_button_rect_instance) # Dunkler Hintergrund
        pygame.draw.rect(screen, GREY, sell_button_rect_instance, 1) # Rand
        if button_font:
            sell_text_surf = button_font.render("Nichts da", True, LIGHT_GREY)
            sell_text_rect = sell_text_surf.get_rect(center=sell_button_rect_instance.center)
            screen.blit(sell_text_surf, sell_text_rect)
        sell_button_rect = None # Kein Klick-Rect speichern

    # Verlassen-Button
    exit_w = 100; exit_h = 40
    exit_x = sell_ui_rect.centerx - exit_w // 2
    exit_y = sell_ui_rect.bottom - exit_h - 15
    sell_exit_button_rect = pygame.Rect(exit_x, exit_y, exit_w, exit_h)
    hover = sell_exit_button_rect.collidepoint(pygame.mouse.get_pos())
    exit_col = RED if hover else DARK_BLUE
    pygame.draw.rect(screen, exit_col, sell_exit_button_rect)
    pygame.draw.rect(screen, WHITE, sell_exit_button_rect, 2) # Rand
    if button_font:
        exit_surf = button_font.render("Verlassen", True, WHITE)
        exit_rect = exit_surf.get_rect(center=sell_exit_button_rect.center)
        screen.blit(exit_surf, exit_rect)

def draw_dialog_ui(node):
    """Zeichnet das Dialogfenster basierend auf dem aktuellen Dialogknoten."""
    global dialog_response_rects # Liste der Klick-Rects für Antworten wird hier gefüllt

    dialog_response_rects.clear() # Alte Rects entfernen

    if node and dialog_font:
        # Dimensionen und Position des Dialogfensters (z.B. unteres Drittel)
        dlg_h = SCREEN_HEIGHT // 3
        dlg_y = SCREEN_HEIGHT - dlg_h
        dlg_rect = pygame.Rect(0, dlg_y, SCREEN_WIDTH, dlg_h)

        # Hintergrund und Rand zeichnen
        pygame.draw.rect(screen, DARK_BLUE, dlg_rect) # Halbtransparenter Hintergrund
        pygame.draw.rect(screen, WHITE, dlg_rect, 3)   # Weißer Rand

        # NPC Text anzeigen (mit Zeilenumbruch)
        npc_txt_rect = pygame.Rect(
            dlg_rect.left + 20, dlg_rect.top + 15,
            dlg_rect.width - 40, dlg_rect.height // 2 - 30 # Bereich für NPC Text
        )
        wrap_text(screen, node.get("npc_text", "Dialogfehler..."), dialog_font, WHITE, npc_txt_rect)

        # Spieler-Antworten als Buttons zeichnen
        resp_y = npc_txt_rect.bottom + 15 # Start Y-Position für Antworten
        resp_h = 35 # Höhe eines Antwort-Buttons
        resp_sp = 10 # Vertikaler Abstand zwischen Buttons
        btn_w = dlg_rect.width // 2 - 30 # Breite eines Antwort-Buttons

        for i, response in enumerate(node.get("responses", [])):
            btn_x = dlg_rect.left + 20
            btn_y = resp_y + i * (resp_h + resp_sp)

            # Sicherstellen, dass der Button nicht aus dem Dialogfenster ragt
            if btn_y + resp_h > dlg_rect.bottom - 10:
                logger.warning("Nicht genug Platz für alle Dialogantworten.")
                break

            resp_rect = pygame.Rect(btn_x, btn_y, btn_w, resp_h)
            dialog_response_rects.append(resp_rect) # Rect zur Klick-Erkennung hinzufügen

            # Hover-Effekt
            mouse_pos = pygame.mouse.get_pos()
            hover = resp_rect.collidepoint(mouse_pos)
            btn_col = LIGHT_GREY if hover else GREY

            pygame.draw.rect(screen, btn_col, resp_rect)
            pygame.draw.rect(screen, WHITE, resp_rect, 1) # Rand

            # Text der Antwort zentriert im Button
            resp_surf = dialog_font.render(response.get("text", "?"), True, BLACK)
            resp_rect_txt = resp_surf.get_rect(center=resp_rect.center)
            screen.blit(resp_surf, resp_rect_txt)

    elif not node:
        logger.error(f"Ungültiger Dialog-Knoten ('{current_dialog_node_id}') in draw_dialog_ui übergeben.")
        # Optional: Automatisch zum Spiel zurückkehren bei Fehler
        # global current_game_state, active_npc, current_dialog_node_id
        # current_game_state = GAME_STATE_PLAY
        # active_npc = None
        # current_dialog_node_id = None

def draw_shop_ui():
    """Zeichnet das Shop-Fenster."""
    global shop_item_rects, shop_exit_button_rect # Globale Rects für Klick-Erkennung

    shop_item_rects.clear() # Alte Item-Rects löschen
    margin = 50
    shop_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)

    # Hintergrund und Rand
    pygame.draw.rect(screen, DARK_BLUE, shop_rect)
    pygame.draw.rect(screen, WHITE, shop_rect, 3)

    # Titel
    if ui_font:
        title_surf = ui_font.render("Shop", True, YELLOW)
        title_rect = title_surf.get_rect(centerx=shop_rect.centerx, top=shop_rect.top + 15)
        screen.blit(title_surf, title_rect)

    # Geld anzeigen
    if inventory_font: # Benötigt inventory_font
        try:
            money_txt_shop = locale.currency(player_money, grouping=True) if LOCALE_SET else f"{player_money:.2f} $"
        except:
            money_txt_shop = f"{player_money:.2f}"
        money_surf_shop = inventory_font.render(f"Dein Geld: {money_txt_shop}", True, GREEN)
        money_rect_shop = money_surf_shop.get_rect(right=shop_rect.right - 20, top=shop_rect.top + 20)
        screen.blit(money_surf_shop, money_rect_shop)

    # Grid für Shop-Items zeichnen
    cols = 4 # Anzahl Spalten im Shop
    rows = 4 # Maximale Anzahl Zeilen (Anpassen nach Bedarf)
    available_items_list = shop_items.get_available_items() # Holt Liste der Shop-Items

    grid_x = shop_rect.left + 30
    grid_y = shop_rect.top + 70 # Unterhalb Titel und Geld
    grid_area_height = shop_rect.height - 120 # Platz für Grid (ohne Titel, Geld, Exit-Button)
    cell_w = (shop_rect.width - 60) // cols
    cell_h = grid_area_height // rows
    icon_size = min(cell_w // 2, cell_h // 2) # Größe für Item-Icons im Shop

    for i, item_data in enumerate(available_items_list):
        if i >= cols * rows: # Nicht mehr Items zeichnen als Platz ist
            logger.warning("Mehr Shop-Items verfügbar als angezeigt werden können.")
            break

        row = i // cols
        col = i % cols
        cell_x = grid_x + col * cell_w
        cell_y = grid_y + row * cell_h

        cell_rect = pygame.Rect(cell_x, cell_y, cell_w - 10, cell_h - 10) # Kleiner Abstand zwischen Zellen
        shop_item_rects.append(cell_rect) # Rect für Klick-Erkennung speichern

        # Hover-Effekt für Item-Zelle
        mouse_pos = pygame.mouse.get_pos()
        hover = cell_rect.collidepoint(mouse_pos)
        cell_col = LIGHT_GREY if hover else GREY
        pygame.draw.rect(screen, cell_col, cell_rect)
        pygame.draw.rect(screen, WHITE, cell_rect, 1) # Rand

        # Item-Icon und Preis zeichnen
        name = item_data.get("name", "Unbekannt")
        price = item_data.get("price", 0.0)
        icon_surf_shop = item_icons.get(name) # Icon aus globalem Dict holen

        text_y_start = cell_rect.top + 5
        if icon_surf_shop:
            # Icon skalieren, falls nötig
            shop_icon_scaled = icon_surf_shop
            if shop_icon_scaled.get_size() != (icon_size, icon_size):
                try:
                    shop_icon_scaled = pygame.transform.smoothscale(shop_icon_scaled, (icon_size, icon_size))
                except Exception as e_scale:
                    logger.error(f"Fehler beim Skalieren des Shop-Icons für {name}: {e_scale}")
                    shop_icon_scaled = None # Kein Icon zeichnen bei Fehler

            if shop_icon_scaled:
                icon_rect_shop = shop_icon_scaled.get_rect(centerx=cell_rect.centerx, top=cell_rect.top + 5)
                screen.blit(shop_icon_scaled, icon_rect_shop)
                text_y_start = icon_rect_shop.bottom + 3 # Text unter Icon
        elif shop_font: # Fallback: Nur Namen anzeigen, wenn kein Icon
             name_surf = shop_font.render(name, True, WHITE)
             name_rect = name_surf.get_rect(centerx=cell_rect.centerx, top=text_y_start)
             screen.blit(name_surf, name_rect)
             text_y_start = name_rect.bottom + 3

        # Preis anzeigen
        if shop_font:
            try:
                price_txt = locale.currency(price, grouping=True) if LOCALE_SET else f"{price:.2f} $"
            except:
                price_txt = f"{price:.2f}"
            price_surf_shop = shop_font.render(price_txt, True, YELLOW)
            price_rect_shop = price_surf_shop.get_rect(centerx=cell_rect.centerx, bottom=cell_rect.bottom - 5)
            screen.blit(price_surf_shop, price_rect_shop)

    # Verlassen-Button
    exit_w = 100; exit_h = 40
    exit_x = shop_rect.centerx - exit_w // 2
    exit_y = shop_rect.bottom - exit_h - 15
    shop_exit_button_rect = pygame.Rect(exit_x, exit_y, exit_w, exit_h)
    hover = shop_exit_button_rect.collidepoint(pygame.mouse.get_pos())
    exit_col = RED if hover else DARK_BLUE
    pygame.draw.rect(screen, exit_col, shop_exit_button_rect)
    pygame.draw.rect(screen, WHITE, shop_exit_button_rect, 2) # Rand
    if button_font:
        exit_surf = button_font.render("Verlassen", True, WHITE)
        exit_rect = exit_surf.get_rect(center=shop_exit_button_rect.center)
        screen.blit(exit_surf, exit_rect)


# ========= SPIEL-LOOP =========
running = True
logger.info("Spiel-Loop startet.")
while running:
    try:
        # Delta Time für Frame-unabhängige Bewegung/Updates
        dt = clock.tick(FPS) / 1000.0
        # Aktuelle Mausposition auf dem Bildschirm
        mouse_pos_screen = pygame.mouse.get_pos()
        # Gedrückte Tasten abfragen
        keys = pygame.key.get_pressed()

        # === UPDATES (nur im Play-Zustand) ===
        if current_game_state == GAME_STATE_PLAY:
            # --- Interaktionsziel finden ---
            closest_target = None
            min_dist_sq = (INTERACTION_RADIUS ** 2) # Quadrat der Distanz spart Wurzelziehen
            player_cx = player.rect.centerx
            player_cy = player.rect.centery
            closest_type = None # 'item' oder 'npc'

            # Suche nächstes platziertes Item im Radius
            for item in placed_items:
                # Grobe Prüfung (Bounding Box) zur Optimierung
                if abs(player_cx - item.rect.centerx) < INTERACTION_RADIUS * 1.5 and \
                   abs(player_cy - item.rect.centery) < INTERACTION_RADIUS * 1.5:
                    # Genaue Distanzberechnung (quadriert)
                    dist_sq = (player_cx - item.rect.centerx)**2 + (player_cy - item.rect.centery)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_target = item
                        closest_type = "item"

            # Suche nächsten NPC im Radius
            for npc_obj in npcs:
                 if abs(player_cx - npc_obj.rect.centerx) < INTERACTION_RADIUS * 1.5 and \
                    abs(player_cy - npc_obj.rect.centery) < INTERACTION_RADIUS * 1.5:
                    dist_sq = (player_cx - npc_obj.rect.centerx)**2 + (player_cy - npc_obj.rect.centery)**2
                    if dist_sq < min_dist_sq:
                         min_dist_sq = dist_sq
                         closest_target = npc_obj
                         closest_type = "npc"

            # Aktualisiere das potentielle Ziel
            potential_interaction_target = closest_target
            target_type = closest_type
            interaction_possible_now = (potential_interaction_target is not None)

            # Wenn Interaktion aktiv war, aber Ziel verloren/gewechselt wurde -> abbrechen
            if interaction_active and potential_interaction_target != closest_target:
                logger.debug("Interaktionsziel während des Haltens verloren/gewechselt.")
                interaction_active = False
                interaction_start_time = 0.0

            # --- Spielobjekte updaten ---
            player.update(keys, camera.get_current_screen_rect()) # Spielerbewegung
            camera.update(player) # Kamera folgt Spieler
            npcs.update() # NPC-Animationen/Bewegung (falls implementiert)
            placed_items.update(dt) # Item-Zustände updaten (z.B. Timer für Wachstum)

            # --- Aufheben-Logik (Langes Drücken) ---
            if (interaction_active and target_type == "item" and
                    potential_interaction_target == closest_target and # Sicherstellen, dass Ziel noch dasselbe ist
                    potential_interaction_target in placed_items and # Sicherstellen, dass Item noch existiert
                    time.time() - interaction_start_time >= LONG_PRESS_THRESHOLD):

                item_to_pickup = potential_interaction_target
                # Prüfen, ob das Item überhaupt aufgehoben werden kann (Definition in items.py?)
                if item_to_pickup.item_type in items.PLACEABLE_ITEMS: # Annahme: Alle platzierbaren sind aufhebbar
                    if inventory.add_item(item_to_pickup.item_type, 1):
                        logger.info(f"'{item_to_pickup.item_type}' erfolgreich aufgehoben und zum Inventar hinzugefügt.")
                        item_to_pickup.kill() # Entfernt Sprite aus allen Gruppen (placed_items, all_sprites)
                        # Reset Interaktion nach erfolgreichem Aufheben
                        interaction_active = False
                        interaction_start_time = 0.0
                        potential_interaction_target = None
                        target_type = None
                    else:
                        logger.warning(f"Aufheben von '{item_to_pickup.item_type}' fehlgeschlagen: Inventar voll?")
                        interaction_active = False # Interaktion abbrechen
                        interaction_start_time = 0.0
                else:
                    logger.warning(f"Versuch, nicht aufhebbares Item '{item_to_pickup.item_type}' aufzuheben.")
                    interaction_active = False # Interaktion abbrechen
                    interaction_start_time = 0.0


        # === EVENT HANDLING ===
        interaction_press_event_handled = False # Flag, um Doppelauslösung MOUSEBUTTONDOWN/UP zu vermeiden
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                logger.info("QUIT Event empfangen. Spiel wird beendet.")

            # --- Tastatur Events ---
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC schließt UI-Fenster oder geht zum Hauptmenü
                    if current_game_state != GAME_STATE_PLAY:
                        logger.info(f"ESC gedrückt: Schließe {current_game_state}.")
                        current_game_state = GAME_STATE_PLAY
                        active_npc = None # Dialog/Shop Kontext zurücksetzen
                        current_dialog_node_id = None
                    elif not platform_utils.IS_ANDROID: # Nur auf Desktop zum Hauptmenü
                        logger.info("ESC gedrückt im Spiel: Speichere und zurück zum Hauptmenü...")
                        save_game_state()
                        pygame.quit()
                        logger.info("Pygame beendet.")
                        # Versuche, das Hauptmenü-Skript neu zu starten
                        try:
                            # Stellt sicher, dass der Python Interpreter und das Hauptskript übergeben werden
                            os.execv(sys.executable, [sys.executable, MAIN_SCRIPT_PATH])
                        except Exception as e:
                            logger.critical("Neustart des Hauptmenüs fehlgeschlagen!", exc_info=True)
                            sys.exit("FEHLER: Hauptmenü konnte nicht neu gestartet werden.")

                # Leertaste für Interaktion (nur Desktop)
                elif (event.key == pygame.K_SPACE and current_game_state == GAME_STATE_PLAY
                      and not platform_utils.IS_ANDROID):
                    if not interaction_active and interaction_possible_now:
                        interaction_active = True
                        interaction_press_event_handled = True # Markieren, dass DOWN-Event behandelt wurde
                        interaction_start_time = time.time()
                        target_name = getattr(potential_interaction_target, 'item_type',
                                              getattr(potential_interaction_target, 'npc_type', '?'))
                        logger.info(f"Start Interaktion (SPACE gedrückt) mit {target_type} '{target_name}'")

            elif event.type == pygame.KEYUP:
                 # Leertaste losgelassen (nur Desktop) -> Kurze Interaktion
                if (event.key == pygame.K_SPACE and current_game_state == GAME_STATE_PLAY
                    and not platform_utils.IS_ANDROID):
                    if interaction_active and potential_interaction_target:
                        press_duration = time.time() - interaction_start_time
                        is_short_press = press_duration < LONG_PRESS_THRESHOLD

                        if is_short_press:
                            # --- Kurze Interaktion (SPACE losgelassen) ---
                            if target_type == "item" and potential_interaction_target in placed_items:
                                item = potential_interaction_target
                                # Verpackstation Interaktion (ZipWeed Minispiel)
                                if item.item_type == "Verpackstation":
                                    logger.info("Kurze Interaktion mit Verpackstation (SPACE).")
                                    try:
                                        # Prüfe Ressourcen im Inventar
                                        weed_count = inventory.get_item_count("Weed")
                                        grips_count = inventory.get_item_count("Grips")
                                        logger.debug(f"Inventar vor ZipWeed (SPACE): {weed_count} Weed, {grips_count} Grips.")
                                        if weed_count > 0 and grips_count > 0:
                                            logger.info("Starte ZipWeed Minispiel (SPACE)...")
                                            save_game_state() # Spielstand vor Minispiel speichern
                                            # Rufe die importierte Funktion auf
                                            final_weed, final_grips, packed_count, outcome = run_zip_weed_game(
                                                screen, weed_count, grips_count, "Normal", current_settings
                                            )
                                            logger.info(f"ZipWeed Minispiel (SPACE) beendet. Ergebnis: Weed={final_weed}, Grips={final_grips}, Verpackt={packed_count}, Outcome: {outcome}")

                                            # Inventar aktualisieren basierend auf Ergebnis
                                            weed_consumed = weed_count - final_weed
                                            grips_consumed = grips_count - final_grips
                                            if weed_consumed > 0: inventory.remove_item("Weed", weed_consumed)
                                            if grips_consumed > 0: inventory.remove_item("Grips", grips_consumed)
                                            if packed_count > 0:
                                                 if not inventory.add_item("VerpacktesWeed", packed_count):
                                                      logger.warning("Konnte nicht alle 'VerpacktesWeed' hinzufügen (Inventar voll?).")
                                            # TODO: Evtl. Feedback basierend auf 'outcome'
                                        else:
                                            logger.info("Nicht genug Weed oder Grips für Verpackstation (SPACE).")
                                            if no_resource_sound: no_resource_sound.play()
                                    except Exception as e_minigame:
                                        logger.exception("FEHLER während/nach ZipWeed Minispiel (SPACE):")

                                # Blumentopf Interaktion (Wachstumsprozess)
                                elif item.item_type == "Blumentopf":
                                    logger.debug(f"Kurze Interaktion (SPACE) mit Blumentopf (Zustand: {item.state})")
                                    if item.state == 'ohneErde':
                                        if inventory.has_item("Sack Erde", 1):
                                            if inventory.remove_item("Sack Erde", 1):
                                                logger.info("Sack Erde verbraucht. Starte Minispiel 1 (Erde füllen)...")
                                                save_game_state()
                                                success = False
                                                try:
                                                    result = subprocess.run(
                                                        [sys.executable, MINIGAME_GROW1_PATH],
                                                        capture_output=True, text=True, check=False,
                                                        encoding='utf-8', errors='ignore', cwd=project_root_dir_game
                                                    )
                                                    success = (result.returncode == 0)
                                                    logger.info(f"Minispiel 1 (Erde) beendet. Return Code={result.returncode}. Success={success}")
                                                    if not success: logger.warning(f"Minispiel 1 Output: STDOUT='{result.stdout.strip() if result.stdout else ''}' STDERR:'{result.stderr.strip() if result.stderr else ''}'")
                                                except Exception:
                                                    logger.exception("Fehler bei Ausführung Minispiel 1 (Erde):")
                                                    success = False
                                                if success:
                                                    item.state = 'ohneSeed'
                                                    item.update_appearance()
                                                    logger.info("Blumentopf Zustand -> ohneSeed")
                                                else:
                                                    inventory.add_item("Sack Erde", 1) # Item zurückgeben bei Fehler
                                                    logger.info("Minispiel 1 fehlgeschlagen. Sack Erde wiederhergestellt.")
                                            else: logger.error("Konnte Sack Erde nicht aus Inventar entfernen, obwohl vorhanden?")
                                        else:
                                            logger.info("Kein Sack Erde im Inventar für Blumentopf.")
                                            if no_resource_sound: no_resource_sound.play()

                                    elif item.state == 'ohneSeed':
                                        if inventory.has_item("Weed Seeds", 1):
                                            if inventory.remove_item("Weed Seeds", 1):
                                                logger.info("Weed Seeds verbraucht. Starte Minispiel 2 (Pflanzen/Gießen)...")
                                                save_game_state()
                                                success = False
                                                try:
                                                     result = subprocess.run(
                                                         [sys.executable, MINIGAME_GROW2_PATH],
                                                         capture_output=True, text=True, check=False,
                                                         encoding='utf-8', errors='ignore', cwd=project_root_dir_game
                                                     )
                                                     success = (result.returncode == 0)
                                                     logger.info(f"Minispiel 2 (Samen) beendet. Return Code={result.returncode}. Success={success}")
                                                     if not success: logger.warning(f"Minispiel 2 Output: STDOUT='{result.stdout.strip() if result.stdout else ''}' STDERR:'{result.stderr.strip() if result.stderr else ''}'")
                                                except Exception:
                                                     logger.exception("Fehler bei Ausführung Minispiel 2 (Samen):")
                                                     success = False
                                                if success:
                                                     item.state = 'giessen' # Nächster Zustand nach Minispiel 2
                                                     item.update_appearance()
                                                     logger.info("Blumentopf Zustand -> giessen")
                                                else:
                                                     inventory.add_item("Weed Seeds", 1) # Item zurückgeben
                                                     logger.info("Minispiel 2 fehlgeschlagen. Weed Seeds wiederhergestellt.")
                                            else: logger.error("Konnte Weed Seeds nicht aus Inventar entfernen, obwohl vorhanden?")
                                        else:
                                            logger.info("Keine Weed Seeds im Inventar für Blumentopf.")
                                            if no_resource_sound: no_resource_sound.play()

                                    elif item.state == 'giessen':
                                        item.interact() # Startet den Wachstumstimer (in PlacedItem definiert)

                                    elif item.state == 'readyToEarn':
                                        logger.info("Ernteaktion (SPACE). Starte Minispiel 3 (Ernten)...")
                                        save_game_state()
                                        success = False; earned_amount = 0
                                        try:
                                            result = subprocess.run(
                                                [sys.executable, MINIGAME_EARN_WEED_PATH],
                                                capture_output=True, text=True, check=False,
                                                encoding='utf-8', errors='ignore', cwd=project_root_dir_game
                                            )
                                            logger.info(f"Minispiel 3 (Ernten) beendet. RC={result.returncode}. STDOUT='{result.stdout.strip() if result.stdout else ''}'")
                                            if result and result.returncode == 0:
                                                success = True
                                                try:
                                                    # Letzte Zeile des Outputs sollte die Menge sein
                                                    earned_amount = int(result.stdout.strip().splitlines()[-1])
                                                    logger.info(f"Erfolgreich geerntet: {earned_amount} Weed.")
                                                except (ValueError, IndexError, TypeError):
                                                    logger.error(f"Konnte Ernte-Menge nicht aus Minispiel-Output lesen: '{result.stdout.strip()}'")
                                                    earned_amount = 0 # Kein Ertrag bei Fehler
                                            else:
                                                logger.warning(f"Minispiel 3 (Ernten) fehlgeschlagen. RC={result.returncode if result else 'N/A'}. STDERR:'{result.stderr.strip() if result and result.stderr else ''}'")
                                        except Exception:
                                            logger.exception("Fehler bei Ausführung Minispiel 3 (Ernten):")
                                            success = False
                                        if success:
                                            if earned_amount > 0:
                                                if inventory.add_item("Weed", earned_amount):
                                                    logger.info(f"{earned_amount} Weed zum Inventar hinzugefügt.")
                                                else:
                                                    logger.warning("Konnte geerntetes Weed nicht hinzufügen (Inventar voll?).")
                                            # Zustand zurücksetzen nach Ernte
                                            item.state = 'ohneErde'
                                            item.update_appearance()
                                            logger.info("Blumentopf Zustand zurückgesetzt -> ohneErde")
                                        else:
                                            logger.info("Minispiel 3 (Ernten) nicht erfolgreich. Zustand bleibt 'readyToEarn'.")

                                    elif item.state == 'growing':
                                        item.interact() # Zeigt verbleibende Zeit im Log

                                    else:
                                        logger.warning(f"Unbehandelter Blumentopf-Zustand für kurze Interaktion (SPACE): {item.state}")
                                else:
                                    logger.warning(f"Kurze Interaktion (SPACE) für Item-Typ '{item.item_type}' ist nicht definiert.")

                            # --- Kurze Interaktion mit NPC (SPACE losgelassen) ---
                            elif target_type == "npc":
                                active_npc = potential_interaction_target
                                logger.info(f"Interagiere mit NPC '{active_npc.npc_type}' (SPACE kurz)")
                                if active_npc.dialog_id:
                                    # Spezifische Logik für NPC-Typen vor Dialogstart
                                    if active_npc.npc_type == "client" and not inventory.has_item("Weed", 1):
                                        current_dialog_node_id = "client_nichts_da" # Alternativer Startknoten
                                        logger.info("Client angesprochen, aber kein Weed dabei.")
                                    else:
                                        current_dialog_node_id = active_npc.dialog_id # Normaler Startknoten

                                    current_game_state = GAME_STATE_DIALOG
                                    logger.info(f"-> Wechsle zu GAME_STATE_DIALOG (Startknoten: {current_dialog_node_id})")
                                else:
                                    logger.warning(f"NPC '{active_npc.npc_type}' hat keine Dialog-ID.")
                                    active_npc = None # Kein Dialog möglich

                        # Reset Interaktionsstatus nach Loslassen (egal ob kurz oder lang)
                        if current_game_state == GAME_STATE_PLAY: # Nur wenn kein UI geöffnet wurde
                             potential_interaction_target = None # Ziel zurücksetzen
                             target_type = None
                        interaction_active = False
                        interaction_start_time = 0.0
                    else: # Falls interaction_active false war (sollte nicht passieren bei KEYUP nach KEYDOWN)
                        interaction_active = False
                        interaction_start_time = 0.0
                        target_type = None

            # --- Maus Events ---
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Linksklick
                # Android Button Klick (Startet Interaktion)
                if (current_game_state == GAME_STATE_PLAY and platform_utils.IS_ANDROID
                        and BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen)):
                    if not interaction_active and interaction_possible_now:
                        interaction_active = True
                        interaction_press_event_handled = True # Button wurde gedrückt
                        interaction_start_time = time.time()
                        target_name = getattr(potential_interaction_target,'item_type', getattr(potential_interaction_target,'npc_type','?'))
                        logger.info(f"Start Interaktion (Android Button gedrückt) mit {target_type} '{target_name}'")

                # Drag & Drop Start (wenn nicht auf Android Button geklickt wurde)
                elif (current_game_state == GAME_STATE_PLAY and not is_dragging and
                      (not platform_utils.IS_ANDROID or not (BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen)))):
                    # Prüfe, ob Klick im Inventarbereich war
                    inv_list_display = inventory.get_item_list_for_display() # Holt sichtbare Items
                    for i in range(MAX_SLOTS): # Gehe durch die sichtbaren Slots
                        slot_x = CENTERED_INVENTORY_X_POS + i * (SCALED_BOX_SIZE + SCALED_PADDING)
                        slot_y = CENTERED_INVENTORY_Y_POS
                        slot_rect = pygame.Rect(slot_x, slot_y, SCALED_BOX_SIZE, SCALED_BOX_SIZE)

                        if slot_rect.collidepoint(mouse_pos_screen) and i < len(inv_list_display):
                            item_name_inv, item_qty_inv = inv_list_display[i]
                            # Prüfen, ob das Item platzierbar ist und vorhanden
                            if item_name_inv in items.PLACEABLE_ITEMS and item_qty_inv > 0:
                                is_dragging = True
                                dragged_item_type = item_name_inv
                                # Versuche, ein passendes Vorschaubild zu finden
                                # 1. Inventar-Icon nehmen
                                dragged_item_image_try = item_icons.get(dragged_item_type)
                                # 2. Wenn kein Icon, Bild des platzierten Items im Startzustand
                                if not dragged_item_image_try:
                                     start_state = 'default' if dragged_item_type == "Verpackstation" else 'ohneErde'
                                     dragged_item_image_try = placed_item_images.get(dragged_item_type, {}).get(start_state)
                                # 3. Wenn immer noch nichts, Fallback-Bild
                                if dragged_item_image_try:
                                     dragged_item_image = dragged_item_image_try.copy()
                                     # Auf Zielgröße skalieren (PLACED_ITEM_SIZE)
                                     if dragged_item_image.get_size() != (PLACED_ITEM_SIZE, PLACED_ITEM_SIZE):
                                          try:
                                              dragged_item_image = pygame.transform.smoothscale(dragged_item_image, (PLACED_ITEM_SIZE, PLACED_ITEM_SIZE))
                                          except Exception:
                                               logger.warning(f"Skalierung der Drag-Vorschau für '{dragged_item_type}' fehlgeschlagen.")
                                               dragged_item_image = fallback_placed_image # Nutze Fallback
                                else:
                                     dragged_item_image = fallback_placed_image # Nutze Fallback
                                     logger.warning(f"Kein geeignetes Drag-Vorschaubild für '{dragged_item_type}' gefunden, nutze Fallback.")

                                logger.info(f"Starte Drag & Drop für: {dragged_item_type}")
                                break # Schleife verlassen, sobald ein Item gezogen wird

                # UI Klicks (Dialog, Shop, Sell)
                elif current_game_state == GAME_STATE_DIALOG:
                    # Prüfe Klick auf Antwort-Buttons
                    for i, rect in enumerate(dialog_response_rects):
                        if rect.collidepoint(mouse_pos_screen):
                            node = dialog.get_dialog_node(current_dialog_node_id)
                            if node and i < len(node.get("responses", [])):
                                response = node["responses"][i]
                                action = response.get("action")
                                next_node = response.get("next_node")
                                logger.debug(f"Dialog Antwort '{response.get('text', '?')}' geklickt. Aktion: {action}, Nächster Knoten: {next_node}")

                                if action == "open_shop":
                                    current_game_state = GAME_STATE_SHOP
                                    logger.info("-> Wechsle zu GAME_STATE_SHOP")
                                elif action == "open_sell_menu":
                                    # Nur öffnen, wenn Spieler Weed hat
                                    if inventory.has_item("Weed", 1):
                                        current_game_state = GAME_STATE_SELL
                                        logger.info("-> Wechsle zu GAME_STATE_SELL")
                                    else:
                                        current_dialog_node_id = "client_nichts_da" # Bleibe im Dialog, aber anderer Text
                                        logger.info("Verkaufsmenü angefordert, aber kein Weed. Zeige 'nichts_da' Dialog.")
                                elif action == "end_dialog":
                                    current_game_state = GAME_STATE_PLAY
                                    current_dialog_node_id = None
                                    active_npc = None
                                    logger.info("-> Dialog beendet, zurück zu GAME_STATE_PLAY")
                                elif next_node:
                                    current_dialog_node_id = next_node # Zum nächsten Dialogknoten wechseln
                                else: # Wenn keine Aktion und kein nächster Knoten -> Dialog beenden
                                    current_game_state = GAME_STATE_PLAY
                                    current_dialog_node_id = None
                                    active_npc = None
                                    logger.info("-> Dialog beendet (keine Aktion/NextNode), zurück zu GAME_STATE_PLAY")
                            else:
                                 logger.warning(f"Klick auf ungültigen Dialog-Antwort-Index {i} für Knoten {current_dialog_node_id}")
                            break # Nur eine Antwort pro Klick

                elif current_game_state == GAME_STATE_SHOP:
                    item_clicked = False
                    available_shop_items = shop_items.get_available_items()
                    # Prüfe Klick auf Shop-Items
                    for i, rect in enumerate(shop_item_rects):
                        if rect.collidepoint(mouse_pos_screen):
                            item_clicked = True
                            if i < len(available_shop_items):
                                item_to_buy = available_shop_items[i]
                                name = item_to_buy.get("name")
                                price = item_to_buy.get("price")
                                if name and price is not None:
                                    logger.debug(f"Versuche '{name}' für {price:.2f} zu kaufen.")
                                    if player_money >= price:
                                        if inventory.add_item(name, 1):
                                            player_money -= price
                                            logger.info(f"Erfolgreich gekauft: {name}. Neues Geld: {player_money:.2f}")
                                            # Optional: Sound abspielen
                                        else:
                                            logger.warning(f"Kauf von '{name}' fehlgeschlagen: Inventar voll?")
                                            if no_resource_sound: no_resource_sound.play() # Evtl. anderen Sound?
                                    else:
                                        logger.warning(f"Kauf von '{name}' fehlgeschlagen: Nicht genug Geld (benötigt {price:.2f}, hat {player_money:.2f}).")
                                        if no_resource_sound: no_resource_sound.play()
                                else:
                                    logger.error(f"Ungültige Item-Daten im Shop an Index {i}: {item_to_buy}")
                            else:
                                logger.warning(f"Klick auf ungültigen Shop-Item-Index {i}.")
                            break # Nur ein Item pro Klick

                    # Prüfe Klick auf Verlassen-Button (nur wenn kein Item geklickt wurde)
                    if not item_clicked and shop_exit_button_rect and shop_exit_button_rect.collidepoint(mouse_pos_screen):
                        current_game_state = GAME_STATE_PLAY
                        active_npc = None # Kontext zurücksetzen
                        current_dialog_node_id = None
                        logger.info("-> Shop verlassen, zurück zu GAME_STATE_PLAY")

                elif current_game_state == GAME_STATE_SELL:
                     # Prüfe Klick auf Verkaufen-Button
                    if sell_button_rect and sell_button_rect.collidepoint(mouse_pos_screen):
                         if inventory.has_item("Weed", 1):
                             if inventory.remove_item("Weed", 1):
                                 player_money += WEED_SELL_PRICE
                                 logger.info(f"1 Weed verkauft. Neues Geld: {player_money:.2f}")
                                 # Optional: Sound abspielen
                             else:
                                 logger.error("Konnte Weed nicht aus Inventar entfernen, obwohl has_item True war?")
                         else:
                             logger.warning("Klick auf Verkaufen-Button, aber kein Weed mehr vorhanden.")
                             # Button sollte eigentlich deaktiviert sein (sell_button_rect is None)

                     # Prüfe Klick auf Verlassen-Button
                    elif sell_exit_button_rect and sell_exit_button_rect.collidepoint(mouse_pos_screen):
                         current_game_state = GAME_STATE_PLAY
                         active_npc = None # Kontext zurücksetzen
                         current_dialog_node_id = None
                         logger.info("-> Verkaufsmenü verlassen, zurück zu GAME_STATE_PLAY")


            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: # Linksklick losgelassen
                if current_game_state == GAME_STATE_PLAY:
                    # Android Button Loslassen (Kurze Interaktion)
                    # Prüfe, ob der Button vorher gedrückt wurde (interaction_press_event_handled)
                    # und ob der Mauszeiger immer noch über dem Button ist
                    if (platform_utils.IS_ANDROID and interaction_active and interaction_press_event_handled
                            and BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen)):

                        if potential_interaction_target: # Ziel muss noch vorhanden sein
                            press_duration = time.time() - interaction_start_time
                            is_short_press = press_duration < LONG_PRESS_THRESHOLD

                            if is_short_press:
                                # --- Kurze Interaktion (Android Button losgelassen) ---
                                if target_type == "item" and potential_interaction_target in placed_items:
                                    item = potential_interaction_target
                                    # Verpackstation (Android)
                                    if item.item_type == "Verpackstation":
                                        logger.info("Kurze Interaktion mit Verpackstation (Android Button).")
                                        try:
                                            weed_count = inventory.get_item_count("Weed")
                                            grips_count = inventory.get_item_count("Grips")
                                            logger.debug(f"Inventar vor ZipWeed (Android): {weed_count} Weed, {grips_count} Grips.")
                                            if weed_count > 0 and grips_count > 0:
                                                logger.info("Starte ZipWeed Minispiel (Android)...")
                                                save_game_state()
                                                final_weed, final_grips, packed_count, outcome = run_zip_weed_game(
                                                    screen, weed_count, grips_count, "Normal", current_settings
                                                )
                                                logger.info(f"ZipWeed Minispiel (Android) beendet. Ergebnis: Weed={final_weed}, Grips={final_grips}, Verpackt={packed_count}, Outcome: {outcome}")
                                                weed_consumed = weed_count - final_weed; grips_consumed = grips_count - final_grips
                                                if weed_consumed > 0: inventory.remove_item("Weed", weed_consumed)
                                                if grips_consumed > 0: inventory.remove_item("Grips", grips_consumed)
                                                if packed_count > 0 and not inventory.add_item("VerpacktesWeed", packed_count):
                                                     logger.warning("Konnte nicht alle 'VerpacktesWeed' (Android) hinzufügen (Inventar voll?).")
                                            else:
                                                logger.info("Nicht genug Weed oder Grips für Verpackstation (Android).")
                                                if no_resource_sound: no_resource_sound.play()
                                        except Exception as e_minigame_a:
                                            logger.exception("FEHLER während/nach ZipWeed Minispiel (Android):")

                                    # Blumentopf (Android)
                                    elif item.item_type == "Blumentopf":
                                        logger.debug(f"Kurze Interaktion (Android Button) mit Blumentopf (Zustand: {item.state})")
                                        # (Logik ist identisch zu SPACE, kopieren oder Funktion auslagern)
                                        if item.state == 'ohneErde':
                                            if inventory.has_item("Sack Erde", 1):
                                                if inventory.remove_item("Sack Erde", 1):
                                                    logger.info("Sack Erde verbraucht (A). Starte Minispiel 1...")
                                                    save_game_state(); success=False
                                                    try:
                                                         result=subprocess.run([sys.executable, MINIGAME_GROW1_PATH], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', cwd=project_root_dir_game)
                                                         success=(result.returncode == 0); logger.info(f"Minispiel 1(A) Ende. RC={result.returncode}. Success={success}")
                                                    except Exception: logger.exception("Fehler Ausführung Minispiel 1(A):"); success=False
                                                    if success: item.state='ohneSeed'; item.update_appearance()
                                                    else: inventory.add_item("Sack Erde", 1); logger.info("Item wiederhergestellt (A).")
                                                else: logger.error("Konnte Sack Erde nicht entfernen(A)?")
                                            else: logger.info("Sack Erde fehlt (A).");
                                        elif item.state == 'ohneSeed':
                                            if inventory.has_item("Weed Seeds", 1):
                                                 if inventory.remove_item("Weed Seeds", 1):
                                                     logger.info("Seeds verbraucht (A). Starte Minispiel 2...")
                                                     save_game_state(); success=False
                                                     try:
                                                          result=subprocess.run([sys.executable, MINIGAME_GROW2_PATH], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', cwd=project_root_dir_game)
                                                          success=(result.returncode == 0); logger.info(f"Minispiel 2(A) Ende. RC={result.returncode}. Success={success}")
                                                     except Exception: logger.exception("Fehler Ausführung Minispiel 2(A):"); success=False
                                                     if success: item.state='giessen'; item.update_appearance()
                                                     else: inventory.add_item("Weed Seeds", 1); logger.info("Item wiederhergestellt (A).")
                                                 else: logger.error("Konnte Seeds nicht entfernen(A)?")
                                            else: logger.info("Seeds fehlen (A).");
                                        elif item.state == 'giessen': item.interact()
                                        elif item.state == 'readyToEarn':
                                             logger.info("Ernteaktion (A). Starte Minispiel 3..."); save_game_state(); success=False; earned_amount=0
                                             try:
                                                 result=subprocess.run([sys.executable, MINIGAME_EARN_WEED_PATH], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', cwd=project_root_dir_game)
                                                 logger.info(f"Minispiel 3(A) Ende. RC={result.returncode}. STDOUT:'{result.stdout.strip() if result.stdout else ''}'")
                                                 if result and result.returncode == 0:
                                                     success = True
                                                     try: earned_amount = int(result.stdout.strip().splitlines()[-1])
                                                     except: earned_amount=0
                                                 else: logger.warning(f"Minispiel 3(A) fail.")
                                             except Exception: logger.exception("Fehler Ausführung Minispiel 3(A):"); success=False
                                             if success:
                                                 if earned_amount > 0 and inventory.add_item("Weed", earned_amount): logger.info(f"{earned_amount} Weed hinzugefügt (A).")
                                                 elif earned_amount > 0: logger.warning("Konnte Weed nicht hinzufügen (A) (Inventar voll?).")
                                                 item.state = 'ohneErde'; item.update_appearance()
                                             else: logger.info("Minispiel 3(A) nicht erfolgreich.")
                                        elif item.state == 'growing': item.interact()
                                        else: logger.warning(f"Unbehandelter Blumentopf-Zustand (Button): {item.state}")
                                    else:
                                        logger.warning(f"Kurze Interaktion (Android Button) für Item '{item.item_type}' nicht definiert.")

                                # --- Kurze Interaktion mit NPC (Android Button losgelassen) ---
                                elif target_type == "npc":
                                     active_npc = potential_interaction_target
                                     logger.info(f"Interagiere mit NPC '{active_npc.npc_type}' (Android Button kurz)")
                                     if active_npc.dialog_id:
                                         if active_npc.npc_type == "client" and not inventory.has_item("Weed", 1):
                                             current_dialog_node_id = "client_nichts_da"
                                         else:
                                             current_dialog_node_id = active_npc.dialog_id
                                         current_game_state = GAME_STATE_DIALOG
                                         logger.info(f"-> Wechsle zu GAME_STATE_DIALOG (Startknoten: {current_dialog_node_id})")
                                     else:
                                         logger.warning(f"NPC '{active_npc.npc_type}' hat keine Dialog-ID.")
                                         active_npc = None

                        # Reset Interaktionsstatus nach Loslassen (egal ob kurz oder lang)
                        if current_game_state == GAME_STATE_PLAY: # Nur wenn kein UI geöffnet wurde
                             potential_interaction_target = None
                             target_type = None
                        interaction_active = False
                        interaction_start_time = 0.0
                        interaction_press_event_handled = False # Wichtig für nächsten Klick

                    # Drag & Drop Ende
                    elif is_dragging:
                        # Prüfen, ob außerhalb des Inventars und des Android-Buttons losgelassen wurde
                        inv_rect_check = pygame.Rect(
                            CENTERED_INVENTORY_X_POS, CENTERED_INVENTORY_Y_POS,
                            MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING, # Nur Item-Slots prüfen
                            SCALED_BOX_SIZE
                        )
                        # Prüfe auch Geld-Slot Bereich
                        money_slot_x_check = CENTERED_INVENTORY_X_POS + MAX_SLOTS * (SCALED_BOX_SIZE + SCALED_PADDING)
                        money_rect_check = pygame.Rect(money_slot_x_check, CENTERED_INVENTORY_Y_POS, SCALED_BOX_SIZE, SCALED_BOX_SIZE)

                        button_collide_check = platform_utils.IS_ANDROID and BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen)

                        if not inv_rect_check.collidepoint(mouse_pos_screen) and \
                           not money_rect_check.collidepoint(mouse_pos_screen) and \
                           not button_collide_check:
                            # Weltkoordinaten berechnen und an Grid ausrichten
                            world_x, world_y = camera.screen_to_world(*mouse_pos_screen)
                            # Berechne die obere linke Ecke der Zelle, in die geklickt wurde
                            snapped_tl_x = (world_x // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                            snapped_tl_y = (world_y // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                            # Berechne den Mittelpunkt der Zielzelle
                            snapped_center_x = snapped_tl_x + PLACED_ITEM_SIZE / 2
                            snapped_center_y = snapped_tl_y + PLACED_ITEM_SIZE / 2

                            # Prüfen, ob an der Zielposition bereits ein Item ist
                            can_place = True
                            temp_rect = pygame.Rect(snapped_tl_x, snapped_tl_y, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)
                            for item in placed_items:
                                if temp_rect.colliderect(item.rect):
                                    can_place = False
                                    logger.info(f"Platzieren von '{dragged_item_type}' blockiert durch Item '{item.item_type}' bei {item.rect.topleft}.")
                                    break

                            if can_place:
                                # Item aus Inventar entfernen
                                if inventory.remove_item(dragged_item_type, 1):
                                    # Bilder für das neue Item holen
                                    images_for_item = placed_item_images.get(dragged_item_type, {})
                                    fallback_img = fallback_placed_image
                                    # Startzustand bestimmen
                                    start_state = 'default' if dragged_item_type == "Verpackstation" else 'ohneErde'
                                    # Wachstumszeit bestimmen
                                    grow_time = GROW_TIME_SECONDS if dragged_item_type == "Blumentopf" else 0

                                    new_item = None # Zur Sicherheit initialisieren
                                    try:
                                        # Neues PlacedItem Objekt erstellen (am Mittelpunkt der Zelle)
                                        new_item = items.PlacedItem(
                                            snapped_center_x, snapped_center_y, dragged_item_type,
                                            images_for_item, fallback_img, grow_time, start_state, None
                                        )
                                        # Prüfen ob Erstellung erfolgreich war
                                        if not new_item or not hasattr(new_item, 'rect') or not new_item.rect:
                                            raise ValueError("Item Erstellung fehlgeschlagen oder ungültiges Rect.")

                                        # Zu Sprite-Gruppen hinzufügen
                                        all_sprites.add(new_item)
                                        placed_items.add(new_item)
                                        logger.info(f"'{dragged_item_type}' erfolgreich platziert bei ({snapped_tl_x},{snapped_tl_y}).")

                                    except Exception as e_create_add:
                                        logger.exception(f"FEHLER beim Erstellen/Hinzufügen des platzierten Items '{dragged_item_type}':")
                                        # Item im Inventar wiederherstellen, falls Platzieren fehlschlägt
                                        inventory.add_item(dragged_item_type, 1)
                                        if new_item and new_item.alive(): # Falls Item schon erstellt wurde, wieder entfernen
                                            new_item.kill()
                                else:
                                    logger.warning(f"Platzieren fehlgeschlagen: Konnte '{dragged_item_type}' nicht aus Inventar entfernen (Fehler in Inventar-Logik?).")
                            # else: (Platzieren blockiert, keine Aktion nötig)

                        else:
                            logger.info("Drag & Drop über Inventar oder Button beendet, Item nicht platziert.")

                        # Dragging-Status zurücksetzen
                        is_dragging = False
                        dragged_item_type = None
                        dragged_item_image = None

                    # Reset Interaktion, falls Button losgelassen wurde, aber nicht über Button/Ziel
                    # oder falls Maus losgelassen wurde ohne Dragging
                    elif interaction_active and interaction_press_event_handled:
                         interaction_active = False
                         interaction_start_time = 0.0
                         interaction_press_event_handled = False


        # === ZEICHNEN ===
        # --- Hintergrund / Overlay ---
        if current_game_state == GAME_STATE_PLAY:
            # Normaler Hintergrund im Spiel
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill(BLACK) # Fallback-Farbe
        else:
            # Hintergrund leicht abgedunkelt für UI-Fenster
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill(BLACK)
            # Dunkler Overlay darüber zeichnen
            dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) # SRCALPHA für Transparenz
            dark_overlay.fill((0, 0, 0, 150)) # Schwarz mit 150 Alpha (0=transparent, 255=opak)
            screen.blit(dark_overlay, (0, 0))

        # --- Zeichnen im Spielzustand ---
        if current_game_state == GAME_STATE_PLAY:
            # Alle Sprites zeichnen (relativ zur Kamera)
            for sprite in all_sprites:
                try:
                    # Nur zeichnen, wenn Sprite Bild und Rect hat UND im sichtbaren Bereich der Kamera ist
                    if (hasattr(sprite, 'image') and sprite.image and
                            hasattr(sprite, 'rect') and sprite.rect and
                            camera.get_current_screen_rect().colliderect(sprite.rect)):
                        screen.blit(sprite.image, camera.apply(sprite)) # camera.apply berechnet Bildschirmposition
                except Exception as e_draw:
                    # Fehler loggen, aber Spiel weiterlaufen lassen
                    logger.exception(f"Fehler beim Zeichnen von Sprite {sprite}: {e_draw}")

            # Interaktionsanzeige (Kreis um Spieler, Fortschrittsbalken für Aufheben)
            if interaction_active and potential_interaction_target:
                try:
                    # Kreis um Spieler auf Bildschirmkoordinaten
                    player_rect_screen = camera.apply_rect(player.rect)
                    center_screen = player_rect_screen.center
                    pygame.draw.circle(screen, WHITE, center_screen, int(INTERACTION_RADIUS), 1) # Dünner weißer Kreis

                    # Fortschrittsbalken für langes Drücken (Aufheben)
                    if interaction_start_time > 0 and target_type == "item":
                        hold_duration = time.time() - interaction_start_time
                        if hold_duration < LONG_PRESS_THRESHOLD:
                            progress = min(1.0, hold_duration / LONG_PRESS_THRESHOLD)
                            if progress > 0:
                                bar_w = 50; bar_h = 5
                                bar_x = center_screen[0] - bar_w // 2
                                bar_y = player_rect_screen.top - bar_h - 5 # Über dem Spieler
                                pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h)) # Hintergrund
                                pygame.draw.rect(screen, RED, (bar_x, bar_y, int(bar_w * progress), bar_h)) # Fortschritt
                except Exception:
                    logger.exception("Fehler beim Zeichnen der Interaktionsanzeige:")

            # UI-Texte (FPS, Ziel, etc.)
            try:
                if ui_font:
                    fps_text = f"FPS: {clock.get_fps():.1f}"
                    screen.blit(ui_font.render(fps_text, True, WHITE), (10, 10))

                    # Anzeige des potenziellen Interaktionsziels
                    target_display_text = "Target: None"
                    if not interaction_active and potential_interaction_target:
                        target_id_disp = getattr(potential_interaction_target, 'item_type', getattr(potential_interaction_target, 'npc_type', '?'))
                        target_display_text = f"Target: {target_type} ({target_id_disp})"
                        if target_type == 'item':
                             target_display_text += f" / State: {getattr(potential_interaction_target, 'state', 'N/A')}"
                    screen.blit(ui_font.render(target_display_text, True, YELLOW), (10, 35))
            except Exception:
                logger.exception("Fehler beim Zeichnen der UI-Texte:")

            # Inventar zeichnen (KORRIGIERTER AUFRUF)
            try:
                # Übergabe der Parameter, die die display-Methode in inventory.py erwartet
                inventory.display(
                    screen,
                    (CENTERED_INVENTORY_X_POS, CENTERED_INVENTORY_Y_POS), # Position
                    item_icons,                 # Icons zum Anzeigen
                    SCALED_BOX_SIZE,            # Größe der Slots
                    SCALED_PADDING              # Abstand zwischen Slots
                )
            except Exception:
                logger.exception("Fehler bei der Inventar-Anzeige:")

            # --- EXPLIZITES ZEICHNEN DES GELD-SLOTS ---
            try:
                # Berechne die Position des Geld-Slots (rechts neben dem letzten Item-Slot)
                # WICHTIG: Verwende die skalierten Werte hier!
                money_slot_x = CENTERED_INVENTORY_X_POS + MAX_SLOTS * (SCALED_BOX_SIZE + SCALED_PADDING)
                money_slot_y = CENTERED_INVENTORY_Y_POS
                money_slot_rect = pygame.Rect(money_slot_x, money_slot_y, SCALED_BOX_SIZE, SCALED_BOX_SIZE)

                # Hintergrund und Rand für Geld-Slot (verwende Farben/Breite aus inventory.py via Import)
                pygame.draw.rect(screen, BG_COLOR, money_slot_rect)
                pygame.draw.rect(screen, BORDER_COLOR, money_slot_rect, BORDER_WIDTH)

                # Geld-Icon zeichnen (falls geladen)
                if money_slot_background_img:
                    icon_rect = money_slot_background_img.get_rect(center=money_slot_rect.center)
                    screen.blit(money_slot_background_img, icon_rect)

                # Geld-Text zeichnen
                if inventory_font: # Verwende den Font, der auch für Item-Mengen vorgesehen war/ist
                     try:
                         # Formatiere Währung mit locale, falls verfügbar
                         money_text = locale.currency(player_money, grouping=True, symbol=True) if LOCALE_SET else f"{player_money:.2f}"
                         # Optional: Kürzen, falls Text zu lang wird
                         # money_text = f"{int(player_money)}"
                     except Exception:
                         money_text = f"{player_money:.2f}" # Fallback

                     # Render den Text (verwende Farbe aus inventory.py via Import)
                     money_surf = inventory_font.render(money_text, True, QUANTITY_COLOR)

                     # Positioniere den Text rechts unten im Geld-Slot (wie Item-Mengen)
                     money_rect = money_surf.get_rect(
                         bottomright=money_slot_rect.bottomright - pygame.Vector2(SCALED_PADDING // 2, SCALED_PADDING // 2)
                     )
                     screen.blit(money_surf, money_rect)
                else:
                     logger.warning("inventory_font nicht verfügbar zum Zeichnen des Geldbetrags.")

            except Exception:
                logger.exception("Fehler beim Zeichnen des Geld-Slots:")
            # --- ENDE GELD-SLOT ZEICHNEN ---


            # Drag-Vorschau zeichnen (wenn aktiv)
            if is_dragging and dragged_item_image:
                try:
                    # Weltkoordinaten der Maus -> Gitter-Koordinaten -> Bildschirmkoordinaten
                    world_x_drag, world_y_drag = camera.screen_to_world(*mouse_pos_screen)
                    snapped_tl_x_drag = (world_x_drag // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                    snapped_tl_y_drag = (world_y_drag // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                    temp_rect_world_drag = pygame.Rect(snapped_tl_x_drag, snapped_tl_y_drag, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)
                    snapped_rect_screen_drag = camera.apply_rect(temp_rect_world_drag)

                    # Leicht transparentes Vorschaubild an Mausposition (am Gitter ausgerichtet)
                    dragged_item_image.set_alpha(180) # Transparent machen
                    drag_rect_preview = dragged_item_image.get_rect(center=snapped_rect_screen_drag.center)
                    screen.blit(dragged_item_image, drag_rect_preview)
                    dragged_item_image.set_alpha(255) # Wieder opak für nächsten Frame

                    # Gitter-Zelle hervorheben
                    pygame.draw.rect(screen, WHITE, snapped_rect_screen_drag, 1)
                except Exception as e_drag_draw:
                    logger.error(f"Fehler beim Zeichnen der Drag-Vorschau: {e_drag_draw}", exc_info=False)

            # Android Interaktionsbutton zeichnen
            if platform_utils.IS_ANDROID and BUTTON_RECT:
                if button_image_normal:
                    # Geladenes Bild verwenden
                    screen.blit(button_image_normal, BUTTON_RECT.topleft)
                else:
                    # Fallback: Rechteck zeichnen
                    pygame.draw.rect(screen, BUTTON_COLOR_NORMAL, BUTTON_RECT)
                    pygame.draw.rect(screen, BUTTON_BORDER_COLOR, BUTTON_RECT, 2) # Rand
                # Text auf Button (optional, falls kein Bild)
                if button_font and not button_image_normal:
                    try:
                        btn_surf = button_font.render("Interact", True, WHITE)
                        btn_rect = btn_surf.get_rect(center=BUTTON_RECT.center)
                        screen.blit(btn_surf, btn_rect)
                    except Exception as e_btn_txt:
                        logger.error(f"Fehler beim Zeichnen des Button-Textes:{e_btn_txt}", exc_info=True)

        # --- Zeichnen in anderen UI-Zuständen ---
        elif current_game_state == GAME_STATE_DIALOG:
            draw_dialog_ui(dialog.get_dialog_node(current_dialog_node_id)) # Ruft die oben definierte Funktion auf
        elif current_game_state == GAME_STATE_SHOP:
            draw_shop_ui() # Ruft die oben definierte Funktion auf
        elif current_game_state == GAME_STATE_SELL:
            draw_sell_ui() # Ruft die oben definierte Funktion auf

        # --- Bildschirm aktualisieren ---
        pygame.display.flip() # Zeigt das gezeichnete Bild an

    # Fehlerbehandlung für die Hauptschleife
    except Exception as e_game_loop:
        logger.critical("Unerwarteter Fehler in der Haupt-Spielschleife:", exc_info=True)
        # Versuche, vor dem Beenden zu speichern
        try:
            save_game_state()
        except Exception as e_save_on_crash:
            logger.error("Konnte Spielstand nach kritischem Fehler nicht speichern.", exc_info=True)
        running = False # Beendet den Loop nach dem Fehler

# ========= SPIEL BEENDEN =========
logger.info("Spiel-Loop beendet.")
# Nur speichern, wenn das Spiel normal beendet wurde (running == True am Ende des Loops)
# Wenn es durch einen Fehler beendet wurde (running == False), wurde oben schon versucht zu speichern.
# -> Check entfernt, Speichern vor Quit/Exit ist sicherer
try:
     save_game_state()
except Exception as e_final_save:
     logger.error("Fehler beim finalen Speichern des Spielstands.", exc_info=True)

# Pygame sauber beenden
if pygame.get_init():
    pygame.quit()
    logger.info("Pygame erfolgreich beendet.")

# Programm beenden
sys.exit()