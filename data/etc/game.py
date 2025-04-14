# game.py (Finale Version mit allen Features und Fixes)
import pygame
import sys
import logging
import os
import math
import time
import traceback
import locale

# Optional: Locale für Währungsformat
try:
    # Versuche Deutsch für Euro-Symbol (€)
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
except locale.Error:
    try:
        # Fallback für Windows
        locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
    except locale.Error:
        # Fallback auf System-Standard, wenn Deutsch nicht geht
        print("WARNUNG: Locale 'de_DE' nicht verfügbar. Währung wird evtl. nicht korrekt formatiert.")

# --- Logging Konfiguration ---
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
log_level = logging.DEBUG
date_fmt = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=log_level, format=log_format, datefmt=date_fmt, force=True) # force=True überschreibt evtl. Root-Logger Config
logger = logging.getLogger(__name__)

# --- Pfade ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.path.abspath(".")
project_root_dir = os.path.normpath(os.path.join(script_dir, "..", ".."))
data_dir_root = os.path.join(project_root_dir, "data")
log_dir = os.path.join(data_dir_root, "logs")
IMAGE_FOLDER = os.path.join(data_dir_root, "bilder")
SAVE_DATA_DIR_ABS = os.path.join(data_dir_root, "savedata")
SETTINGS_DIR = os.path.join(data_dir_root, "settings")
SETTINGS_FILE_PATH = os.path.join(SETTINGS_DIR, "settings.json")
MAIN_SCRIPT_PATH = os.path.join(project_root_dir, "main.py")

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
    logging.getLogger().addHandler(file_handler) # Füge Handler zum Root-Logger hinzu
    logger.info(f"File logging initialisiert: {log_file_path}")
except Exception as e_log_setup:
    logger.error(f"Fehler File Logging: {e_log_setup}", exc_info=True)

logger.info("Spiel wird initialisiert...")
logger.debug(f"Game Script Verzeichnis: {script_dir}")

# --- Eigene Module importieren ---
try:
    import platform_utils
    from player import Player
    from npc import NPC
    from camera import Camera
    from inventory import Inventory, BOX_SIZE, PADDING, MAX_SLOTS
    from persistence import load_data, save_data
    import settings_utils
    import items          # Enthält PlacedItem und Asset Loading
    import dialog         # Enthält Dialogstruktur
    import shop_items     # Enthält Shopangebot
    logger.info("Eigene Module importiert.")
except ImportError as e:
    logger.critical(f"Fehler Import Modul: {e}.", exc_info=True); sys.exit()
except Exception as e:
    logger.critical(f"Unerwarteter Import-Fehler: {e}", exc_info=True); sys.exit()

# --- Einstellungen laden ---
try:
    current_settings = settings_utils.load_settings(SETTINGS_FILE_PATH)
    logger.info(f"Einstellungen geladen: {current_settings}")
except Exception:
    logger.exception("FEHLER beim Laden der Einstellungen:")
    current_settings = {'music_volume': 0.5, 'sfx_volume': 0.5, 'master_volume': 0.5}
    logger.warning(f"Fallback-Einstellungen: {current_settings}")

# --- Konstanten ---
TILE_SIZE = 32
FPS = 60
# Farben
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREEN = (0, 200, 0)
RED = (255, 0, 0); BLUE = (0, 0, 255); MAGENTA = (255, 0, 255)
GREY = (100, 100, 100); LIGHT_GREY = (180, 180, 180); DARK_BLUE = (0, 0, 100)
YELLOW = (255, 255, 0)
# Spielmechanik
PLACED_ITEM_SIZE = TILE_SIZE
INTERACTION_RADIUS = TILE_SIZE * 1.5 # Etwas größer für leichtere Interaktion
LONG_PRESS_THRESHOLD = 1.0
GROW_TIME_SECONDS = 10 # Zum Testen kurz
# Inventar-Skalierung
INVENTORY_SCALE_FACTOR = 2.0
SCALED_BOX_SIZE = int(BOX_SIZE * INVENTORY_SCALE_FACTOR)
SCALED_PADDING = int(PADDING * INVENTORY_SCALE_FACTOR)
# Berechne Icon-Größe, stelle sicher, dass sie nicht <= 0 ist
SCALED_ICON_W = max(1, SCALED_BOX_SIZE - SCALED_PADDING * 2)
SCALED_ICON_H = max(1, SCALED_BOX_SIZE - SCALED_PADDING * 2)
SCALED_ICON_SIZE = (SCALED_ICON_W, SCALED_ICON_H)
logger.debug(f"SCALED_ICON_SIZE: {SCALED_ICON_SIZE}")
INVENTORY_BOTTOM_PADDING = 20
# Button (Interaktion)
BUTTON_DEFAULT_WIDTH_PERCENT = 0.08
BUTTON_DEFAULT_HEIGHT_PERCENT = 0.13
BUTTON_PADDING = 15
BUTTON_X = BUTTON_PADDING
BUTTON_COLOR_NORMAL = (80, 80, 80)
BUTTON_BORDER_COLOR = WHITE
# Fonts (Basisgrößen)
FONT_SIZE_REF_H = 600.0 # Referenzhöhe für Skalierung
BASE_UI_FONT_SIZE = 28
BASE_BUTTON_FONT_SIZE = 18
BASE_INV_QTY_FONT_SIZE = 16
BASE_DIALOG_FONT_SIZE = 24
BASE_SHOP_FONT_SIZE = 18

# --- Asset-Dateinamen ---
BACKGROUND_FILENAME = "background.png"
BUTTON_FILENAME = "interact_button.png"
MONEY_ICON_FILENAME = "money_icon.png" # Für Geld-Slot Hintergrund
# Speicherdateien
INVENTORY_FILENAME="inventar.json"
INVENTORY_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, INVENTORY_FILENAME)
PLAYER_POS_FILENAME="player_position.json"
PLAYER_POS_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, PLAYER_POS_FILENAME)
PLACED_ITEMS_FILENAME="placed_items.json"
PLACED_ITEMS_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, PLACED_ITEMS_FILENAME)

