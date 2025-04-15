# game.py (Korrektur: Reihenfolge beim Platzieren geändert)
# Formatiert für maximale Lesbarkeit
# Stand: 2025-04-15 (Drag&Drop Fix)

# ========= MODULE IMPORTIEREN =========
# Standardbibliothek
import sys
import logging
import os
import math
import time
import traceback
import locale
import subprocess # Für Minispiel-Start

# Pygame
import pygame

# Eigene Module (Annahme: Liegen im Suchpfad oder relativ erreichbar)
try:
    import platform_utils # Für Android-spezifische Dinge
    from player import Player
    from npc import NPC # Stelle sicher, dass die NPC Klasse hier importiert wird
    from camera import Camera
    from inventory import Inventory, BOX_SIZE, PADDING, MAX_SLOTS
    from persistence import load_data, save_data
    import settings_utils
    # Stelle sicher, dass items jetzt PLACEABLE_ITEMS auf Modulebene hat
    import items
    import dialog # Enthält Dialogstruktur
    import shop_items # Enthält Shopangebot
except ImportError as e:
    # Kritischer Fehler, wenn ein Modul fehlt
    print(f"FATAL ERROR: Modul '{e.name}' nicht gefunden. Traceback:\n{traceback.format_exc()}")
    sys.exit(f"FEHLER: Modul '{e.name}' fehlt. Spiel kann nicht starten.")
except Exception as e:
    print(f"FATAL ERROR: Unerwarteter Fehler beim Importieren eigener Module. Traceback:\n{traceback.format_exc()}")
    sys.exit("FEHLER: Unerwarteter Import-Fehler. Spiel kann nicht starten.")

# ========= LOKALISIERUNG (Währung) =========
try:
    # Bevorzugt für Linux/macOS
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    LOCALE_SET = True
except locale.Error:
    try:
        # Fallback für Windows
        locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
        LOCALE_SET = True
    except locale.Error:
        # Fallback, wenn nichts geht
        print("WARNUNG: Locale 'de_DE' oder 'German_Germany.1252' nicht verfügbar für Währung.")
        LOCALE_SET = False

# ========= LOGGING KONFIGURATION =========
log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s' # Name hinzugefügt
log_level = logging.DEBUG # Sehr ausführlich für Entwicklung/Fehlersuche
date_fmt = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(
    level=log_level, format=log_format, datefmt=date_fmt, force=True
)
logger = logging.getLogger(__name__) # Logger für dieses Modul

# --- Pfad-Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.path.abspath(".")
# Annahme: game.py liegt in data/etc/ -> 2 Ebenen hoch zum Projekt-Root
project_root_dir = os.path.normpath(os.path.join(script_dir, "..", ".."))
data_dir_root = os.path.join(project_root_dir, "data")
log_dir = os.path.join(data_dir_root, "logs")
IMAGE_FOLDER = os.path.join(data_dir_root, "bilder")
SAVE_DATA_DIR_ABS = os.path.join(data_dir_root, "savedata")
SETTINGS_DIR = os.path.join(data_dir_root, "settings")
MINIGAME_FOLDER = os.path.join(data_dir_root, "miniGame", "Growing")

# --- Absolute Dateipfade ---
SETTINGS_FILE_PATH = os.path.join(SETTINGS_DIR, "settings.json")
MAIN_SCRIPT_PATH = os.path.join(project_root_dir, "main.py") # Annahme: main.py im Root
MINIGAME_GROW1_PATH = os.path.join(MINIGAME_FOLDER, "plant_grow1.py")
MINIGAME_GROW2_PATH = os.path.join(MINIGAME_FOLDER, "grow_plant2.py")
MINIGAME_EARN_WEED_PATH = os.path.join(MINIGAME_FOLDER, "earn_buds.py")
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
logger.debug(f"Project Root Verzeichnis: {project_root_dir}")
logger.debug(f"Pfad Minispiel 1 (Erde): {MINIGAME_GROW1_PATH}")
logger.debug(f"Pfad Minispiel 2 (Samen/Gießen): {MINIGAME_GROW2_PATH}") # Name angepasst
logger.debug(f"Pfad Minispiel 3 (Ernten): {MINIGAME_EARN_WEED_PATH}")


# ========= EINSTELLUNGEN LADEN =========
try:
    current_settings = settings_utils.load_settings(SETTINGS_FILE_PATH)
    logger.info(f"Einstellungen geladen: {current_settings}")
except Exception:
    logger.exception("FEHLER beim Laden der Einstellungen:")
    current_settings = {'music_volume': 0.5, 'sfx_volume': 0.5, 'master_volume': 0.5}
    logger.warning(f"Nutze Fallback-Einstellungen: {current_settings}")


# ========= KONSTANTEN =========
# --- Spielwelt & Physik ---
TILE_SIZE = 32
FPS = 60
INTERACTION_RADIUS = TILE_SIZE * 1.5 # Radius um Spieler für Interaktion
LONG_PRESS_THRESHOLD = 1.0 # Sekundenschwelle für langen vs. kurzen Druck
GROW_TIME_SECONDS = 10 # Basis-Wachstumszeit für Blumentopf (andere Items haben 0)

# --- Farben (RGB) ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0)
GREEN = (0, 200, 0) # Helles Grün
DARK_GREEN = (0, 100, 0) # NEU: Dunkles Grün für Client NPC
RED = (255, 0, 0); BLUE = (0, 0, 255); MAGENTA = (255, 0, 255)
GREY = (100, 100, 100); LIGHT_GREY = (180, 180, 180); DARK_BLUE = (0, 0, 100)
YELLOW = (255, 255, 0) # Für Verpackstation Fallback

# --- Visuelle Elemente ---
PLACED_ITEM_SIZE = TILE_SIZE # Größe platzierter Items (visuell)

# --- Inventar-Skalierung & Layout ---
INVENTORY_SCALE_FACTOR = 2.0
SCALED_BOX_SIZE = int(BOX_SIZE * INVENTORY_SCALE_FACTOR)
SCALED_PADDING = int(PADDING * INVENTORY_SCALE_FACTOR)
SCALED_ICON_W = max(1, SCALED_BOX_SIZE - SCALED_PADDING * 2)
SCALED_ICON_H = max(1, SCALED_BOX_SIZE - SCALED_PADDING * 2)
SCALED_ICON_SIZE = (SCALED_ICON_W, SCALED_ICON_H)
logger.debug(f"Berechnete Icon-Größe (skaliert): {SCALED_ICON_SIZE}")
INVENTORY_BOTTOM_PADDING = 20 # Abstand Inventar vom unteren Rand

# --- Button (Interaktion auf Android) ---
BUTTON_DEFAULT_WIDTH_PERCENT = 0.08 # % der Bildschirmbreite
BUTTON_DEFAULT_HEIGHT_PERCENT = 0.13 # % der Bildschirmhöhe
BUTTON_PADDING = 15 # Abstand Button von anderen UI-Elementen
BUTTON_X = BUTTON_PADDING # X-Position Button
BUTTON_COLOR_NORMAL = (80, 80, 80) # Fallback-Farbe
BUTTON_BORDER_COLOR = WHITE

# --- Fonts (Basisgrößen, werden skaliert) ---
FONT_SIZE_REF_H = 600.0 # Referenzhöhe für Font-Skalierung
BASE_UI_FONT_SIZE = 28
BASE_BUTTON_FONT_SIZE = 18
BASE_INV_QTY_FONT_SIZE = 16
BASE_DIALOG_FONT_SIZE = 24
BASE_SHOP_FONT_SIZE = 18 # Wird auch für Sell UI verwendet

# --- Asset-Dateinamen ---
BACKGROUND_FILENAME = "background.png"
BUTTON_FILENAME = "interact_button.png"
MONEY_ICON_FILENAME = "money_icon.png"

# --- Spielzustände ---
GAME_STATE_PLAY = "play"
GAME_STATE_DIALOG = "dialog"
GAME_STATE_SHOP = "shop"
GAME_STATE_SELL = "sell" # NEU: Zustand für das Verkaufsmenü

# --- Gameplay ---
WEED_SELL_PRICE = 15.0 # NEU: Preis, den der Client für 1 Weed zahlt


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
    except FileNotFoundError: # Explizit abfangen für bessere Logs
         logger.warning(f"Bilddatei nicht gefunden: '{path}'")
         return None
    except Exception as e:
        logger.error(f"Allg. Fehler Laden Bild '{path}': {e}", exc_info=True)
        return None

    if scale_to:
        if (not isinstance(scale_to, (tuple, list))
                or len(scale_to) != 2
                or scale_to[0] <= 0
                or scale_to[1] <= 0):
            logger.error(f"Ungültiges scale_to '{scale_to}' für '{filename}'.")
        else:
            try:
                # smoothscale für bessere Qualität, scale wenn fehlerhaft
                if image.get_width() > 0 and image.get_height() > 0:
                      image = pygame.transform.smoothscale(image, scale_to)
                else:
                      logger.warning(f"Ungültige Bilddimensionen vor Skalierung für '{filename}'. Überspringe Skalierung.")

            except ValueError: # Kann bei 0-Dimensionen auftreten
                logger.error(f"ValueError beim Skalieren von '{filename}' zu {scale_to}. Bild ungültig?", exc_info=False)
            except Exception:
                logger.error(f"Fehler Skalieren '{filename}' zu {scale_to}", exc_info=True)
    return image