# --- Asset Ladefunktion ---
def load_image_asset(filename, alpha=True, scale_to=None):
    """Lädt ein Bild und skaliert es optional."""
    if not filename: # Fange leere Dateinamen ab
        logger.warning("load_image_asset erhielt leeren Dateinamen.")
        return None
    path = os.path.join(IMAGE_FOLDER, filename)
    try:
        image = pygame.image.load(path)
        image = image.convert_alpha() if alpha else image.convert()
    except pygame.error as e_load: # Spezifischerer Fehler für Pygame
        logger.error(f"Pygame Fehler Laden Bild '{path}': {e_load}")
        return None
    except Exception as e_load_other: # Andere Fehler (z.B. FileNotFound)
        logger.error(f"Allg. Fehler Laden Bild '{path}': {e_load_other}", exc_info=True)
        return None

    if scale_to:
        if not isinstance(scale_to, (tuple, list)) or len(scale_to) != 2:
             logger.error(f"Ungültiges scale_to Format für '{filename}': {scale_to}")
        elif scale_to[0] <= 0 or scale_to[1] <= 0:
            logger.error(f"Ungültige Skalierungsgröße für '{filename}': {scale_to}.")
        else:
            try:
                # smoothscale für bessere Qualität bei Vergrößerung/Verkleinerung
                image = pygame.transform.smoothscale(image, scale_to)
            except Exception as e_scale:
                logger.error(f"Fehler Skalieren '{filename}' zu {scale_to}: {e_scale}", exc_info=True)
                # Gebe hier das unskalierte Bild zurück, besser als None
    return image

# --- Globale Variablen (Initialisierung im Hauptblock) ---
screen = None; clock = None; ui_font = None; button_font = None; inventory_font = None
dialog_font = None; shop_font = None
background_image = None; button_image_normal = None; money_slot_background_img = None
item_icons = {}; placed_item_images = {}; fallback_placed_image = None
player = None; camera = None; inventory = None; all_sprites = None; npcs = None
placed_items = None
CENTERED_INVENTORY_X_POS = 0; CENTERED_INVENTORY_Y_POS = 0; BUTTON_RECT = None
player_money = 0.0
GAME_STATE_PLAY = "play"; GAME_STATE_DIALOG = "dialog"; GAME_STATE_SHOP = "shop"
current_game_state = GAME_STATE_PLAY
active_npc = None; current_dialog_node_id = None; dialog_response_rects = []
shop_item_rects = []; shop_exit_button_rect = None
is_dragging = False; dragged_item_type = None; dragged_item_image = None
interaction_active = False; interaction_start_time = 0.0
potential_interaction_target = None; target_type = None

# --- Speicherfunktion ---
def save_game_state():
    """Speichert alle relevanten Spieldaten."""
    logger.info("Speichere Spielstand...")
    # Inventar
    try:
        if inventory: logger.info("Speichere Inventar..."); inventory.save_inventory()
        else: logger.warning("Inventar nicht initialisiert.")
    except Exception as e: logger.error("Fehler Inv speichern:", exc_info=True)
    # Spielerdaten
    try:
        if player:
            logger.info("Speichere Spielerposition & Geld...")
            player_data = {'x': player.rect.x, 'y': player.rect.y, 'money': player_money}
            save_data(player_data, PLAYER_POS_SAVE_FILE)
        else: logger.warning("Spieler nicht initialisiert.")
    except Exception as e: logger.error("Fehler Pos/Geld speichern:", exc_info=True)
    # Platzierte Items
    try:
        if placed_items is not None:
             logger.info("Speichere platzierte Items...");
             items_to_save = [{'type': item.item_type, 'x': item.rect.centerx,
                               'y': item.rect.centery, 'state': item.state,
                               'timer_end': item.timer_end_timestamp}
                              for item in placed_items]
             save_data(items_to_save, PLACED_ITEMS_SAVE_FILE)
             logger.info(f"{len(items_to_save)} Items gespeichert.")
        else: logger.warning("Placed_items Gruppe nicht initialisiert.")
    except Exception as e: logger.error("Fehler Items speichern:", exc_info=True)

# --- Hilfsfunktion für Textumbruch ---
def wrap_text(surface, text, font, color, rect, aa=True):
    """Zeichnet Text mit Zeilenumbruch innerhalb eines Rechtecks."""
    y = rect.top
    line_spacing = -2 # Kleiner negativer Wert rückt Zeilen etwas zusammen
    words = text.split(' ')

    while words:
        line_words = []
        # Prüfe, ob Font verfügbar ist, bevor get_height aufgerufen wird
        if not font: logger.error("wrap_text: Font ist None!"); return
        fh = font.get_height()

        # Füge Worte hinzu, bis Zeile voll ist
        while words:
            line_words.append(words.pop(0))
            # Prüfe Breite der aktuellen Zeile + nächstes Wort (falls vorhanden)
            next_word_preview = words[:1]
            try:
                fw, _ = font.size(' '.join(line_words + next_word_preview))
            except pygame.error as e_size:
                logger.error(f"Pygame Fehler bei font.size(): {e_size}"); break # Abbruch für diese Zeile
            if fw > rect.width:
                break

        # Wenn Zeile zu lang wurde, letztes Wort zurück (außer es ist das einzige)
        if len(line_words) > 1 and fw > rect.width:
            words.insert(0, line_words.pop())

        # Zeile zeichnen
        line = ' '.join(line_words)
        if line: # Nur nicht-leere Zeilen rendern
            try:
                img = font.render(line, aa, color)
                surface.blit(img, (rect.left, y))
                y += fh + line_spacing
            except pygame.error as e_render:
                logger.error(f"Pygame Fehler bei font.render(): {e_render}"); break # Abbruch

        # Prüfen, ob Text noch ins Rect passt
        if y > rect.bottom - fh:
            if words: # Nur warnen, wenn noch Text übrig ist
                 logger.warning("Textumbruch: Text passt nicht vollständig ins Rechteck.")
            break

# --- Haupt-Initialisierungsblock ---
try:
    pygame.init()
    try:
        pygame.mixer.init()
        logger.info("Pygame Mixer initialisiert.")
    except pygame.error:
        logger.error("Mixer Init fehlgeschlagen", exc_info=True)

    # Bildschirm Setup
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # Fallback
    try:
        info=pygame.display.Info()
        SCREEN_WIDTH,SCREEN_HEIGHT=info.current_w, info.current_h
        logger.info(f"Bildschirmgröße: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    except Exception:
        logger.warning(f"Bildschirm Fehler. Nutze 800x600.", exc_info=True)
        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
        try:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
        except Exception as e_fallback:
            logger.critical("Fallback-Bildschirm Fehler", exc_info=True); pygame.quit(); sys.exit()
    if screen is None:
        logger.critical("Bildschirm nicht initialisiert."); pygame.quit(); sys.exit()
    pygame.display.set_caption("Das Spiel")
    clock = pygame.time.Clock()
    logger.info("Screen & Clock erstellt.")

    # Weltgröße, Fonts, UI-Elemente Positionen/Größen
    WORLD_WIDTH = SCREEN_WIDTH * 3
    WORLD_HEIGHT = SCREEN_HEIGHT * 2
    # Skalierte Schriftgrößen berechnen
    ui_fs = max(12, int(SCREEN_HEIGHT * (BASE_UI_FONT_SIZE / FONT_SIZE_REF_H)))
    btn_fs = max(10, int(SCREEN_HEIGHT * (BASE_BUTTON_FONT_SIZE / FONT_SIZE_REF_H)))
    inv_fs = max(8, int(SCREEN_HEIGHT * (BASE_INV_QTY_FONT_SIZE / FONT_SIZE_REF_H)))
    dlg_fs = max(14, int(SCREEN_HEIGHT * (BASE_DIALOG_FONT_SIZE / FONT_SIZE_REF_H)))
    shp_fs = max(10, int(SCREEN_HEIGHT * (BASE_SHOP_FONT_SIZE / FONT_SIZE_REF_H)))
    # Fonts erstellen (mit Fallback)
    try:
        ui_font = pygame.font.Font(None, ui_fs)
        btn_font = pygame.font.Font(None, btn_fs)
        inv_font = pygame.font.Font(None, inv_fs)
        dlg_font = pygame.font.Font(None, dlg_fs)
        shp_font = pygame.font.Font(None, shp_fs)
        logger.info(f"Fonts: UI={ui_fs},Btn={btn_fs},Inv={inv_fs},Dlg={dlg_fs},Shop={shp_fs}")
    except Exception:
        logger.exception("Font Fehler:")
        ui_font=pygame.font.Font(None, 28); btn_font=pygame.font.Font(None,18)
        inv_font=pygame.font.Font(None, 16); dlg_font=pygame.font.Font(None, 24)
        shp_font=pygame.font.Font(None, 18) # Fallback Fonts
    # Button und Inventar-Position berechnen
    BTN_DEF_W = int(SCREEN_WIDTH * BUTTON_DEFAULT_WIDTH_PERCENT)
    BTN_DEF_H = int(SCREEN_HEIGHT * BUTTON_DEFAULT_HEIGHT_PERCENT)
    BUTTON_RECT = pygame.Rect(BUTTON_X, 0, BTN_DEF_W, BTN_DEF_H)
    inv_w = MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING
    CENTERED_INVENTORY_X_POS = (SCREEN_WIDTH - inv_w) // 2
    CENTERED_INVENTORY_Y_POS = SCREEN_HEIGHT - SCALED_BOX_SIZE - INVENTORY_BOTTOM_PADDING
    logger.info(f"Inventar: B={inv_w}, Pos=({CENTERED_INVENTORY_X_POS},{CENTERED_INVENTORY_Y_POS})")

    # Assets laden
    logger.info("Lade Assets...")
    item_icons, placed_item_images, fallback_placed_image = items.load_item_assets(
        IMAGE_FOLDER, PLACED_ITEM_SIZE, SCALED_ICON_SIZE, load_image_asset
    )
    background_image = load_image_asset(BACKGROUND_FILENAME, alpha=False)
    if background_image:
        try:
            if background_image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                background_image=pygame.transform.smoothscale(background_image,(SCREEN_WIDTH,SCREEN_HEIGHT))
                logger.info("BG skaliert.")
        except Exception:
            logger.exception("BG Skalierung fehlgeschlagen:"); background_image = None
    button_image_normal = load_image_asset(BUTTON_FILENAME, alpha=True)
    money_slot_background_img = load_image_asset(MONEY_ICON_FILENAME, alpha=True,
                                             scale_to=(SCALED_BOX_SIZE, SCALED_BOX_SIZE))
    if not money_slot_background_img:
        logger.warning(f"Geld-Icon '{MONEY_ICON_FILENAME}' nicht geladen.")

    # Spielobjekte erstellen (inkl. Laden)
    player_start_x=WORLD_WIDTH//2; player_start_y=WORLD_HEIGHT//2
    player_radius=TILE_SIZE//3; spawn_x,spawn_y=player_start_x,player_start_y
    player_money = 0.0
    loaded_player_data = load_data(PLAYER_POS_SAVE_FILE)
    if isinstance(loaded_player_data, dict):
        if 'x' in loaded_player_data and 'y' in loaded_player_data:
            try: spawn_x=int(loaded_player_data['x']); spawn_y=int(loaded_player_data['y'])
            except: logger.warning(f"Ungültige Pos-Daten. Standard ({spawn_x},{spawn_y})")
        if 'money' in loaded_player_data:
            try: player_money = float(loaded_player_data['money'])
            except: logger.warning(f"Ungültige Money-Daten. Standard ({player_money})")
    else: logger.info("Keine Spielerdatei. Standardwerte.")
    player = Player(spawn_x, spawn_y, player_radius, RED)
    logger.info(f"Spieler erstellt bei ({spawn_x},{spawn_y}), Geld: {player_money:.2f}")

    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
    cam_x = max(0, min(player.rect.centerx - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
    cam_y = max(0, min(player.rect.centery - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))
    camera.camera_rect.topleft = (cam_x, cam_y)
    logger.info(f"Kamera ausgerichtet: {camera.camera_rect.topleft}")

    inventory = Inventory(filepath=INVENTORY_SAVE_FILE); logger.info("Inventar erstellt/geladen.");
    if not inventory.has_item("Blumentopf"): inventory.add_item("Blumentopf", 3)
    if not inventory.has_item("Sack Erde"): inventory.add_item("Sack Erde", 5)
    if not inventory.has_item("Weed Seeds"): inventory.add_item("Weed Seeds", 5)

    all_sprites=pygame.sprite.Group(); npcs=pygame.sprite.Group(); placed_items=pygame.sprite.Group()
    logger.debug("Lade platzierte Items...")
    loaded_items_list = load_data(PLACED_ITEMS_SAVE_FILE, default_data=[])
    loaded_item_count = 0
    if isinstance(loaded_items_list, list):
        for item_data in loaded_items_list:
            if isinstance(item_data, dict):
                try:
                    item_type=item_data.get('type','?'); item_x=int(item_data['x'])
                    item_y=int(item_data['y']); item_state=item_data.get('state','ohneErde')
                    item_timer=item_data.get('timer_end', None)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Ungültiger Eintrag: {item_data} -> {e}", exc_info=True); continue
                images = placed_item_images.get(item_type, {})
                fallback = fallback_placed_image
                new = items.PlacedItem(item_x,item_y,item_type,images,fallback,GROW_TIME_SECONDS,state=item_state,timer_end_timestamp=item_timer)
                if new.rect: all_sprites.add(new); placed_items.add(new); loaded_item_count += 1
                else: logger.error(f"PlacedItem Laden Fehler: {item_data}")
            else: logger.warning(f"Ungültiger Typ in {PLACED_ITEMS_FILENAME}: {type(item_data)}")
        logger.info(f"{loaded_item_count} Items geladen.")
    else: logger.warning(f"'{PLACED_ITEMS_FILENAME}' war keine Liste.")

    npc_radius=TILE_SIZE//3
    npc_generic=NPC(WORLD_WIDTH-TILE_SIZE*10, TILE_SIZE*15, npc_radius, GREEN, npc_type="generic", dialog_id="generic_hallo")
    npc_merchant=NPC(2400, 1000, npc_radius, BLUE, npc_type="merchant", dialog_id="händler_start")
    all_sprites.add(player, npc_generic, npc_merchant); npcs.add(npc_generic, npc_merchant)
    logger.debug("NPCs hinzugefügt.")

    # UI & Button Rect anpassen
    if platform_utils.IS_ANDROID and button_image_normal:
        btn_w_act=button_image_normal.get_width(); btn_h_act=button_image_normal.get_height()
    else: btn_w_act=BTN_DEF_W; btn_h_act=BTN_DEF_H
    BUTTON_Y=CENTERED_INVENTORY_Y_POS-btn_h_act-BUTTON_PADDING
    BUTTON_RECT.size=(btn_w_act,btn_h_act); BUTTON_RECT.topleft=(BUTTON_X,BUTTON_Y)
    logger.debug(f"Interaktions-Button Rect: {BUTTON_RECT}")

    if platform_utils.IS_ANDROID:
        platform_utils.set_android_immersive_mode(); logger.info("Immersive Mode aktiviert.")

except Exception as e:
    logger.critical("Init/Setup Fehler", exc_info=True); pygame.quit(); sys.exit()


# --- Spiel-Loop ---
running = True; logger.info("Spiel-Loop startet.")
while running:
    try:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos_screen = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # --- Nur im Play-Zustand ---
        if current_game_state == GAME_STATE_PLAY:
            # Interaktionsziel finden
            closest_target=None; min_dist_sq=(INTERACTION_RADIUS*1.1)**2
            player_cx=player.rect.centerx; player_cy=player.rect.centery; closest_type=None
            # Items prüfen
            for item in placed_items:
                dist_sq=(player_cx-item.rect.centerx)**2+(player_cy-item.rect.centery)**2
                if dist_sq<min_dist_sq: min_dist_sq=dist_sq; closest_target=item; closest_type="item"
            # NPCs prüfen
            for npc_obj in npcs:
                 dist_sq=(player_cx-npc_obj.rect.centerx)**2+(player_cy-npc_obj.rect.centery)**2
                 if dist_sq<min_dist_sq: min_dist_sq=dist_sq; closest_target=npc_obj; closest_type="npc"
            potential_interaction_target=closest_target; target_type=closest_type
            interaction_possible_now=potential_interaction_target is not None
            # Ziel verloren?
            if interaction_active and potential_interaction_target!=closest_target:
                logger.debug("Ziel verloren.")
                potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False; target_type=None
            # Updates
            player.update(keys, camera.get_current_screen_rect()); camera.update(player)
            npcs.update(); placed_items.update(dt)
            # Aufheben (Langes Halten)
            if (interaction_active and target_type=="item" and potential_interaction_target and
                time.time() - interaction_start_time >= LONG_PRESS_THRESHOLD):
                logger.info(f"Pickup '{potential_interaction_target.item_type}'")
                item_type=potential_interaction_target.item_type
                if inventory.add_item(item_type, 1):
                    logger.info(f"'{item_type}' zum Inventar.")
                    potential_interaction_target.kill(); logger.info("Item entfernt.")
                else: logger.warning("Aufheben fehlgeschlagen: Inventar voll?")
                potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False

        # --- Event Handling ---
        interaction_press_event_handled = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False; logger.info("QUIT Event.")

            # --- Keyboard ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: # ESC Taste
                    if current_game_state in [GAME_STATE_DIALOG, GAME_STATE_SHOP]:
                        logger.info("ESC: Zurück zum Spiel.")
                        current_game_state=GAME_STATE_PLAY; active_npc=None; current_dialog_node_id=None
                    elif not platform_utils.IS_ANDROID: # ESC im Spiel (Nicht-Android)
                        logger.info("ESC: Zurück zum Menü..."); save_game_state()
                        pygame.quit(); logger.info("Game beendet.");
                        try: args=[sys.executable,MAIN_SCRIPT_PATH]; logger.info(f"Exec: {args}"); os.execv(sys.executable, args)
                        except Exception as e: logger.critical("Exec Fehler", exc_info=True); sys.exit(1)
                # Leertaste Interaktion (nur Play State, Nicht-Android)
                elif (event.key == pygame.K_SPACE and
                      current_game_state == GAME_STATE_PLAY and
                      not platform_utils.IS_ANDROID):
                    if not interaction_active and interaction_possible_now:
                        interaction_active=True; interaction_press_event_handled=True
                        interaction_start_time=time.time()
                        target_name=getattr(potential_interaction_target,'item_type',getattr(potential_interaction_target,'npc_type','?'))
                        logger.info(f"Start Interaktion (SPACE) mit {target_type} '{target_name}'")

            elif event.type == pygame.KEYUP:
                 # Leertaste Loslassen (nur Play State, Nicht-Android)
                 if (event.key == pygame.K_SPACE and
                     current_game_state == GAME_STATE_PLAY and
                     not platform_utils.IS_ANDROID):
                     if interaction_active and potential_interaction_target:
                         # Kurzer Druck?
                         if time.time() - interaction_start_time < LONG_PRESS_THRESHOLD:
                             logger.debug(f"Kurz (SPACE) auf {target_type}")
                             if target_type == "item": # Item Interaktion
                                 item=potential_interaction_target; logger.debug(f"-> Aktion {item.state}")
                                 req_item=None; prereq_ok=False
                                 if item.state=='ohneErde': req_item="Sack Erde"
                                 elif item.state=='ohneSeed': req_item="Weed Seeds"
                                 elif item.state in ['giessen', 'readyToEarn', 'growing']: prereq_ok=True
                                 if req_item:
                                     has=inventory.has_item(req_item, 1); logger.debug(f"Check '{req_item}': {has}")
                                     if has:
                                         rem=inventory.remove_item(req_item, 1); logger.debug(f"Remove '{req_item}': {rem}")
                                         if rem: prereq_ok=True; logger.info(f"'{req_item}' verbraucht.")
                                         else: logger.error(f"Remove Fehler trotz has_item")
                                     else: logger.info(f"Fehlt: '{req_item}'.")
                                 if prereq_ok: logger.debug("-> item.interact()"); item.interact()
                                 else: logger.debug("Voraussetzung nicht erfüllt.")
                             elif target_type == "npc": # NPC Interaktion -> Dialog
                                 active_npc=potential_interaction_target; logger.info(f"Interagiere mit NPC '{active_npc.npc_type}'")
                                 if active_npc.dialog_id:
                                     current_dialog_node_id=active_npc.dialog_id
                                     current_game_state=GAME_STATE_DIALOG; logger.info(f"-> DIALOG (Start: {current_dialog_node_id})")
                                 else: logger.warning("NPC hat keine Dialog-ID."); active_npc=None
                         # Reset nach Loslassen (kurz oder lang)
                         potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False; target_type=None

            # --- Maus ---
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_game_state == GAME_STATE_PLAY:
                    # Android Button
                    if platform_utils.IS_ANDROID and BUTTON_RECT.collidepoint(mouse_pos_screen):
                         if not interaction_active and interaction_possible_now:
                             interaction_active=True; interaction_press_event_handled=True
                             interaction_start_time=time.time()
                             target_name=getattr(potential_interaction_target,'item_type',getattr(potential_interaction_target,'npc_type','?'))
                             logger.info(f"Start Interaktion (Button) mit {target_type} '{target_name}'")
                         else: logger.debug("Button Klick ignoriert")
                    # Drag Start?
                    elif not is_dragging:
                        inv_list=inventory.get_item_list_for_display()
                        for i in range(MAX_SLOTS):
                            if i==MAX_SLOTS-1: continue # Geld-Slot
                            slot_x=CENTERED_INVENTORY_X_POS+i*(SCALED_BOX_SIZE+SCALED_PADDING); slot_y=CENTERED_INVENTORY_Y_POS
                            slot_rect=pygame.Rect(slot_x,slot_y,SCALED_BOX_SIZE,SCALED_BOX_SIZE)
                            if slot_rect.collidepoint(mouse_pos_screen) and i<len(inv_list):
                                try:
                                    item_name_temp, quantity_temp = inv_list[i]
                                    logger.debug(f"Slot {i} C: '{item_name_temp}', Q:{quantity_temp}")
                                    if item_name_temp=="Blumentopf" and quantity_temp>0:
                                        is_dragging=True; dragged_item_type="Blumentopf"
                                        img_key='ohneErde'; dragged_item_image=placed_item_images.get("Blumentopf",{}).get(img_key,fallback_placed_image)
                                        logger.info(f"Starte Drag: {dragged_item_type}"); break
                                except ValueError: logger.error(f"Inv list unpack Error: {inv_list[i]}",exc_info=True)
                                except Exception as e: logger.error(f"Drag Start Error: {e}",exc_info=True)

                elif current_game_state == GAME_STATE_DIALOG: # Dialog Klick
                    for i,rect in enumerate(dialog_response_rects):
                        if rect.collidepoint(mouse_pos_screen):
                            logger.debug(f"Dialog Antwort {i} geklickt.")
                            node=dialog.get_dialog_node(current_dialog_node_id)
                            if node and i<len(node["responses"]):
                                response=node["responses"][i]; action=response.get("action"); next_node=response.get("next_node")
                                if action=="open_shop": logger.info("Aktion: Shop."); current_game_state=GAME_STATE_SHOP
                                elif action=="end_dialog": logger.info("Aktion: Dialog Ende."); current_game_state=GAME_STATE_PLAY; current_dialog_node_id=None; active_npc=None
                                elif next_node: logger.info(f"-> Dialog: {next_node}"); current_dialog_node_id=next_node
                                elif not action: logger.info("Keine Aktion -> Dialog Ende."); current_game_state=GAME_STATE_PLAY; current_dialog_node_id=None; active_npc=None
                            break # Nur eine Antwort pro Klick

                elif current_game_state == GAME_STATE_SHOP: # Shop Klick
                    item_clicked = False
                    available_items = shop_items.get_available_items()
                    for i, rect in enumerate(shop_item_rects):
                        if rect.collidepoint(mouse_pos_screen):
                            item_clicked = True
                            logger.debug(f"Shop Slot {i} geklickt.")
                            if i < len(available_items): # Gültiger Index?
                                item_to_buy=available_items[i]; name=item_to_buy["name"]; price=item_to_buy["price"]
                                logger.info(f"Versuche Kauf: '{name}' für {price:.2f}.")
                                if player_money >= price:
                                    if inventory.add_item(name, 1): player_money -= price; logger.info(f"Gekauft! Neu: {player_money:.2f}")
                                    else: logger.warning("Kauf fehlgeschlagen: Inventar voll?")
                                else: logger.warning("Kauf fehlgeschlagen: Zu wenig Geld.")
                            else: logger.error(f"Shop-Klick Fehler: Index {i}")
                            break # Klick auf Slot verarbeitet
                    # Prüfe Exit Button NUR wenn kein Item geklickt wurde
                    if not item_clicked and shop_exit_button_rect and shop_exit_button_rect.collidepoint(mouse_pos_screen):
                        logger.info("Shop verlassen -> Zurück zum Spiel.")
                        current_game_state = GAME_STATE_PLAY
                        active_npc = None
                        current_dialog_node_id = None

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: # Linksklick Loslassen
                if current_game_state == GAME_STATE_PLAY:
                    # Android Button Loslassen
                    if platform_utils.IS_ANDROID and interaction_active:
                        logger.debug("Android Button losgelassen")
                        if potential_interaction_target and time.time()-interaction_start_time<LONG_PRESS_THRESHOLD: # Kurzer Druck
                            logger.debug(f"Kurz (Button) auf {target_type}")
                            if target_type=="item": # Item Interaktion
                                item=potential_interaction_target; logger.debug(f"-> Aktion {item.state}")
                                req_item=None; prereq_ok=False
                                if item.state=='ohneErde': req_item="Sack Erde"
                                elif item.state=='ohneSeed': req_item="Weed Seeds"
                                elif item.state in ['giessen','readyToEarn','growing']: prereq_ok=True
                                if req_item:
                                    has=inventory.has_item(req_item, 1); logger.debug(f"Check '{req_item}': {has}")
                                    if has:
                                        rem=inventory.remove_item(req_item, 1); logger.debug(f"Remove '{req_item}': {rem}")
                                        if rem: prereq_ok=True; logger.info(f"'{req_item}' verbraucht.")
                                        else: logger.error("Remove Fehler trotz has_item (Android)")
                                    else: logger.info(f"Fehlt: '{req_item}'.")
                                if prereq_ok: logger.debug("-> item.interact()"); item.interact()
                                else: logger.debug("Voraussetzung nicht erfüllt.")
                            elif target_type=="npc": # NPC Interaktion
                                active_npc=potential_interaction_target; logger.info(f"Interagiere mit NPC '{active_npc.npc_type}'")
                                if active_npc.dialog_id: current_dialog_node_id=active_npc.dialog_id; current_game_state=GAME_STATE_DIALOG; logger.info(f"-> DIALOG (Start: {current_dialog_node_id})")
                                else: logger.warning("NPC hat keine Dialog-ID."); active_npc=None
                        potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False; target_type=None # Reset
                    # Drag Ende
                    elif is_dragging:
                         world_x,world_y=camera.screen_to_world(mouse_pos_screen[0],mouse_pos_screen[1]); snapped_tl_x=(world_x//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE; snapped_tl_y=(world_y//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE; snapped_center_x=snapped_tl_x+PLACED_ITEM_SIZE/2; snapped_center_y=snapped_tl_y+PLACED_ITEM_SIZE/2; can_place=True; temp_rect=pygame.Rect(snapped_tl_x,snapped_tl_y,PLACED_ITEM_SIZE,PLACED_ITEM_SIZE)
                         for item in placed_items:
                             if temp_rect.colliderect(item.rect): can_place=False; logger.info("Platzieren blockiert."); break
                         if can_place:
                             if inventory.remove_item(dragged_item_type,1):
                                 images=placed_item_images.get(dragged_item_type,{}); fallback=fallback_placed_image; new_item=items.PlacedItem(snapped_center_x,snapped_center_y,dragged_item_type,images,fallback,GROW_TIME_SECONDS,state='ohneErde');
                                 if new_item.rect: all_sprites.add(new_item); placed_items.add(new_item); logger.info(f"'{dragged_item_type}' platziert.")
                                 else: logger.error("Fehler PlacedItem Erstellung!"); inventory.add_item(dragged_item_type,1)
                             else: logger.warning("Platzieren fehlgeschlagen (Inventar-Problem?)")
                         is_dragging=False; dragged_item_type=None; dragged_item_image=None

        # --- Draw ---
        # 1. Spielwelt (nur Play State)
        if current_game_state == GAME_STATE_PLAY:
            if background_image: screen.blit(background_image, (0, 0))
            else: screen.fill(BLACK)
            for sprite in all_sprites:
                if camera.get_current_screen_rect().colliderect(sprite.rect): screen.blit(sprite.image, camera.apply(sprite))
            if interaction_active and potential_interaction_target:
                try: 
                    player_rect_s=camera.apply(player); center_s=player_rect_s.center; pygame.draw.circle(screen,WHITE,center_s,int(INTERACTION_RADIUS),1);
                    if interaction_start_time>0 and target_type=="item": hold_dur=time.time()-interaction_start_time; prog=min(1.0,hold_dur/LONG_PRESS_THRESHOLD);
                    if prog>0: bar_w=50;bar_h=5;bar_x=center_s[0]-bar_w//2;bar_y=player_rect_s.top-bar_h-5; pygame.draw.rect(screen,(50,50,50),(bar_x,bar_y,bar_w,bar_h)); pygame.draw.rect(screen,RED,(bar_x,bar_y,int(bar_w*prog),bar_h))
                except Exception as e: 
                    logger.error(f"Zeichenfehler Interaktion: {e}", exc_info=True)
            try: # UI Text
                if ui_font: pos_txt=f"P({player.rect.x},{player.rect.y}) C({camera.camera_rect.x},{camera.camera_rect.y})"; surf=ui_font.render(pos_txt,True,WHITE); screen.blit(surf,(10,10))
            except Exception as e: logger.error(f"Zeichenfehler UI-Text: {e}", exc_info=True)
            # Inventar + Geld
            try:
                inv_list=inventory.get_item_list_for_display();
                for i in range(MAX_SLOTS):
                    slot_x=CENTERED_INVENTORY_X_POS+i*(SCALED_BOX_SIZE+SCALED_PADDING); slot_y=CENTERED_INVENTORY_Y_POS; slot_rect=pygame.Rect(slot_x,slot_y,SCALED_BOX_SIZE,SCALED_BOX_SIZE)
                    if i==MAX_SLOTS-1: # Geld
                        if money_slot_background_img: screen.blit(money_slot_background_img,slot_rect.topleft)
                        else: pygame.draw.rect(screen,(100,100,100,180),slot_rect)
                        pygame.draw.rect(screen,WHITE,slot_rect,2)
                        if inv_font: 
                            try:money_txt=locale.currency(player_money,grouping=True)
                            except:money_txt=f"{player_money:.2f}"
                        m_surf=inv_font.render(money_txt,True,GREEN); m_rect=m_surf.get_rect(center=slot_rect.center); screen.blit(m_surf,m_rect)
                    elif i<len(inv_list): # Item
                        pygame.draw.rect(screen,(100,100,100,180),slot_rect); pygame.draw.rect(screen,WHITE,slot_rect,2); name,qty=inv_list[i]; icon_surf=item_icons.get(name)
                        if icon_surf: i_rect=icon_surf.get_rect(center=slot_rect.center); screen.blit(icon_surf,i_rect)
                        else: # Text Fallback
                            if inv_font: fb_surf=inv_font.render(name,True,WHITE); fb_rect=fb_surf.get_rect(center=slot_rect.center); screen.blit(fb_surf,fb_rect)
                        if qty>0 and inv_font: q_surf=inv_font.render(str(qty),True,WHITE); q_rect=q_surf.get_rect(bottomright=(slot_rect.right-SCALED_PADDING//2,slot_rect.bottom-SCALED_PADDING//2)); screen.blit(q_surf,q_rect)
                    else: # Leer
                        pygame.draw.rect(screen,(100,100,100,180),slot_rect); pygame.draw.rect(screen,WHITE,slot_rect,2)
            except Exception as e: logger.error(f"Fehler Inventar-Anzeige: {e}", exc_info=True)
            # Drag Preview
            if is_dragging and dragged_item_image: world_x, world_y = camera.screen_to_world(mouse_pos_screen[0], mouse_pos_screen[1]); snapped_tl_x = (world_x // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE; snapped_tl_y = (world_y // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE; temp_snap_rect_world = pygame.Rect(snapped_tl_x, snapped_tl_y, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE); snapped_screen_rect = camera.apply_rect(temp_snap_rect_world); drag_rect = dragged_item_image.get_rect(center=snapped_screen_rect.center); screen.blit(dragged_item_image, drag_rect); pygame.draw.rect(screen, WHITE, snapped_screen_rect, 1)
            # Android Button
            if platform_utils.IS_ANDROID:
                if button_image_normal: screen.blit(button_image_normal, BUTTON_RECT.topleft)
                else: pygame.draw.rect(screen, BUTTON_COLOR_NORMAL, BUTTON_RECT); pygame.draw.rect(screen, BUTTON_BORDER_COLOR, BUTTON_RECT, 2)
                if not button_image_normal and pygame.font.get_init() and btn_font:
                    try: btn_surf=btn_font.render("Interact",True,WHITE); btn_rect=btn_surf.get_rect(center=BUTTON_RECT.center); screen.blit(btn_surf,btn_rect)
                    except Exception as e: logger.error(f"Fehler Button-Text: {e}", exc_info=True)

        # 2. Dialog-UI
        elif current_game_state == GAME_STATE_DIALOG:
             dialog_response_rects.clear(); node = dialog.get_dialog_node(current_dialog_node_id)
             if node and dlg_font:
                 dlg_h=SCREEN_HEIGHT//3; dlg_rect=pygame.Rect(0,SCREEN_HEIGHT-dlg_h,SCREEN_WIDTH,dlg_h); pygame.draw.rect(screen,DARK_BLUE,dlg_rect); pygame.draw.rect(screen,WHITE,dlg_rect,3)
                 npc_txt_rect=pygame.Rect(dlg_rect.left+20,dlg_rect.top+20,dlg_rect.width-40,dlg_rect.height//2-30); wrap_text(screen,node["npc_text"],dlg_font,WHITE,npc_txt_rect)
                 resp_y=npc_txt_rect.bottom+15; resp_h=35; resp_sp=10; btn_w=dlg_rect.width//2-30
                 for i,response in enumerate(node["responses"]):
                     btn_x=dlg_rect.left+20; btn_y=resp_y+i*(resp_h+resp_sp); resp_rect=pygame.Rect(btn_x,btn_y,btn_w,resp_h); dialog_response_rects.append(resp_rect)
                     hover=resp_rect.collidepoint(mouse_pos_screen); btn_col=LIGHT_GREY if hover else GREY; pygame.draw.rect(screen,btn_col,resp_rect); pygame.draw.rect(screen,WHITE,resp_rect,1)
                     resp_surf=dlg_font.render(response["text"],True,BLACK); resp_rect_txt=resp_surf.get_rect(center=resp_rect.center); screen.blit(resp_surf,resp_rect_txt)
             else: logger.error(f"Dialog-Knoten '{current_dialog_node_id}' Fehler."); current_game_state=GAME_STATE_PLAY; active_npc=None; current_dialog_node_id=None

        # 3. Shop-UI
        elif current_game_state == GAME_STATE_SHOP:
            shop_item_rects.clear(); shop_margin=50; shop_rect=pygame.Rect(shop_margin,shop_margin,SCREEN_WIDTH-2*shop_margin,SCREEN_HEIGHT-2*shop_margin); pygame.draw.rect(screen,DARK_BLUE,shop_rect); pygame.draw.rect(screen,WHITE,shop_rect,3)
            if ui_font: title_surf=ui_font.render("Shop",True,YELLOW); title_rect=title_surf.get_rect(centerx=shop_rect.centerx,top=shop_rect.top+15); screen.blit(title_surf,title_rect)
            if inv_font: 
                try: money_txt_shop=locale.currency(player_money,grouping=True)
                except: money_txt_shop=f"{player_money:.2f}"
            m_surf_s=inv_font.render(f"Geld: {money_txt_shop}",True,GREEN); m_rect_s=m_surf_s.get_rect(right=shop_rect.right-20,top=shop_rect.top+20); screen.blit(m_surf_s,m_rect_s)
            cols=4; rows=8; shop_list=shop_items.get_available_items(); grid_x=shop_rect.left+30; grid_y=shop_rect.top+70; cell_w=(shop_rect.width-60)//cols; cell_h=(shop_rect.height-120)//rows; shop_icon_size=min(cell_w//2,cell_h//2)
            for i,item_data in enumerate(shop_list):
                if i>=cols*rows: break
                row=i//cols; col=i%cols; cell_x=grid_x+col*cell_w; cell_y=grid_y+row*cell_h; cell_rect=pygame.Rect(cell_x,cell_y,cell_w-10,cell_h-10); shop_item_rects.append(cell_rect)
                hover=cell_rect.collidepoint(mouse_pos_screen); cell_col=LIGHT_GREY if hover else GREY; pygame.draw.rect(screen,cell_col,cell_rect); pygame.draw.rect(screen,WHITE,cell_rect,1)
                name=item_data["name"]; s_icon=load_image_asset(items.ICON_FILES.get(name),alpha=True,scale_to=(shop_icon_size,shop_icon_size))
                if s_icon: i_rect=s_icon.get_rect(centerx=cell_rect.centerx,top=cell_rect.top+5); screen.blit(s_icon,i_rect)
                if shp_font: 
                    try: price_txt=locale.currency(item_data["price"],grouping=True)
                    except: price_txt=f"{item_data['price']:.2f}"
                p_surf=shp_font.render(price_txt,True,YELLOW); p_rect=p_surf.get_rect(centerx=cell_rect.centerx,bottom=cell_rect.bottom-5); screen.blit(p_surf,p_rect)
            exit_w=100; exit_h=40; exit_x=shop_rect.centerx-exit_w//2; exit_y=shop_rect.bottom-exit_h-15; shop_exit_button_rect=pygame.Rect(exit_x,exit_y,exit_w,exit_h); hover=shop_exit_button_rect.collidepoint(mouse_pos_screen); exit_col=RED if hover else DARK_BLUE; pygame.draw.rect(screen,exit_col,shop_exit_button_rect); pygame.draw.rect(screen,WHITE,shop_exit_button_rect,2)
            if btn_font: exit_surf=btn_font.render("Verlassen",True,WHITE); exit_rect=exit_surf.get_rect(center=shop_exit_button_rect.center); screen.blit(exit_surf,exit_rect)

        # Flip
        pygame.display.flip()

    except Exception as e_game_loop:
        logger.critical(f"Unerwarteter Fehler in Spielschleife: {e_game_loop}", exc_info=True)
        running = False

# --- Spiel beenden ---
logger.info("Spiel-Loop beendet.")
save_game_state()
if pygame.get_init(): pygame.quit(); logger.info("Pygame beendet.")
else: logger.info("Pygame war bereits beendet.")
sys.exit()