def save_game_state():
    """Speichert alle relevanten Spieldaten in separaten JSON-Dateien."""
    logger.info("Speichere Spielstand...")
    # Inventar
    try:
        if inventory:
            logger.info("  Speichere Inventar...")
            inventory.save_inventory() # Nutzt die Methode der Inventory-Klasse
        else:
            logger.warning("  Inventar nicht initialisiert.")
    except Exception:
        logger.exception("  Fehler Inv speichern:")
    # Spielerdaten
    try:
        if player:
            logger.info("  Speichere Spielerposition & Geld...")
            player_data = {'x': player.rect.x, 'y': player.rect.y, 'money': player_money}
            save_data(player_data, PLAYER_POS_SAVE_FILE)
        else:
            logger.warning("  Spieler nicht initialisiert.")
    except Exception:
        logger.exception("  Fehler Pos/Geld speichern:")
    # Platzierte Items
    try:
        if placed_items is not None:
            logger.info("  Speichere platzierte Items...")
            items_to_save = []
            for item in placed_items:
                # Füge nur hinzu, wenn das Item auch ein Rect hat (Sicherheitscheck)
                if hasattr(item, 'rect') and item.rect:
                     items_to_save.append({
                         'type': item.item_type,
                         'x': item.rect.centerx,
                         'y': item.rect.centery,
                         'state': item.state,
                         'timer_end': item.timer_end_timestamp,
                         'grow_time': item.grow_time_seconds
                     })
                else:
                     logger.warning(f"Überspringe Speichern von Item {item} (Typ: {getattr(item, 'item_type', '?')}), da es kein gültiges Rect hat.")

            save_data(items_to_save, PLACED_ITEMS_SAVE_FILE)
            logger.info(f"  {len(items_to_save)} platzierte Items gespeichert.")
        else:
            logger.warning("  Placed_items Gruppe nicht initialisiert.")
    except Exception:
        logger.exception("  Fehler Items speichern:")

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
            line_width, _ = font.size(' '.join(current_line_words))
            # Wenn Zeile zu lang wird
            if line_width > rect.width:
                # Wenn mehr als ein Wort -> letztes Wort zurück in die Liste
                if len(current_line_words) > 1:
                    last_word = current_line_words.pop()
                    words.insert(0, last_word)
                # Aktuelle Zeile (ohne das letzte Wort) speichern
                lines.append(' '.join(current_line_words))
                current_line_words = [] # Neue Zeile beginnen (ggf. mit dem 'last_word')
        except pygame.error:
            logger.exception("Fehler bei font.size() in wrap_text")
            return # Abbruch bei Font-Fehler

    # Letzte verbleibende Zeile hinzufügen
    if current_line_words:
        lines.append(' '.join(current_line_words))

    # Zeichne die erstellten Zeilen
    y = rect.top
    line_spacing = font.get_linesize() * 0.9 # Etwas weniger als Standard für kompakteres Aussehen
    line_height = font.get_height()

    for line in lines:
        # Prüfen, ob nächste Zeile noch ins Rechteck passt
        if y + line_height > rect.bottom:
            logger.warning("Textumbruch: Nicht alle Zeilen passen ins Rechteck.")
            break
        try:
            img = font.render(line, aa, color)
            surface.blit(img, (rect.left, y))
            y += int(line_spacing) # Zur nächsten Zeilenposition springen
        except pygame.error:
            logger.exception(f"Fehler bei font.render() für Zeile: '{line}'")
            break # Bei Fehler Schleife abbrechen


# ========= GLOBALE VARIABLEN (Initialisierung) =========
# Spielobjekte & Zustände
screen: pygame.Surface | None = None
clock: pygame.time.Clock | None = None
player: Player | None = None
camera: Camera | None = None
inventory: Inventory | None = None
all_sprites: pygame.sprite.Group | None = None # Alle sichtbaren Objekte
npcs: pygame.sprite.Group | None = None      # Nur NPCs (für spezifische Logik)
placed_items: pygame.sprite.Group | None = None # Nur platzierte Items (für spezifische Logik)

# UI Elemente & Fonts
ui_font: pygame.font.Font | None = None
button_font: pygame.font.Font | None = None
inventory_font: pygame.font.Font | None = None
dialog_font: pygame.font.Font | None = None
shop_font: pygame.font.Font | None = None # Wird auch für Sell UI verwendet
background_image: pygame.Surface | None = None
button_image_normal: pygame.Surface | None = None
money_slot_background_img: pygame.Surface | None = None
item_icons: dict = {}             # Geladene Icons {item_name: surface | None}
placed_item_images: dict = {}     # Geladene Zustandsbilder {item_type: {state: surface}}
fallback_placed_image: pygame.Surface | None = None # Generisches Fallback-Bild für Items (Magenta)

# Spielzustand & Interaktion
current_game_state: str = GAME_STATE_PLAY
player_money: float = 0.0
active_npc: NPC | None = None
current_dialog_node_id: str | None = None
dialog_response_rects: list = []
shop_item_rects: list = []
shop_exit_button_rect: pygame.Rect | None = None
sell_item_rect: pygame.Rect | None = None # Rect für das verkaufbare Item (nur für Anzeige)
sell_button_rect: pygame.Rect | None = None # Rect für den "Verkaufen"-Button
sell_exit_button_rect: pygame.Rect | None = None # Rect für den "Verlassen"-Button im Verkaufsmenü
is_dragging: bool = False
dragged_item_type: str | None = None
dragged_item_image: pygame.Surface | None = None # Bild für das gezogene Item
interaction_active: bool = False
interaction_start_time: float = 0.0
potential_interaction_target: pygame.sprite.Sprite | None = None # Item oder NPC
target_type: str | None = None # "item" oder "npc"

# UI Layout (wird nach Screen-Erstellung berechnet)
CENTERED_INVENTORY_X_POS: int = 0
CENTERED_INVENTORY_Y_POS: int = 0
BUTTON_RECT: pygame.Rect | None = None


# ========= HAUPT-INITIALISIERUNGSBLOCK =========
try:
    # --- Pygame & Mixer ---
    pygame.init()
    try:
        pygame.mixer.init()
        logger.info("Pygame Mixer initialisiert.")
    except pygame.error:
        logger.error("Mixer Init fehlgeschlagen", exc_info=True)

    # --- Bildschirm ---
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # Fallback
    try:
        info = pygame.display.Info()
        SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
        logger.info(f"Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        # Flags für Skalierung und Größenänderung
        screen_flags = pygame.SCALED | pygame.RESIZABLE
        # Bei Bedarf Vollbild hinzufügen (ggf. über Einstellung steuern)
        # screen_flags |= pygame.FULLSCREEN
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), screen_flags)
    except Exception:
        logger.warning("Bildschirm Fehler. Nutze Fallback 800x600.", exc_info=True)
        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
        try:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        except Exception as e_fallback:
            logger.critical("Fallback-Bildschirm Fehler", exc_info=True)
            pygame.quit()
            sys.exit(1) # Beenden mit Fehlercode
    if screen is None:
        logger.critical("Bildschirm konnte nicht initialisiert werden.")
        pygame.quit()
        sys.exit(1)
    pygame.display.set_caption("Das Spiel")
    clock = pygame.time.Clock()
    logger.info("Screen & Clock erstellt.")

    # --- Weltgröße ---
    WORLD_WIDTH = SCREEN_WIDTH * 3
    WORLD_HEIGHT = SCREEN_HEIGHT * 2
    logger.info(f"Weltgröße: {WORLD_WIDTH}x{WORLD_HEIGHT}")

    # --- Fonts ---
    # Skalierte Größen berechnen
    ui_fs = max(12, int(SCREEN_HEIGHT * (BASE_UI_FONT_SIZE / FONT_SIZE_REF_H)))
    btn_fs = max(10, int(SCREEN_HEIGHT * (BASE_BUTTON_FONT_SIZE / FONT_SIZE_REF_H)))
    inv_fs = max(8, int(SCREEN_HEIGHT * (BASE_INV_QTY_FONT_SIZE / FONT_SIZE_REF_H)))
    dlg_fs = max(14, int(SCREEN_HEIGHT * (BASE_DIALOG_FONT_SIZE / FONT_SIZE_REF_H)))
    shp_fs = max(10, int(SCREEN_HEIGHT * (BASE_SHOP_FONT_SIZE / FONT_SIZE_REF_H)))
    # Fonts laden
    try:
        ui_font = pygame.font.Font(None, ui_fs)
        button_font = pygame.font.Font(None, btn_fs)
        inventory_font = pygame.font.Font(None, inv_fs)
        dialog_font = pygame.font.Font(None, dlg_fs)
        shop_font = pygame.font.Font(None, shp_fs) # Für Shop und Sell UI
        logger.info(f"Fonts erstellt (Größen: UI={ui_fs}, Btn={btn_fs}, Inv={inv_fs}, Dlg={dlg_fs}, Shop={shp_fs}).")
    except Exception:
        logger.exception("Font Fehler:")
        # Fallback mit unskalierten Basisgrößen
        ui_font,button_font,inventory_font,dialog_font,shop_font=(pygame.font.Font(None, s) for s in [BASE_UI_FONT_SIZE,BASE_BUTTON_FONT_SIZE,BASE_INV_QTY_FONT_SIZE,BASE_DIALOG_FONT_SIZE,BASE_SHOP_FONT_SIZE])
        logger.warning("Nutze Fallback-Schriftarten mit Basisgrößen.")

    # --- UI Layout Berechnungen ---
    BTN_DEF_W = int(SCREEN_WIDTH * BUTTON_DEFAULT_WIDTH_PERCENT)
    BTN_DEF_H = int(SCREEN_HEIGHT * BUTTON_DEFAULT_HEIGHT_PERCENT)
    BUTTON_RECT = pygame.Rect(BUTTON_X, 0, BTN_DEF_W, BTN_DEF_H) # Y wird später gesetzt
    inv_w = MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING
    CENTERED_INVENTORY_X_POS = (SCREEN_WIDTH - inv_w) // 2
    CENTERED_INVENTORY_Y_POS = SCREEN_HEIGHT - SCALED_BOX_SIZE - INVENTORY_BOTTOM_PADDING
    logger.info("Inventar Position berechnet.")

    # --- Assets laden ---
    logger.info("Lade Assets...")
    # Nutzt die angepasste Funktion aus items.py
    item_icons, placed_item_images, fallback_placed_image = items.load_item_assets(
        IMAGE_FOLDER, PLACED_ITEM_SIZE, SCALED_ICON_SIZE, load_image_asset
    )
    background_image = load_image_asset(BACKGROUND_FILENAME, alpha=False)
    # Hintergrund an Bildschirm anpassen
    if background_image and background_image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
        try:
            background_image = pygame.transform.smoothscale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            logger.info("BG an Bildschirmgröße angepasst.")
        except Exception:
            logger.exception("BG Skalierung fehlgeschlagen:")
            background_image = None # Kein Hintergrund verwenden
    button_image_normal = load_image_asset(BUTTON_FILENAME, alpha=True)
    money_slot_background_img = load_image_asset(
        MONEY_ICON_FILENAME, alpha=True, scale_to=(SCALED_BOX_SIZE, SCALED_BOX_SIZE)
    )
    if not money_slot_background_img:
        logger.warning(f"'{MONEY_ICON_FILENAME}' nicht geladen, Geld-Slot hat Fallback-Farbe.")

    # --- Spielobjekte erstellen / Spielstand laden ---
    # Spieler
    player_start_x = WORLD_WIDTH // 2
    player_start_y = WORLD_HEIGHT // 2
    player_radius = TILE_SIZE // 3
    spawn_x, spawn_y = player_start_x, player_start_y
    player_money = 0.0
    loaded_player_data = load_data(PLAYER_POS_SAVE_FILE)
    if isinstance(loaded_player_data, dict):
        try:
            spawn_x = int(loaded_player_data.get('x', spawn_x))
            spawn_y = int(loaded_player_data.get('y', spawn_y))
        except ValueError: logger.warning("Ungültige Spieler-Positionsdaten geladen.")
        try:
            player_money = float(loaded_player_data.get('money', player_money))
        except ValueError: logger.warning("Ungültige Spieler-Gelddaten geladen.")
        logger.info("Spielerdaten geladen.")
    else: logger.info("Keine Spielerdatei gefunden. Nutze Standardwerte.")
    player = Player(spawn_x, spawn_y, player_radius, RED)
    logger.info(f"Spieler erstellt bei ({spawn_x},{spawn_y}), Geld: {player_money:.2f}")

    # Kamera
    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
    # Kamera initial auf Spieler zentrieren
    cam_x = max(0, min(player.rect.centerx - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
    cam_y = max(0, min(player.rect.centery - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))
    camera.camera_rect.topleft = (cam_x, cam_y)
    logger.info("Kamera initialisiert und ausgerichtet.")

    # Inventar
    inventory = Inventory(filepath=INVENTORY_SAVE_FILE)
    logger.info("Inventar erstellt/geladen.")
    # Start-Items hinzufügen, falls Inventar neu/leer ist
    if not inventory.has_item("Blumentopf"): inventory.add_item("Blumentopf", 3)
    if not inventory.has_item("Sack Erde"): inventory.add_item("Sack Erde", 5)
    if not inventory.has_item("Weed Seeds"): inventory.add_item("Weed Seeds", 10)
    if not inventory.has_item("Verpackstation"): inventory.add_item("Verpackstation", 1) # Start-Verpackstation
    # if not inventory.has_item("Weed"): inventory.add_item("Weed", 5) # Zum Testen des Verkaufs

    # Sprite-Gruppen
    all_sprites = pygame.sprite.Group()
    npcs = pygame.sprite.Group()
    placed_items = pygame.sprite.Group() # Gruppe nur für platzierbare Items

    # Platzierte Items laden
    logger.debug("Lade platzierte Items...")
    loaded_items_list = load_data(PLACED_ITEMS_SAVE_FILE, default_data=[])
    loaded_item_count = 0
    if isinstance(loaded_items_list, list):
        for item_data in loaded_items_list:
            if isinstance(item_data, dict):
                try:
                    item_type = item_data.get('type')
                    if not item_type:
                        logger.warning(f"Item-Typ fehlt in Speicherdaten: {item_data}")
                        continue

                    item_x = int(item_data['x'])
                    item_y = int(item_data['y'])
                    item_state = item_data.get('state')
                    item_timer = item_data.get('timer_end', None)
                    default_grow = GROW_TIME_SECONDS if item_type == "Blumentopf" else 0
                    item_grow_time = item_data.get('grow_time', default_grow)

                    images_for_this_type = placed_item_images.get(item_type, {})
                    fallback_img = fallback_placed_image

                    # Erstelle das Item-Objekt
                    new_item = items.PlacedItem(
                        item_x, item_y, item_type,
                        images_for_this_type,
                        fallback_img,
                        item_grow_time,
                        item_state,
                        item_timer
                    )

                    # Wichtig: Füge das Item ZU DEN GRUPPEN hinzu. alive() ist hier noch False!
                    # Die Validierung erfolgt implizit dadurch, ob es hinzugefügt werden kann
                    # und ob es ein gültiges Rect hat etc.
                    if new_item and hasattr(new_item, 'rect') and new_item.rect:
                         all_sprites.add(new_item)
                         placed_items.add(new_item)
                         loaded_item_count += 1
                         logger.debug(f"  -> Geladenes Item '{item_type}' zu Gruppen hinzugefügt.")
                    else:
                         logger.error(f"  -> FEHLER: Geladenes PlacedItem {item_type} konnte nicht hinzugefügt werden (Objekt ungültig oder kein Rect?). Daten: {item_data}")

                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Ungültiger Item-Eintrag in '{PLACED_ITEMS_FILENAME}': {item_data} -> {e}", exc_info=False)
                except Exception as e_load:
                     logger.error(f"Allg. Fehler beim Laden eines Items: {item_data}", exc_info=True)
            else:
                logger.warning(f"Ungültiger Typ in '{PLACED_ITEMS_FILENAME}': {type(item_data)}")
        logger.info(f"{loaded_item_count} platzierte Items geladen.")
    elif loaded_items_list is not None:
        logger.warning(f"'{PLACED_ITEMS_FILENAME}' war keine Liste, sondern {type(loaded_items_list)}.")
    else:
        logger.info(f"Keine Speicherdatei für platzierte Items ('{PLACED_ITEMS_FILENAME}') gefunden.")

    # NPCs erstellen
    npc_radius = TILE_SIZE // 3
    npc_g = NPC(WORLD_WIDTH - TILE_SIZE * 10, TILE_SIZE * 15, npc_radius, GREY, "generic", "generic_hallo")
    logger.debug(f"NPC Generic erstellt: {npc_g} at rect {npc_g.rect if hasattr(npc_g, 'rect') else 'N/A'}")

    merchant_x = spawn_x + TILE_SIZE * 5
    merchant_y = spawn_y + TILE_SIZE * 3
    merchant_x = max(npc_radius, min(merchant_x, WORLD_WIDTH - npc_radius))
    merchant_y = max(npc_radius, min(merchant_y, WORLD_HEIGHT - npc_radius))
    logger.debug(f"Angepasste Merchant-Position: ({merchant_x}, {merchant_y})")
    npc_m = NPC(merchant_x, merchant_y, npc_radius, BLUE, "merchant", "händler_start")
    logger.debug(f"NPC Merchant erstellt: {npc_m} at rect {npc_m.rect if hasattr(npc_m, 'rect') else 'N/A'}")

    client_offset_x = 200
    client_x = merchant_x + client_offset_x
    client_y = merchant_y
    client_x = max(npc_radius, min(client_x, WORLD_WIDTH - npc_radius))
    client_y = max(npc_radius, min(client_y, WORLD_HEIGHT - npc_radius))
    logger.debug(f"Angepasste Client-Position: ({client_x}, {client_y})")
    npc_client = NPC(client_x, client_y, npc_radius, DARK_GREEN, "client", "client_start")
    logger.debug(f"NPC Client erstellt: {npc_client} at rect {npc_client.rect if hasattr(npc_client, 'rect') else 'N/A'}")

    # Spieler und ALLE NPCs zu den Gruppen hinzufügen
    all_sprites.add(player)
    npcs.add(npc_g, npc_m, npc_client)
    all_sprites.add(npcs)
    # Geladene PlacedItems sind bereits in all_sprites und placed_items

    logger.debug(f"NPC Merchant in all_sprites: {npc_m in all_sprites}")
    logger.debug(f"NPC Client in all_sprites: {npc_client in all_sprites}")
    logger.debug(f"Anzahl Sprites in all_sprites nach Init (Player+NPCs+LoadedItems): {len(all_sprites)}")
    logger.debug(f"Anzahl NPCs in npcs group: {len(npcs)}")
    logger.debug(f"Anzahl PlacedItems nach Init: {len(placed_items)}")

    # --- Finale UI-Anpassungen ---
    if platform_utils.IS_ANDROID and button_image_normal:
        btn_w_act, btn_h_act = button_image_normal.get_size()
    else:
        btn_w_act, btn_h_act = BTN_DEF_W, BTN_DEF_H
    BUTTON_Y = CENTERED_INVENTORY_Y_POS - btn_h_act - BUTTON_PADDING
    BUTTON_RECT.size = (btn_w_act, btn_h_act)
    BUTTON_RECT.topleft = (BUTTON_X, BUTTON_Y)
    logger.debug(f"Finale Button Rect: {BUTTON_RECT}")

    # Android Immersive Mode
    if platform_utils.IS_ANDROID:
        platform_utils.set_android_immersive_mode()
        logger.info("Immersive Mode für Android aktiviert.")

except Exception as e:
    logger.critical("Kritischer Fehler während der Initialisierung.", exc_info=True)
    if pygame.get_init(): pygame.quit()
    sys.exit(1)


# ========= NEUE FUNKTION: Verkaufs-UI zeichnen (KORRIGIERT) =========
def draw_sell_ui():
    """Zeichnet das Verkaufsfenster für den Client-NPC."""
    global sell_item_rect, sell_button_rect, sell_exit_button_rect # Globale Rects für Klicks

    margin = 50
    sell_ui_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)
    pygame.draw.rect(screen, DARK_GREEN, sell_ui_rect)
    pygame.draw.rect(screen, WHITE, sell_ui_rect, 3)

    if ui_font:
        title_surf = ui_font.render("Verkaufen", True, YELLOW)
        title_rect = title_surf.get_rect(centerx=sell_ui_rect.centerx, top=sell_ui_rect.top + 15)
        screen.blit(title_surf, title_rect)

    if inventory_font:
        try:
            money_txt_sell = locale.currency(player_money, grouping=True) if LOCALE_SET else f"{player_money:.2f} $"
        except Exception:
            money_txt_sell = f"{player_money:.2f}"
        m_surf_s = inventory_font.render(f"Dein Geld: {money_txt_sell}", True, GREEN)
        m_rect_s = m_surf_s.get_rect(right=sell_ui_rect.right - 20, top=sell_ui_rect.top + 20)
        screen.blit(m_surf_s, m_rect_s)

    item_name_to_sell = "Weed"
    item_price = WEED_SELL_PRICE
    item_icon = item_icons.get(item_name_to_sell)

    item_qty = 0
    try:
        if inventory:
            inv_list = inventory.get_item_list_for_display()
            for name, qty in inv_list:
                if name == item_name_to_sell:
                    item_qty = qty
                    break
        else:
            logger.warning("draw_sell_ui: Inventar ist nicht initialisiert!")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Item-Menge für '{item_name_to_sell}' aus dem Inventar: {e}")

    item_area_x = sell_ui_rect.left + 30
    item_area_y = sell_ui_rect.top + 70
    item_area_w = sell_ui_rect.width - 60
    item_area_h = 100

    sell_item_rect = pygame.Rect(item_area_x, item_area_y, item_area_w, item_area_h)
    pygame.draw.rect(screen, GREY, sell_item_rect)
    pygame.draw.rect(screen, WHITE, sell_item_rect, 1)

    if item_icon:
        icon_rect = item_icon.get_rect(centery=sell_item_rect.centery, left=sell_item_rect.left + 15)
        screen.blit(item_icon, icon_rect)
        text_start_x = icon_rect.right + 20
    else:
        text_start_x = sell_item_rect.left + 15

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

    button_w = 150
    button_h = 40
    button_y = sell_item_rect.bottom + 20
    button_x = sell_item_rect.centerx - button_w // 2

    sell_button_rect_instance = pygame.Rect(button_x, button_y, button_w, button_h)

    if item_qty > 0:
        hover = sell_button_rect_instance.collidepoint(pygame.mouse.get_pos())
        btn_col = LIGHT_GREY if hover else GREY
        pygame.draw.rect(screen, btn_col, sell_button_rect_instance)
        pygame.draw.rect(screen, WHITE, sell_button_rect_instance, 1)
        if button_font:
            sell_text_surf = button_font.render("1 Verkaufen", True, BLACK)
            sell_text_rect = sell_text_surf.get_rect(center=sell_button_rect_instance.center)
            screen.blit(sell_text_surf, sell_text_rect)
        sell_button_rect = sell_button_rect_instance
    else:
        pygame.draw.rect(screen, (50, 50, 50), sell_button_rect_instance)
        pygame.draw.rect(screen, GREY, sell_button_rect_instance, 1)
        if button_font:
            sell_text_surf = button_font.render("Nichts zu verkaufen", True, LIGHT_GREY)
            sell_text_rect = sell_text_surf.get_rect(center=sell_button_rect_instance.center)
            screen.blit(sell_text_surf, sell_text_rect)
        sell_button_rect = None

    exit_w = 100
    exit_h = 40
    exit_x = sell_ui_rect.centerx - exit_w // 2
    exit_y = sell_ui_rect.bottom - exit_h - 15
    sell_exit_button_rect = pygame.Rect(exit_x, exit_y, exit_w, exit_h)
    hover = sell_exit_button_rect.collidepoint(pygame.mouse.get_pos())
    exit_col = RED if hover else DARK_BLUE
    pygame.draw.rect(screen, exit_col, sell_exit_button_rect)
    pygame.draw.rect(screen, WHITE, sell_exit_button_rect, 2)
    if button_font:
        exit_surf = button_font.render("Verlassen", True, WHITE)
        exit_rect = exit_surf.get_rect(center=sell_exit_button_rect.center)
        screen.blit(exit_surf, exit_rect)


# ========= SPIEL-LOOP =========
running = True
logger.info("Spiel-Loop startet.")
while running:
    try:
        # Delta Time berechnen
        dt = clock.tick(FPS) / 1000.0
        # Aktuelle Mausposition holen
        mouse_pos_screen = pygame.mouse.get_pos()
        # Aktuell gedrückte Tasten holen
        keys = pygame.key.get_pressed()

        # === UPDATES (nur im Play-Zustand) ===
        if current_game_state == GAME_STATE_PLAY:
            # --- Interaktionsziel finden ---
            closest_target = None
            min_dist_sq = (INTERACTION_RADIUS ** 2)
            player_cx = player.rect.centerx
            player_cy = player.rect.centery
            closest_type = None

            # Items prüfen (nur die in der 'placed_items' Gruppe)
            for item in placed_items:
                if abs(player_cx - item.rect.centerx) < INTERACTION_RADIUS * 1.5 and \
                   abs(player_cy - item.rect.centery) < INTERACTION_RADIUS * 1.5:
                    dist_sq = (player_cx - item.rect.centerx)**2 + (player_cy - item.rect.centery)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_target = item
                        closest_type = "item"
            # NPCs prüfen
            for npc_obj in npcs:
                 if abs(player_cx - npc_obj.rect.centerx) < INTERACTION_RADIUS * 1.5 and \
                    abs(player_cy - npc_obj.rect.centery) < INTERACTION_RADIUS * 1.5:
                     dist_sq = (player_cx - npc_obj.rect.centerx)**2 + (player_cy - npc_obj.rect.centery)**2
                     if dist_sq < min_dist_sq:
                         min_dist_sq = dist_sq
                         closest_target = npc_obj
                         closest_type = "npc"

            potential_interaction_target = closest_target
            target_type = closest_type
            interaction_possible_now = (potential_interaction_target is not None)

            if interaction_active and potential_interaction_target != closest_target:
                logger.debug("Interaktionsziel während des Haltens verloren/gewechselt.")
                interaction_active = False
                interaction_start_time = 0.0

            # --- Spielobjekte updaten ---
            player.update(keys, camera.get_current_screen_rect())
            camera.update(player)
            npcs.update()
            placed_items.update(dt)

            # --- Aufheben-Logik (Langes Drücken auf PlacedItem) ---
            if (interaction_active and
                    target_type == "item" and
                    potential_interaction_target and
                    potential_interaction_target == closest_target and
                    potential_interaction_target in placed_items and
                    time.time() - interaction_start_time >= LONG_PRESS_THRESHOLD):

                item_to_pickup = potential_interaction_target
                # Prüfen ob das Item überhaupt aufhebbar ist (NUTZT MODULVARIABLE)
                if item_to_pickup.item_type in items.PLACEABLE_ITEMS:
                    item_type_pickup = item_to_pickup.item_type
                    logger.info(f"Langes Drücken -> Versuch Pickup '{item_type_pickup}'")

                    if inventory.add_item(item_type_pickup, 1):
                        logger.info(f"'{item_type_pickup}' zum Inventar hinzugefügt.")
                        item_to_pickup.kill() # Entfernt aus ALLEN Gruppen
                        logger.info("Item aus Welt entfernt.")
                        interaction_active = False
                        interaction_start_time = 0.0
                        potential_interaction_target = None
                        target_type = None
                    else:
                        logger.warning(f"Aufheben von '{item_type_pickup}' fehlgeschlagen: Inventar voll?")
                        interaction_active = False
                        interaction_start_time = 0.0
                else:
                    logger.warning(f"Item '{item_to_pickup.item_type}' ist als 'item' erkannt, aber nicht in PLACEABLE_ITEMS? Aufheben nicht möglich.")
                    interaction_active = False
                    interaction_start_time = 0.0


        # === EVENT HANDLING (Alle Zustände) ===
        interaction_press_event_handled = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                logger.info("QUIT Event empfangen.")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_game_state in [GAME_STATE_DIALOG, GAME_STATE_SHOP, GAME_STATE_SELL]:
                        logger.info(f"ESC: {current_game_state} geschlossen.")
                        current_game_state = GAME_STATE_PLAY
                        active_npc = None
                        current_dialog_node_id = None
                    elif not platform_utils.IS_ANDROID:
                        logger.info("ESC: Zurück zum Hauptmenü...")
                        save_game_state()
                        pygame.quit()
                        logger.info("Pygame beendet.")
                        try:
                            args = [sys.executable, MAIN_SCRIPT_PATH]
                            logger.info(f"Starte Hauptmenü neu: {args}")
                            os.execv(sys.executable, args)
                        except Exception as e:
                            logger.critical("Neustart Hauptmenü fehlgeschlagen!", exc_info=True)
                            sys.exit(1)

                elif (event.key == pygame.K_SPACE and
                        current_game_state == GAME_STATE_PLAY and
                        not platform_utils.IS_ANDROID):
                    if not interaction_active and interaction_possible_now:
                        interaction_active = True
                        interaction_press_event_handled = True
                        interaction_start_time = time.time()
                        target_name = getattr(potential_interaction_target, 'item_type', getattr(potential_interaction_target, 'npc_type', '?'))
                        logger.info(f"Start Interaktion (SPACE) mit {target_type} '{target_name}'")
                    elif interaction_active: logger.debug("SPACE Down ignoriert: Interaktion bereits aktiv.")
                    elif not interaction_possible_now: logger.debug("SPACE Down ignoriert: Kein Interaktionsziel.")

            elif event.type == pygame.KEYUP:
                 if (event.key == pygame.K_SPACE and
                      current_game_state == GAME_STATE_PLAY and
                      not platform_utils.IS_ANDROID):
                     logger.debug(f"KEYUP SPACE: active={interaction_active}, target={potential_interaction_target}, type={target_type}")

                     if interaction_active and potential_interaction_target:
                         press_duration = time.time() - interaction_start_time
                         is_short_press = press_duration < LONG_PRESS_THRESHOLD
                         logger.debug(f"KEYUP SPACE: Short press={is_short_press} (Duration: {press_duration:.2f}s)")

                         if is_short_press:
                             if target_type == "item" and potential_interaction_target in placed_items:
                                 item = potential_interaction_target

                                 # Verpackstation Interaktion (SPACE)
                                 if item.item_type == "Verpackstation":
                                     logger.info(f"Interaktion (SPACE) mit {item.item_type}. Keine Aktion definiert.")
                                     item.interact()

                                 # Blumentopf Interaktion (SPACE)
                                 elif item.item_type == "Blumentopf":
                                     logger.debug(f"Item Interaktion (SPACE) - Blumentopf. Aktueller Zustand: {item.state}")
                                     if item.state == 'ohneErde':
                                         logger.debug("Zustand 'ohneErde' (SPACE)...")
                                         req="Sack Erde"; has=inventory.has_item(req, 1); logger.debug(f"Prüfe '{req}': {has}")
                                         if has:
                                             removed=inventory.remove_item(req, 1); logger.debug(f"Entferne '{req}': {removed}")
                                             if removed:
                                                 logger.info(f"'{req}' verbraucht. Starte Minispiel1..."); save_game_state(); success=False
                                                 logger.info(f"!!! > {MINIGAME_GROW1_PATH}")
                                                 try:
                                                     result=subprocess.run([sys.executable, MINIGAME_GROW1_PATH], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', cwd=project_root_dir)
                                                     logger.info(f"Minispiel1 Ende. RC={result.returncode}."); success=(result.returncode == 0)
                                                     if not success: logger.warning(f"Minispiel1 fail (RC={result.returncode}). STDOUT:'{result.stdout.strip() if result.stdout else ''}' STDERR:'{result.stderr.strip() if result.stderr else ''}'")
                                                 except FileNotFoundError: logger.error(f"Skript fehlt: {MINIGAME_GROW1_PATH}", exc_info=True); success=False
                                                 except Exception: logger.exception("Fehler Ausführung Minispiel1:"); success=False
                                                 if success: logger.info("Minispiel1 OK -> 'ohneSeed'."); item.state='ohneSeed'; item.update_appearance()
                                                 else: logger.info("Minispiel1 nicht OK, stelle Item wieder her."); inventory.add_item(req, 1)
                                             else: logger.error(f"Konnte '{req}' nicht entfernen?")
                                         else: logger.info(f"Fehlt: '{req}'. Minispiel nicht gestartet.")

                                     elif item.state == 'ohneSeed':
                                         logger.debug("Zustand 'ohneSeed' (SPACE)...")
                                         req_seed = "Weed Seeds"; has_seed = inventory.has_item(req_seed, 1); logger.debug(f"Prüfe '{req_seed}': {has_seed}")
                                         if has_seed:
                                             removed_seed = inventory.remove_item(req_seed, 1); logger.debug(f"Entferne '{req_seed}': {removed_seed}")
                                             if removed_seed:
                                                 logger.info(f"'{req_seed}' verbraucht. Starte Minispiel2..."); save_game_state(); success=False
                                                 logger.info(f"!!! > {MINIGAME_GROW2_PATH}")
                                                 try:
                                                     result=subprocess.run([sys.executable, MINIGAME_GROW2_PATH], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', cwd=project_root_dir)
                                                     logger.info(f"Minispiel2 Ende. RC={result.returncode}."); success=(result.returncode == 0)
                                                     if not success: logger.warning(f"Minispiel2 fail (RC={result.returncode}). STDOUT:'{result.stdout.strip() if result.stdout else ''}' STDERR:'{result.stderr.strip() if result.stderr else ''}'")
                                                 except FileNotFoundError: logger.error(f"Skript fehlt: {MINIGAME_GROW2_PATH}", exc_info=True); success=False
                                                 except Exception: logger.exception("Fehler Ausführung Minispiel2:"); success=False
                                                 if success: logger.info("Minispiel2 OK -> 'giessen'."); item.state='giessen'; item.update_appearance()
                                                 else: logger.info("Minispiel2 nicht OK, stelle Item wieder her."); inventory.add_item(req_seed, 1)
                                             else: logger.error(f"Konnte '{req_seed}' nicht entfernen?")
                                         else: logger.info(f"Fehlt: '{req_seed}'. Minispiel nicht gestartet.")

                                     elif item.state == 'giessen':
                                         logger.debug(f"Zustand '{item.state}' (SPACE). Rufe item.interact() auf.")
                                         item.interact() # Startet Timer

                                     elif item.state == 'readyToEarn':
                                         logger.debug("Zustand 'readyToEarn' (SPACE)...")
                                         logger.info(f"Starte Minispiel3..."); save_game_state(); success=False; earned_amount=0
                                         logger.info(f"!!! > {MINIGAME_EARN_WEED_PATH}"); result=None
                                         try:
                                             result=subprocess.run([sys.executable, MINIGAME_EARN_WEED_PATH], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', cwd=project_root_dir)
                                             if result:
                                                 stdout_content = result.stdout.strip() if result.stdout else ""; stderr_content = result.stderr.strip() if result.stderr else ""
                                                 logger.info(f"Minispiel3 Ende. RC={result.returncode}. STDOUT:'{stdout_content}'")
                                                 if result.returncode == 0:
                                                     if stdout_content:
                                                         try: last_line = stdout_content.splitlines()[-1].strip(); earned_amount = int(last_line); logger.info(f"STDOUT gelesen: {earned_amount}"); success = True
                                                         except (ValueError, IndexError): logger.error(f"Letzte Zeile STDOUT nicht lesbar: '{stdout_content}'"); earned_amount=0; success=True
                                                         except Exception as e_parse: logger.error(f"Fehler STDOUT Parsing: {e_parse}", exc_info=True); earned_amount=0; success=False
                                                     else: logger.warning("Minispiel3 OK (RC=0), aber STDOUT war leer."); earned_amount = 0; success = True
                                                 else: logger.warning(f"Minispiel3 fail (RC={result.returncode}). STDERR:'{stderr_content}'"); success = False
                                             else: logger.error("Subprocess result war None (unerwartet)."); success = False
                                         except FileNotFoundError: logger.error(f"Skript fehlt: {MINIGAME_EARN_WEED_PATH}", exc_info=True); success=False
                                         except Exception: logger.exception("Fehler Ausführung Minispiel3:"); success=False
                                         if success:
                                             if earned_amount > 0:
                                                 logger.info(f"Minispiel3 OK! Füge {earned_amount} Weed hinzu -> 'ohneErde'.")
                                                 if inventory.add_item("Weed", earned_amount): logger.info(f"{earned_amount} Weed hinzugefügt.")
                                                 else: logger.warning("Konnte Weed nicht hinzufügen (Inventar voll?).")
                                             else: logger.info(f"Minispiel3 OK (RC=0), aber Menge={earned_amount}. Setze Zustand zurück.")
                                             item.state = 'ohneErde'; item.update_appearance()
                                         else: logger.info("Minispiel3 nicht erfolgreich. Zustand bleibt 'readyToEarn'.")

                                     elif item.state == 'growing':
                                         logger.debug(f"Zustand '{item.state}' (SPACE). Rufe item.interact() auf.")
                                         item.interact() # Loggt Zeit

                                     else: logger.warning(f"Unbehandelter Blumentopf-Zustand für kurze Interaktion (SPACE): {item.state}")

                                 else: logger.warning(f"Kurze Interaktion (SPACE) für unbekannten Item-Typ '{item.item_type}' nicht definiert.")

                             elif target_type == "npc":
                                 active_npc = potential_interaction_target
                                 logger.info(f"Interagiere mit NPC '{active_npc.npc_type}' ({id(active_npc)})")
                                 if active_npc.dialog_id:
                                     if active_npc.npc_type == "client" and not inventory.has_item("Weed", 1):
                                         current_dialog_node_id = "client_nichts_da"
                                         logger.info("Client angesprochen, aber Spieler hat kein Weed.")
                                     else: current_dialog_node_id = active_npc.dialog_id
                                     current_game_state = GAME_STATE_DIALOG
                                     logger.info(f"-> DIALOG (Start:{current_dialog_node_id})")
                                 else: logger.warning("NPC hat keine Dialog-ID."); active_npc = None

                             else: logger.debug(f"Kurze Interaktion (SPACE), aber target_type '{target_type}' oder Ziel ungültig.")

                         else: logger.debug("KEYUP SPACE: Langes Drücken erkannt, keine Aktion beim Loslassen (Pickup oben behandelt).")

                         # Interaktionsstatus nur zurücksetzen, wenn wir im Spiel bleiben
                         if current_game_state == GAME_STATE_PLAY:
                             logger.debug("KEYUP SPACE: Resetting interaction state (stayed in PLAY).")
                             potential_interaction_target = None; interaction_start_time = 0.0; interaction_active = False; target_type = None
                         else:
                             # Wenn Zustand wechselt (z.B. Dialog öffnet), Interaktion beenden, aber Ziel nicht sofort löschen
                             logger.debug("KEYUP SPACE: Interaction ended, state changed. Not resetting target.")
                             interaction_active = False; interaction_start_time = 0.0

                     else: # Wenn Interaktion nicht aktiv war oder kein Ziel da war
                         logger.debug(f"KEYUP SPACE: Interaktion nicht aktiv oder kein Ziel. active={interaction_active}, target is None: {potential_interaction_target is None}.")
                         interaction_active = False; interaction_start_time = 0.0; target_type = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                 # Android Button Klick (Start Interaktion)
                 if current_game_state == GAME_STATE_PLAY and platform_utils.IS_ANDROID and BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen):
                     if not interaction_active and interaction_possible_now:
                         interaction_active = True; interaction_press_event_handled = True; interaction_start_time = time.time()
                         target_name = getattr(potential_interaction_target,'item_type',getattr(potential_interaction_target,'npc_type','?'))
                         logger.info(f"Start Interaktion (Button) mit {target_type} '{target_name}'")
                     else: logger.debug(f"Button Klick ignoriert: active={interaction_active}, possible={interaction_possible_now}")

                 # Drag & Drop Start
                 elif current_game_state == GAME_STATE_PLAY and not is_dragging \
                      and (not platform_utils.IS_ANDROID or not (BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen))):
                     inv_list = inventory.get_item_list_for_display()
                     for i in range(MAX_SLOTS):
                         if i == MAX_SLOTS - 1: continue # Geld-Slot ignorieren
                         slot_x = CENTERED_INVENTORY_X_POS + i * (SCALED_BOX_SIZE + SCALED_PADDING)
                         slot_y = CENTERED_INVENTORY_Y_POS
                         slot_rect = pygame.Rect(slot_x, slot_y, SCALED_BOX_SIZE, SCALED_BOX_SIZE)

                         if slot_rect.collidepoint(mouse_pos_screen) and i < len(inv_list):
                             try:
                                 name_t, qty_t = inv_list[i]
                                 logger.debug(f"Slot {i} Klick: Item='{name_t}', Menge={qty_t}")
                                 # Prüfen ob das Item ziehbar ist (NUTZT MODULVARIABLE)
                                 if name_t in items.PLACEABLE_ITEMS and qty_t > 0:
                                     is_dragging = True
                                     dragged_item_type = name_t
                                     # Nutze das Icon oder das erste Zustandsbild als Vorschau
                                     dragged_item_image_try = item_icons.get(name_t) # Erst Icon versuchen
                                     if not dragged_item_image_try: # Wenn kein Icon, dann erstes Zustandsbild
                                         start_state = 'default' if name_t == "Verpackstation" else 'ohneErde'
                                         dragged_item_image_try = placed_item_images.get(name_t, {}).get(start_state)

                                     if dragged_item_image_try:
                                         dragged_item_image = dragged_item_image_try.copy() # Kopie verwenden!
                                         # Skaliere Vorschau auf die platzierte Größe, falls nötig
                                         if dragged_item_image.get_size() != (PLACED_ITEM_SIZE, PLACED_ITEM_SIZE):
                                              try:
                                                  dragged_item_image = pygame.transform.smoothscale(dragged_item_image, (PLACED_ITEM_SIZE, PLACED_ITEM_SIZE))
                                              except Exception:
                                                  logger.warning(f"Konnte Drag-Vorschau für '{name_t}' nicht auf Zielgröße skalieren.")
                                                  dragged_item_image = fallback_placed_image # Fallback, wenn Skalierung fehlschlägt
                                     else:
                                         dragged_item_image = fallback_placed_image;
                                         logger.warning(f"Kein Icon/Startbild für Drag '{name_t}' gefunden, nutze generisches Fallback-Bild.")

                                     logger.info(f"Starte Drag: {dragged_item_type}")
                                     break # Beende Schleife nach gefundenem Item
                                 else: logger.debug(f"Item '{name_t}' nicht ziehbar oder Menge 0.")
                             except Exception as e: logger.exception(f"Drag Start Error:{e}")

                 # Dialog Klick
                 elif current_game_state == GAME_STATE_DIALOG:
                     for i, rect in enumerate(dialog_response_rects):
                         if rect.collidepoint(mouse_pos_screen):
                             logger.debug(f"Dialog Antwort {i}.")
                             node = dialog.get_dialog_node(current_dialog_node_id)
                             if node and i < len(node["responses"]):
                                 response = node["responses"][i]; action = response.get("action"); next_node = response.get("next_node")
                                 if action == "open_shop": logger.info("Aktion: Shop."); current_game_state = GAME_STATE_SHOP
                                 elif action == "open_sell_menu":
                                     logger.info("Aktion: Verkaufsmenü.")
                                     if inventory.has_item("Weed", 1): current_game_state = GAME_STATE_SELL
                                     else: logger.info("Spieler hat kein Weed, zeige 'nichts_da'-Dialog."); current_dialog_node_id = "client_nichts_da"
                                 elif action == "end_dialog": logger.info("Aktion: Ende."); current_game_state = GAME_STATE_PLAY; current_dialog_node_id = None; active_npc = None
                                 elif next_node: logger.info(f"-> Dialog: {next_node}"); current_dialog_node_id = next_node
                                 elif not action: logger.info("Keine Aktion/NextNode->Ende."); current_game_state = GAME_STATE_PLAY; current_dialog_node_id = None; active_npc = None
                             break # Beende Schleife nach Klick

                 # Shop Klick
                 elif current_game_state == GAME_STATE_SHOP:
                     item_clicked = False; available = shop_items.get_available_items()
                     for i, rect in enumerate(shop_item_rects):
                         if rect.collidepoint(mouse_pos_screen):
                             item_clicked = True; logger.debug(f"Shop Slot {i}.")
                             if i < len(available):
                                 item_buy = available[i]; name = item_buy["name"]; price = item_buy["price"]
                                 logger.info(f"Kaufversuch:'{name}' ({price:.2f}). Geld: {player_money:.2f}")
                                 if player_money >= price:
                                     if inventory.add_item(name, 1): player_money -= price; logger.info(f"Gekauft! Geld neu: {player_money:.2f}")
                                     else: logger.warning("Kauf fehlgeschlagen: Inventar voll?")
                                 else: logger.warning("Kauf fehlgeschlagen: Zu wenig Geld.")
                             else: logger.error(f"Shop-Klick Fehler: Index {i} außerhalb von Angebot ({len(available)} Items).")
                             break # Beende Schleife nach Klick
                     # Klick auf Verlassen-Button prüfen, wenn kein Item geklickt wurde
                     if not item_clicked and shop_exit_button_rect and shop_exit_button_rect.collidepoint(mouse_pos_screen):
                         logger.info("Shop verlassen."); current_game_state = GAME_STATE_PLAY; active_npc = None; current_dialog_node_id = None

                 # Verkaufs-UI Klick
                 elif current_game_state == GAME_STATE_SELL:
                     # Klick auf Verkaufen-Button
                     if sell_button_rect and sell_button_rect.collidepoint(mouse_pos_screen):
                         item_to_sell = "Weed"
                         if inventory.has_item(item_to_sell, 1):
                             if inventory.remove_item(item_to_sell, 1):
                                 player_money += WEED_SELL_PRICE
                                 logger.info(f"1 {item_to_sell} verkauft für {WEED_SELL_PRICE:.2f}. Geld neu: {player_money:.2f}")
                             else: # Sollte nicht passieren, wenn has_item True war
                                 logger.error(f"Konnte {item_to_sell} nicht entfernen, obwohl has_item True war?")
                         else: logger.warning("Verkaufen-Button geklickt, aber kein Weed mehr vorhanden.")
                     # Klick auf Verlassen-Button
                     elif sell_exit_button_rect and sell_exit_button_rect.collidepoint(mouse_pos_screen):
                         logger.info("Verkaufsmenü verlassen."); current_game_state = GAME_STATE_PLAY; active_npc = None; current_dialog_node_id = None


            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                 if current_game_state == GAME_STATE_PLAY:
                     # Android Button Loslassen (Kurze Interaktion)
                     if platform_utils.IS_ANDROID and interaction_active:
                         # Nur auslösen, wenn Button losgelassen UND über Button losgelassen UND durch Button gedrückt wurde
                         if BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen) and interaction_press_event_handled:
                             logger.debug(f"MOUSEUP (Android Button): active={interaction_active}, target={potential_interaction_target}, type={target_type}")
                             if potential_interaction_target:
                                 press_duration=time.time()-interaction_start_time; is_short_press=press_duration<LONG_PRESS_THRESHOLD
                                 logger.debug(f"MOUSEUP (Android Button): Short press={is_short_press} (Duration: {press_duration:.2f}s)")
                                 if is_short_press: # Nur bei kurzem Druck Aktionen ausführen
                                     # --- Kurze Interaktionslogik (Android Button) ---
                                     if target_type=="item" and potential_interaction_target in placed_items:
                                         item = potential_interaction_target
                                         # Verpackstation Interaktion (Android Button)
                                         if item.item_type == "Verpackstation":
                                              logger.info(f"Interaktion (Button) mit {item.item_type}. Keine Aktion definiert.")
                                              item.interact()
                                         # Blumentopf Interaktion (Android Button)
                                         elif item.item_type == "Blumentopf":
                                             logger.debug(f"Item Interaktion (Button) - Blumentopf. Zustand: {item.state}")
                                             if item.state=='ohneErde':
                                                 logger.debug("Zustand 'ohneErde' (Button)..."); req="Sack Erde"; has=inventory.has_item(req,1); logger.debug(f"Prüfe '{req}': {has}")
                                                 if has:
                                                     removed=inventory.remove_item(req,1); logger.debug(f"Entferne '{req}': {removed}")
                                                     if removed:
                                                         logger.info(f"'{req}' verbraucht (A). Starte Minispiel1..."); save_game_state(); success=False; logger.info(f"!!! > {MINIGAME_GROW1_PATH}")
                                                         try:
                                                             result=subprocess.run([sys.executable,MINIGAME_GROW1_PATH],capture_output=True,text=True,check=False,encoding='utf-8',errors='ignore',cwd=project_root_dir); logger.info(f"Minispiel1(A) Ende. RC={result.returncode}."); success=(result.returncode==0);
                                                             if not success: logger.warning(f"Minispiel1(A) fail (RC={result.returncode}). STDOUT:'{result.stdout.strip() if result.stdout else ''}' STDERR:'{result.stderr.strip() if result.stderr else ''}'")
                                                         except FileNotFoundError: logger.error(f"Skript fehlt(A): {MINIGAME_GROW1_PATH}",exc_info=True); success=False;
                                                         except Exception: logger.exception("Fehler Ausführung Minispiel1(A):"); success=False
                                                         if success: logger.info("Minispiel1(A) OK -> 'ohneSeed'."); item.state='ohneSeed'; item.update_appearance()
                                                         else: logger.info("Minispiel1(A) nicht OK, stelle Item wieder her."); inventory.add_item(req, 1)
                                                     else: logger.error(f"Konnte '{req}' nicht entfernen(A)?")
                                                 else: logger.info(f"Fehlt: '{req}'(A).")
                                             elif item.state=='ohneSeed':
                                                 logger.debug("Zustand 'ohneSeed' (Button)..."); req_seed="Weed Seeds"; has_seed=inventory.has_item(req_seed,1); logger.debug(f"Prüfe '{req_seed}': {has_seed}")
                                                 if has_seed:
                                                      removed_seed=inventory.remove_item(req_seed,1); logger.debug(f"Entferne '{req_seed}': {removed_seed}")
                                                      if removed_seed:
                                                           logger.info(f"'{req_seed}' verbraucht (A). Starte Minispiel2..."); save_game_state(); success=False; logger.info(f"!!! > {MINIGAME_GROW2_PATH}")
                                                           try:
                                                               result=subprocess.run([sys.executable,MINIGAME_GROW2_PATH],capture_output=True,text=True,check=False,encoding='utf-8',errors='ignore',cwd=project_root_dir); logger.info(f"Minispiel2(A) Ende. RC={result.returncode}."); success=(result.returncode==0);
                                                               if not success: logger.warning(f"Minispiel2(A) fail (RC={result.returncode}). STDOUT:'{result.stdout.strip() if result.stdout else ''}' STDERR:'{result.stderr.strip() if result.stderr else ''}'")
                                                           except FileNotFoundError: logger.error(f"Skript fehlt(A): {MINIGAME_GROW2_PATH}",exc_info=True); success=False;
                                                           except Exception: logger.exception("Fehler Ausführung Minispiel2(A):"); success=False
                                                           if success: logger.info("Minispiel2(A) OK -> 'giessen'."); item.state='giessen'; item.update_appearance()
                                                           else: logger.info("Minispiel2(A) nicht OK, stelle Item wieder her."); inventory.add_item(req_seed, 1)
                                                      else: logger.error(f"Konnte '{req_seed}' nicht entfernen(A)?")
                                                 else: logger.info(f"Fehlt: '{req_seed}'(A).")
                                             elif item.state == 'giessen': logger.debug(f"Zustand '{item.state}' (Button). Rufe item.interact() auf."); item.interact()
                                             elif item.state == 'readyToEarn':
                                                 logger.debug("Zustand 'readyToEarn' (Button)..."); logger.info(f"Starte Minispiel3(A)..."); save_game_state(); success=False; earned_amount=0; logger.info(f"!!! > {MINIGAME_EARN_WEED_PATH}"); result=None
                                                 try:
                                                     result=subprocess.run([sys.executable,MINIGAME_EARN_WEED_PATH],capture_output=True,text=True,check=False,encoding='utf-8',errors='ignore',cwd=project_root_dir)
                                                     if result:
                                                         stdout_content=result.stdout.strip() if result.stdout else ""; stderr_content=result.stderr.strip() if result.stderr else ""; logger.info(f"Minispiel3(A) Ende. RC={result.returncode}. STDOUT:'{stdout_content}'")
                                                         if result.returncode==0:
                                                             if stdout_content:
                                                                 try: last_line=stdout_content.splitlines()[-1].strip(); earned_amount=int(last_line); logger.info(f"STDOUT(A) gelesen: {earned_amount}"); success=True
                                                                 except(ValueError,IndexError): logger.error(f"Letzte Zeile STDOUT(A) nicht lesbar: '{stdout_content}'"); earned_amount=0; success=True
                                                                 except Exception as e_parse: logger.error(f"Fehler STDOUT(A) Parsing: {e_parse}",exc_info=True); earned_amount=0; success=False
                                                             else: logger.warning("Minispiel3(A) OK (RC=0), aber STDOUT leer."); earned_amount=0; success=True
                                                         else: logger.warning(f"Minispiel3(A) fail (RC={result.returncode}). STDERR:'{stderr_content}'"); success=False
                                                     else: logger.error("Subprocess result(A) war None"); success=False
                                                 except FileNotFoundError: logger.error(f"Skript fehlt(A): {MINIGAME_EARN_WEED_PATH}",exc_info=True); success=False;
                                                 except Exception: logger.exception("Fehler Ausführung Minispiel3(A):"); success=False
                                                 if success:
                                                     if earned_amount>0:
                                                         logger.info(f"Minispiel3(A) OK! Füge {earned_amount} Weed hinzu -> 'ohneErde'.");
                                                         if inventory.add_item("Weed",earned_amount): logger.info(f"{earned_amount} Weed hinzugefügt(A).")
                                                         else: logger.warning("Konnte Weed nicht hinzufügen(A) (Inventar voll?).")
                                                     else: logger.info(f"Minispiel3(A) OK (RC=0), aber Menge={earned_amount}. Setze Zustand zurück.")
                                                     item.state='ohneErde'; item.update_appearance()
                                                 else: logger.info("Minispiel3(A) nicht erfolgreich. Zustand bleibt 'readyToEarn'.")
                                             elif item.state == 'growing': logger.debug(f"Zustand '{item.state}' (Button). Rufe item.interact() auf."); item.interact()
                                             else: logger.warning(f"Unbehandelter Blumentopf-Zustand (Button): {item.state}")
                                         else: logger.warning(f"Kurze Interaktion (Button) für unbekannten Item-Typ '{item.item_type}' nicht definiert.")
                                     elif target_type=="npc":
                                         active_npc=potential_interaction_target; logger.info(f"Interagiere mit NPC '{active_npc.npc_type}' ({id(active_npc)})")
                                         if active_npc.dialog_id:
                                             if active_npc.npc_type == "client" and not inventory.has_item("Weed", 1):
                                                 current_dialog_node_id = "client_nichts_da"; logger.info("Client angesprochen (A), aber Spieler hat kein Weed.")
                                             else: current_dialog_node_id=active_npc.dialog_id
                                             current_game_state=GAME_STATE_DIALOG; logger.info(f"-> DIALOG (Start:{current_dialog_node_id})")
                                         else: logger.warning("NPC hat keine Dialog-ID."); active_npc=None
                                     else: logger.debug(f"Kurze Interaktion (Button), aber target_type '{target_type}' oder Ziel ungültig.")
                                 # Kein 'else' hier, da langes Drücken in der Update-Schleife behandelt wird
                             else: logger.debug("MOUSEUP (Android Button): target war None.")

                             # Interaktion beenden, egal ob kurz oder lang, wenn Zustand wechselt oder nicht
                             if current_game_state == GAME_STATE_PLAY:
                                 logger.debug("MOUSEUP (Android Button): Resetting interaction state (stayed in PLAY)."); potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False; target_type=None
                             else:
                                 logger.debug("MOUSEUP (Android Button): Interaction ended, state changed. Not resetting target.")
                                 interaction_active = False; interaction_start_time = 0.0
                         else: # Loslassen nicht über Button oder Interaktion nicht durch Button gestartet
                              logger.debug("MOUSEUP (Android): Nicht über Button losgelassen oder nicht durch Button-Presse gestartet.")
                              if interaction_active: interaction_active = False; interaction_start_time = 0.0

                     # Drag & Drop Ende
                     elif is_dragging:
                         inv_rect_check = pygame.Rect(CENTERED_INVENTORY_X_POS, CENTERED_INVENTORY_Y_POS, MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING, SCALED_BOX_SIZE)
                         button_collide_check = platform_utils.IS_ANDROID and BUTTON_RECT and BUTTON_RECT.collidepoint(mouse_pos_screen)

                         # Nur platzieren, wenn NICHT über Inventar oder Button losgelassen wird
                         if not inv_rect_check.collidepoint(mouse_pos_screen) and not button_collide_check:
                             world_x, world_y = camera.screen_to_world(mouse_pos_screen[0], mouse_pos_screen[1])
                             # Snapping auf das Raster
                             snapped_tl_x = (world_x // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                             snapped_tl_y = (world_y // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                             snapped_center_x = snapped_tl_x + PLACED_ITEM_SIZE / 2
                             snapped_center_y = snapped_tl_y + PLACED_ITEM_SIZE / 2

                             # Prüfen, ob die Zielposition bereits belegt ist
                             can_place = True
                             temp_rect = pygame.Rect(snapped_tl_x, snapped_tl_y, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)
                             for item in placed_items:
                                 if temp_rect.colliderect(item.rect):
                                     can_place = False; logger.info(f"Platzieren bei ({snapped_tl_x},{snapped_tl_y}) blockiert durch {item.item_type} @ {item.rect.topleft}."); break

                             if can_place:
                                 logger.info(f"Versuche '{dragged_item_type}' bei Welt ({snapped_center_x:.0f},{snapped_center_y:.0f}) zu platzieren.")
                                 # Versuche, Item aus Inventar zu entfernen
                                 if inventory.remove_item(dragged_item_type, 1):
                                     # Hole benötigte Infos für das neue Item
                                     images = placed_item_images.get(dragged_item_type, {})
                                     fallback = fallback_placed_image
                                     start_state = 'default' if dragged_item_type == "Verpackstation" else 'ohneErde'
                                     grow_time = GROW_TIME_SECONDS if dragged_item_type == "Blumentopf" else 0

                                     # === KORRIGIERTE LOGIK START ===
                                     new_item = None # Sicherstellen, dass new_item definiert ist
                                     try:
                                         # 1. Erstelle das Item-Objekt
                                         new_item = items.PlacedItem(snapped_center_x, snapped_center_y, dragged_item_type, images, fallback, grow_time, start_state, None)

                                         # 2. Prüfe nur auf Konstruktor-Fehler (z.B. wenn Rect am Ende None ist)
                                         if not new_item or not hasattr(new_item, 'rect') or not new_item.rect:
                                              # Der verbesserte Konstruktor sollte das verhindern, aber sicher ist sicher
                                              raise ValueError(f"PlacedItem Konstruktor fehlgeschlagen oder kein Rect für {dragged_item_type}.")

                                         # 3. Füge das Item ZUERST zu den Gruppen hinzu
                                         all_sprites.add(new_item)
                                         placed_items.add(new_item)
                                         # Jetzt ist new_item.alive() True!
                                         logger.info(f"'{dragged_item_type}' erfolgreich platziert und zu Gruppen hinzugefügt (Alive: {new_item.alive()}).")

                                     except Exception as e_create_add:
                                         # Fehler beim Erstellen ODER Hinzufügen (oder der manuellen Prüfung)
                                         logger.exception(f"FEHLER beim Erstellen oder Hinzufügen von PlacedItem '{dragged_item_type}':")
                                         # Stelle Item im Inventar wieder her
                                         inventory.add_item(dragged_item_type, 1)
                                         # Entferne das fehlerhafte Item aus Gruppen, falls es doch kurz hinzugefügt wurde
                                         # (Sollte nicht passieren, wenn add() nach der Prüfung kommt, aber sicherheitshalber)
                                         if new_item and new_item.alive(): # Prüfe ob es doch hinzugefügt wurde
                                             new_item.kill()
                                             logger.warning(f"Fehlerhaftes '{dragged_item_type}' wieder aus Gruppen entfernt.")
                                     # === KORRIGIERTE LOGIK ENDE ===

                                 else: # Falls inventory.remove_item fehlschlägt
                                     logger.warning(f"Platzieren fehlgeschlagen (Konnte '{dragged_item_type}' nicht aus Inventar entfernen?)")
                             else:
                                 logger.info("Platzieren nicht möglich (Position blockiert).")
                         else:
                             logger.info("Drag beendet über UI (Inventar/Button) - Item nicht platziert.")

                         # Drag-Status IMMER zurücksetzen
                         is_dragging = False; dragged_item_type = None; dragged_item_image = None; logger.debug("Drag beendet.")


        # === ZEICHNEN ===
        # Hintergrund (falls vorhanden, sonst schwarz)
        if current_game_state == GAME_STATE_PLAY:
             if background_image: screen.blit(background_image, (0,0))
             else: screen.fill(BLACK)
        else:
            # Dunkler Overlay für Menüs etc. (Hintergrund sichtbar lassen)
            if background_image: screen.blit(background_image, (0,0))
            else: screen.fill(BLACK)
            dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 150)); screen.blit(dark_overlay, (0, 0))

        # --- Zeichnen im Spielzustand ---
        if current_game_state == GAME_STATE_PLAY:
            # Alle Sprites zeichnen, die im Kamerabereich sind
            for sprite in all_sprites:
                try:
                    # Prüfen ob Sprite Bild und Rect hat UND sichtbar ist
                    if hasattr(sprite,'image') and sprite.image and hasattr(sprite,'rect') and sprite.rect and camera.get_current_screen_rect().colliderect(sprite.rect):
                        screen_pos = camera.apply(sprite); screen.blit(sprite.image, screen_pos)
                    # Optional: Loggen, wenn ein Sprite kein Bild/Rect hat
                    # elif not (hasattr(sprite, 'image') and sprite.image and hasattr(sprite, 'rect') and sprite.rect):
                    #      logger.warning(f"Sprite {sprite} hat kein gültiges Bild/Rect zum Zeichnen.")
                except AttributeError as e_attr: logger.warning(f"Fehler Zeichnen(Attr {e_attr}): {sprite}")
                except Exception as e_draw: logger.exception(f"Fehler Zeichnen(Allg): {sprite} -> {e_draw}")

            # Interaktionsanzeige (Kreis, Fortschrittsbalken)
            if interaction_active and potential_interaction_target:
                try:
                    p_rect_s = camera.apply_rect(player.rect); c_s = p_rect_s.center;
                    pygame.draw.circle(screen, WHITE, c_s, int(INTERACTION_RADIUS), 1)
                    # Fortschrittsbalken für langes Drücken (Aufheben)
                    if interaction_start_time > 0 and target_type == "item":
                        hold_dur = time.time() - interaction_start_time
                        if hold_dur < LONG_PRESS_THRESHOLD:
                            prog = min(1.0, hold_dur / LONG_PRESS_THRESHOLD)
                            if prog > 0:
                                bar_w=50; bar_h=5; bar_x=c_s[0]-bar_w//2; bar_y=p_rect_s.top-bar_h-5
                                pygame.draw.rect(screen, (50,50,50), (bar_x, bar_y, bar_w, bar_h))
                                pygame.draw.rect(screen, RED, (bar_x, bar_y, int(bar_w * prog), bar_h))
                except Exception: logger.exception("Zeichenfehler Interaktion:")

            # UI-Texte (FPS, Ziel)
            try:
                if ui_font:
                    fps_text = f"FPS: {clock.get_fps():.1f}"; surf_fps = ui_font.render(fps_text, True, WHITE); screen.blit(surf_fps, (10, 10))
                    target_txt = "Target: None"
                    # Nur anzeigen, wenn keine Interaktion läuft (verhindert Flackern)
                    if not interaction_active and potential_interaction_target:
                        target_state = getattr(potential_interaction_target, 'state', 'N/A'); target_id = getattr(potential_interaction_target, 'item_type', getattr(potential_interaction_target, 'npc_type', '?'))
                        target_txt = f"Target: {target_type} ({target_id})"
                        if target_type == 'item': target_txt += f" / State: {target_state}"
                    surf_target=ui_font.render(target_txt, True, YELLOW); screen.blit(surf_target, (10, 35))
            except Exception: logger.exception("Zeichenfehler UI-Text:")

            # Inventar zeichnen
            try:
                inv_list = inventory.get_item_list_for_display()
                for i in range(MAX_SLOTS):
                    slot_x = CENTERED_INVENTORY_X_POS + i * (SCALED_BOX_SIZE + SCALED_PADDING); slot_y = CENTERED_INVENTORY_Y_POS
                    slot_rect = pygame.Rect(slot_x, slot_y, SCALED_BOX_SIZE, SCALED_BOX_SIZE)
                    # Geld-Slot (letzter Slot)
                    if i == MAX_SLOTS - 1:
                        if money_slot_background_img: screen.blit(money_slot_background_img, slot_rect.topleft)
                        else: pygame.draw.rect(screen, (100, 100, 100, 180), slot_rect) # Leicht transparentes Grau
                        pygame.draw.rect(screen, WHITE, slot_rect, 2) # Rahmen
                        if inventory_font:
                            try: money_txt = locale.currency(player_money, grouping=True) if LOCALE_SET else f"{player_money:.2f} $"
                            except: money_txt = f"{player_money:.2f}"
                            m_surf = inventory_font.render(money_txt, True, GREEN); m_rect = m_surf.get_rect(center = slot_rect.center); screen.blit(m_surf, m_rect)
                    # Normale Item-Slots
                    elif i < len(inv_list):
                        pygame.draw.rect(screen, (100, 100, 100, 180), slot_rect); pygame.draw.rect(screen, WHITE, slot_rect, 2)
                        name, qty = inv_list[i]; icon_surf = item_icons.get(name)
                        # Icon zeichnen oder Fallback-Text
                        if icon_surf: i_rect = icon_surf.get_rect(center=slot_rect.center); screen.blit(icon_surf, i_rect)
                        else:
                            if inventory_font: fb_surf = inventory_font.render(name[:5]+"..", True, WHITE); fb_rect = fb_surf.get_rect(center=slot_rect.center); screen.blit(fb_surf, fb_rect)
                        # Menge zeichnen (rechts unten)
                        if qty > 0 and inventory_font:
                            q_surf = inventory_font.render(str(qty), True, WHITE); q_rect = q_surf.get_rect(bottomright = (slot_rect.right - SCALED_PADDING // 2, slot_rect.bottom - SCALED_PADDING // 2)); screen.blit(q_surf, q_rect)
                    # Leere Slots
                    else: pygame.draw.rect(screen, (100, 100, 100, 180), slot_rect); pygame.draw.rect(screen, WHITE, slot_rect, 2)
            except Exception: logger.exception("Fehler Inventar-Anzeige:")

            # Drag-Vorschau zeichnen (semi-transparent am Mauszeiger/Raster)
            if is_dragging and dragged_item_image:
                # Weltkoordinaten -> Gerasterte Weltkoordinaten -> Gerasterte Bildschirmkoordinaten
                world_x, world_y = camera.screen_to_world(*mouse_pos_screen); snapped_tl_x = (world_x // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE; snapped_tl_y = (world_y // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                temp_rect_w = pygame.Rect(snapped_tl_x, snapped_tl_y, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE); snapped_rect_s = camera.apply_rect(temp_rect_w)
                try:
                    # Bild leicht transparent machen und zeichnen
                    dragged_item_image.set_alpha(180)
                    # Zentriert im Rasterfeld zeichnen
                    drag_rect = dragged_item_image.get_rect(center=snapped_rect_s.center)
                    screen.blit(dragged_item_image, drag_rect)
                    dragged_item_image.set_alpha(255) # Alpha zurücksetzen für nächsten Frame/Inventar
                    # Raster hervorheben
                    pygame.draw.rect(screen, WHITE, snapped_rect_s, 1)
                except Exception as e: logger.error(f"Fehler beim Zeichnen der Drag-Vorschau: {e}", exc_info=False)

            # Android Interaktions-Button zeichnen
            if platform_utils.IS_ANDROID:
                if BUTTON_RECT:
                    if button_image_normal: screen.blit(button_image_normal, BUTTON_RECT.topleft)
                    else: # Fallback: Rechteck + Text
                        pygame.draw.rect(screen, BUTTON_COLOR_NORMAL, BUTTON_RECT); pygame.draw.rect(screen, BUTTON_BORDER_COLOR, BUTTON_RECT, 2)
                        if button_font:
                            try: btn_surf = button_font.render("Interact", True, WHITE); btn_rect = btn_surf.get_rect(center=BUTTON_RECT.center); screen.blit(btn_surf, btn_rect)
                            except Exception as e: logger.error(f"Fehler Button-Text:{e}", exc_info=True)
                else: logger.warning("BUTTON_RECT nicht initialisiert, Button wird nicht gezeichnet.")

        # --- Zeichnen im Dialogzustand ---
        elif current_game_state == GAME_STATE_DIALOG:
            dialog_response_rects.clear(); node = dialog.get_dialog_node(current_dialog_node_id)
            if node and dialog_font:
                dlg_h = SCREEN_HEIGHT // 3; dlg_y = SCREEN_HEIGHT - dlg_h; dlg_rect = pygame.Rect(0, dlg_y, SCREEN_WIDTH, dlg_h)
                pygame.draw.rect(screen, DARK_BLUE, dlg_rect); pygame.draw.rect(screen, WHITE, dlg_rect, 3)
                # NPC Text (mit Umbruch)
                npc_txt_rect = pygame.Rect(dlg_rect.left + 20, dlg_rect.top + 20, dlg_rect.width - 40, dlg_rect.height // 2 - 30)
                wrap_text(screen, node["npc_text"], dialog_font, WHITE, npc_txt_rect)
                # Antwortmöglichkeiten (Buttons)
                resp_y = npc_txt_rect.bottom + 15; resp_h = 35; resp_sp = 10; btn_w = dlg_rect.width // 2 - 30
                for i, response in enumerate(node["responses"]):
                    btn_x = dlg_rect.left + 20; btn_y = resp_y + i * (resp_h + resp_sp)
                    if btn_y + resp_h > dlg_rect.bottom - 10: break # Passt nicht mehr
                    resp_rect = pygame.Rect(btn_x, btn_y, btn_w, resp_h); dialog_response_rects.append(resp_rect)
                    # Hover-Effekt
                    hover = resp_rect.collidepoint(mouse_pos_screen); btn_col = LIGHT_GREY if hover else GREY
                    pygame.draw.rect(screen, btn_col, resp_rect); pygame.draw.rect(screen, WHITE, resp_rect, 1)
                    # Text auf Button
                    resp_surf = dialog_font.render(response["text"], True, BLACK); resp_rect_txt = resp_surf.get_rect(center=resp_rect.center); screen.blit(resp_surf, resp_rect_txt)
            else:
                # Fallback, falls Dialogknoten ungültig ist
                logger.error(f"Dialog-Knoten '{current_dialog_node_id}' nicht gefunden/geladen."); current_game_state = GAME_STATE_PLAY; active_npc = None; current_dialog_node_id = None

        # --- Zeichnen im Shopzustand ---
        elif current_game_state == GAME_STATE_SHOP:
            shop_item_rects.clear(); margin = 50; shop_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)
            pygame.draw.rect(screen, DARK_BLUE, shop_rect); pygame.draw.rect(screen, WHITE, shop_rect, 3)
            # Titel
            if ui_font: title_surf=ui_font.render("Shop",True,YELLOW); title_rect=title_surf.get_rect(centerx=shop_rect.centerx,top=shop_rect.top+15); screen.blit(title_surf,title_rect)
            # Geldanzeige
            if inventory_font:
                try: money_txt_shop=locale.currency(player_money,grouping=True) if LOCALE_SET else f"{player_money:.2f} $"
                except: money_txt_shop=f"{player_money:.2f}"
                m_surf_s=inventory_font.render(f"Geld: {money_txt_shop}",True,GREEN); m_rect_s=m_surf_s.get_rect(right=shop_rect.right-20,top=shop_rect.top+20); screen.blit(m_surf_s,m_rect_s)
            # Item-Grid
            cols=4; rows=8; shop_list=shop_items.get_available_items()
            grid_x=shop_rect.left+30; grid_y=shop_rect.top+70; cell_w=(shop_rect.width-60)//cols; cell_h=(shop_rect.height-120)//rows; icon_size=min(cell_w//2,cell_h//2) # Dynamische Icongröße
            for i,item_data in enumerate(shop_list):
                if i>=cols*rows: break # Mehr Items als Zellen
                row=i//cols; col=i%cols; cell_x=grid_x+col*cell_w; cell_y=grid_y+row*cell_h
                cell_rect=pygame.Rect(cell_x,cell_y,cell_w-10,cell_h-10); shop_item_rects.append(cell_rect)
                # Hover-Effekt
                hover=cell_rect.collidepoint(mouse_pos_screen); cell_col=LIGHT_GREY if hover else GREY
                pygame.draw.rect(screen,cell_col,cell_rect); pygame.draw.rect(screen,WHITE,cell_rect,1)
                # Item-Icon oder Name
                name=item_data["name"]; icon_surf_shop = item_icons.get(name)
                if icon_surf_shop:
                    # Icon skalieren, falls nötig (um in Zelle zu passen)
                    shop_icon_scaled = icon_surf_shop
                    if icon_surf_shop.get_size() != (icon_size, icon_size):
                        try: shop_icon_scaled = pygame.transform.smoothscale(icon_surf_shop, (icon_size, icon_size))
                        except: pass # Ignoriere Fehler bei Skalierung
                    i_rect=shop_icon_scaled.get_rect(centerx=cell_rect.centerx,top=cell_rect.top+5); screen.blit(shop_icon_scaled,i_rect)
                elif shop_font: # Fallback: Name anzeigen
                    name_surf = shop_font.render(name, True, WHITE); name_rect = name_surf.get_rect(centerx=cell_rect.centerx, top=cell_rect.top+5); screen.blit(name_surf, name_rect)
                # Preis anzeigen
                if shop_font:
                    try: price_txt=locale.currency(item_data["price"],grouping=True) if LOCALE_SET else f"{item_data['price']:.2f} $"
                    except: price_txt=f"{item_data['price']:.2f}"
                    p_surf=shop_font.render(price_txt,True,YELLOW); p_rect=p_surf.get_rect(centerx=cell_rect.centerx,bottom=cell_rect.bottom-5); screen.blit(p_surf,p_rect)
            # Verlassen-Button
            exit_w=100; exit_h=40; exit_x=shop_rect.centerx-exit_w//2; exit_y=shop_rect.bottom-exit_h-15
            shop_exit_button_rect=pygame.Rect(exit_x,exit_y,exit_w,exit_h); hover=shop_exit_button_rect.collidepoint(mouse_pos_screen); exit_col=RED if hover else DARK_BLUE
            pygame.draw.rect(screen,exit_col,shop_exit_button_rect); pygame.draw.rect(screen,WHITE,shop_exit_button_rect,2)
            if button_font: exit_surf=button_font.render("Verlassen",True,WHITE); exit_rect=exit_surf.get_rect(center=shop_exit_button_rect.center); screen.blit(exit_surf,exit_rect)

        # --- Zeichnen im Verkaufszustand ---
        elif current_game_state == GAME_STATE_SELL:
             draw_sell_ui()

        # Bildschirm aktualisieren
        pygame.display.flip()

    except Exception as e_game_loop:
        logger.critical("Unerwarteter Fehler in Spielschleife:", exc_info=True)
        try: save_game_state()
        except Exception as e_save_on_crash: logger.error("Konnte Spielstand nach Crash nicht speichern.", exc_info=True)
        running = False

# ========= SPIEL BEENDEN =========
logger.info("Spiel-Loop beendet.")
# Nur speichern, wenn der Loop normal beendet wurde (nicht durch Crash)
if running:
    save_game_state()
else:
    logger.warning("Spiel wurde aufgrund eines Fehlers beendet, Spielstand wurde evtl. nicht korrekt gespeichert.")

# Pygame sauber beenden
if pygame.get_init():
    pygame.quit();
    logger.info("Pygame beendet.")
else:
    logger.info("Pygame war bereits beendet.")
sys.exit()