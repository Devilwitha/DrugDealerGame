# game.py (Erneut formatiert für maximale Lesbarkeit)
import pygame
import sys
import logging
import os
import math
import time
import traceback
import locale
import subprocess # Für Minispiel-Start

# Optional: Locale für Währungsformat setzen (mit Fallbacks)
try:
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
    except locale.Error:
        print("WARNUNG: Locale 'de_DE' nicht verfügbar für Währung.")


# --- Logging Konfiguration ---
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
log_level = logging.DEBUG
date_fmt = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(
    level=log_level, format=log_format, datefmt=date_fmt, force=True
)
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
# Dateipfade
SETTINGS_FILE_PATH = os.path.join(SETTINGS_DIR, "settings.json")
MAIN_SCRIPT_PATH = os.path.join(project_root_dir, "main.py")
MINIGAME_GROW1_PATH = os.path.join(
    project_root_dir, "data", "miniGame", "Growing", "plant_grow1.py"
)
INVENTORY_FILENAME = "inventar.json"
INVENTORY_SAVE_FILE = os.path.join(SAVE_DATA_DIR_ABS, INVENTORY_FILENAME)
PLAYER_POS_FILENAME = "player_position.json"
PLAYER_POS_SAVE_FILE = os.path.join(SAVE_DATA_DIR_ABS, PLAYER_POS_FILENAME)
PLACED_ITEMS_FILENAME = "placed_items.json"
PLACED_ITEMS_SAVE_FILE = os.path.join(SAVE_DATA_DIR_ABS, PLACED_ITEMS_FILENAME)

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
    logger.error(f"Fehler File Logging: {e}", exc_info=True)

logger.info("Spiel wird initialisiert...")
logger.debug(f"Project Root: {project_root_dir}")

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
INTERACTION_RADIUS = TILE_SIZE * 1.5
LONG_PRESS_THRESHOLD = 1.0
GROW_TIME_SECONDS = 10 # Zum Testen kurz
# Inventar-Skalierung
INVENTORY_SCALE_FACTOR = 2.0
SCALED_BOX_SIZE = int(BOX_SIZE * INVENTORY_SCALE_FACTOR)
SCALED_PADDING = int(PADDING * INVENTORY_SCALE_FACTOR)
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
MONEY_ICON_FILENAME = "money_icon.png"


# === Hilfsfunktionen ===

def load_image_asset(filename, alpha=True, scale_to=None):
    """Lädt ein Bild aus dem IMAGE_FOLDER und skaliert es optional."""
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
    except Exception as e:
        logger.error(f"Allg. Fehler Laden Bild '{path}': {e}", exc_info=True)
        return None

    if scale_to:
        # Prüfe auf gültige Skalierungsdimensionen
        if (not isinstance(scale_to, (tuple, list)) or len(scale_to) != 2 or
                scale_to[0] <= 0 or scale_to[1] <= 0):
            logger.error(f"Ungültiges scale_to '{scale_to}' für '{filename}'.")
        else:
            try:
                image = pygame.transform.smoothscale(image, scale_to)
            except Exception:
                logger.error(f"Fehler Skalieren '{filename}' zu {scale_to}", exc_info=True)
    return image

def save_game_state():
    """Speichert alle relevanten Spieldaten."""
    logger.info("Speichere Spielstand...")
    # Inventar
    try:
        if inventory:
            logger.info("  Speichere Inventar...")
            inventory.save_inventory()
        else: logger.warning("  Inventar nicht initialisiert.")
    except Exception: logger.exception("  Fehler Inv speichern:")
    # Spielerdaten
    try:
        if player:
            logger.info("  Speichere Spielerposition & Geld...")
            player_data = {'x': player.rect.x, 'y': player.rect.y, 'money': player_money}
            save_data(player_data, PLAYER_POS_SAVE_FILE)
        else: logger.warning("  Spieler nicht initialisiert.")
    except Exception: logger.exception("  Fehler Pos/Geld speichern:")
    # Platzierte Items
    try:
        if placed_items is not None:
            logger.info("  Speichere platzierte Items...")
            items_to_save = [
                {'type': item.item_type, 'x': item.rect.centerx,
                 'y': item.rect.centery, 'state': item.state,
                 'timer_end': item.timer_end_timestamp}
                for item in placed_items
            ]
            save_data(items_to_save, PLACED_ITEMS_SAVE_FILE)
            logger.info(f"  {len(items_to_save)} Items gespeichert.")
        else: logger.warning("  Placed_items Gruppe nicht initialisiert.")
    except Exception: logger.exception("  Fehler Items speichern:")

def wrap_text(surface, text, font, color, rect, aa=True):
    """Zeichnet Text mit Zeilenumbruch innerhalb eines Rechtecks."""
    if not font:
        logger.error("wrap_text: Font ist None!")
        return
    
    lines = []
    words = text.split(' ')
    current_line_words = []

    # Erstelle Zeilen, die in das Rechteck passen
    while words:
        word = words.pop(0)
        current_line_words.append(word)
        try:
            line_width, line_height = font.size(' '.join(current_line_words))
            if line_width > rect.width:
                # Wenn mehr als ein Wort -> letztes Wort zurück in die Liste
                if len(current_line_words) > 1:
                    last_word = current_line_words.pop()
                    words.insert(0, last_word)
                # Aktuelle Zeile speichern (auch wenn nur 1 Wort zu lang ist)
                lines.append(' '.join(current_line_words))
                current_line_words = [] # Neue Zeile beginnen
        except pygame.error:
            logger.exception("Fehler bei font.size() in wrap_text")
            return # Abbruch bei Font-Fehler

    if current_line_words: # Letzte Zeile hinzufügen
        lines.append(' '.join(current_line_words))

    # Zeichne die erstellten Zeilen
    y = rect.top
    line_spacing = font.get_linesize() * 0.9 # Etwas weniger als Standard
    line_height = font.get_height()

    for line in lines:
        if y + line_height > rect.bottom:
            logger.warning("Textumbruch: Nicht alle Zeilen passen ins Rechteck.")
            break
        try:
            img = font.render(line, aa, color)
            surface.blit(img, (rect.left, y))
            y += int(line_spacing)
        except pygame.error:
            logger.exception(f"Fehler bei font.render() für: '{line}'")
            break


# === Globale Variablen (Initialisierung im Hauptblock) ===
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

# === Haupt-Initialisierungsblock ===
try:
    pygame.init()
    try:
        pygame.mixer.init()
        logger.info("Pygame Mixer initialisiert.")
    except pygame.error:
        logger.error("Mixer Init fehlgeschlagen", exc_info=True)

    # Bildschirm
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # Fallback
    try:
        info = pygame.display.Info()
        SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
        logger.info(f"Bildschirmgröße: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    except Exception:
        logger.warning("Bildschirm Fehler. Nutze 800x600.", exc_info=True)
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

    # Welt, Fonts, UI
    WORLD_WIDTH = SCREEN_WIDTH * 3; WORLD_HEIGHT = SCREEN_HEIGHT * 2
    # Skalierte Schriftgrößen
    ui_fs = max(12, int(SCREEN_HEIGHT * (BASE_UI_FONT_SIZE / FONT_SIZE_REF_H)))
    btn_fs = max(10, int(SCREEN_HEIGHT * (BASE_BUTTON_FONT_SIZE / FONT_SIZE_REF_H)))
    inv_fs = max(8, int(SCREEN_HEIGHT * (BASE_INV_QTY_FONT_SIZE / FONT_SIZE_REF_H)))
    dlg_fs = max(14, int(SCREEN_HEIGHT * (BASE_DIALOG_FONT_SIZE / FONT_SIZE_REF_H)))
    shp_fs = max(10, int(SCREEN_HEIGHT * (BASE_SHOP_FONT_SIZE / FONT_SIZE_REF_H)))
    # Fonts erstellen
    try:
        ui_font = pygame.font.Font(None, ui_fs)
        button_font = pygame.font.Font(None, btn_fs)
        inventory_font = pygame.font.Font(None, inv_fs)
        dialog_font = pygame.font.Font(None, dlg_fs)
        shop_font = pygame.font.Font(None, shp_fs)
        logger.info(f"Fonts erstellt.")
    except Exception:
        logger.exception("Font Fehler:")
        # Fallback Fonts
        ui_font, button_font, inventory_font, dialog_font, shop_font = (
            pygame.font.Font(None, s) for s in [28, 18, 16, 24, 18]
        )
    # Button und Inventar Geometrie
    BTN_DEF_W = int(SCREEN_WIDTH * BUTTON_DEFAULT_WIDTH_PERCENT)
    BTN_DEF_H = int(SCREEN_HEIGHT * BUTTON_DEFAULT_HEIGHT_PERCENT)
    BUTTON_RECT = pygame.Rect(BUTTON_X, 0, BTN_DEF_W, BTN_DEF_H) # Y wird später gesetzt
    inv_w = MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING
    CENTERED_INVENTORY_X_POS = (SCREEN_WIDTH - inv_w) // 2
    CENTERED_INVENTORY_Y_POS = SCREEN_HEIGHT - SCALED_BOX_SIZE - INVENTORY_BOTTOM_PADDING
    logger.info("Inventar Pos berechnet.")

    # Assets laden
    logger.info("Lade Assets...")
    item_icons, placed_item_images, fallback_placed_image = items.load_item_assets(
        IMAGE_FOLDER, PLACED_ITEM_SIZE, SCALED_ICON_SIZE, load_image_asset
    )
    background_image = load_image_asset(BACKGROUND_FILENAME, alpha=False)
    if background_image and background_image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
        try:
            background_image = pygame.transform.smoothscale(background_image,(SCREEN_WIDTH,SCREEN_HEIGHT))
            logger.info("BG skaliert.")
        except Exception:
            logger.exception("BG Skalierung fehlgeschlagen:"); background_image = None
    button_image_normal = load_image_asset(BUTTON_FILENAME, alpha=True)
    money_slot_background_img = load_image_asset(MONEY_ICON_FILENAME, alpha=True,
                                             scale_to=(SCALED_BOX_SIZE, SCALED_BOX_SIZE))
    if not money_slot_background_img:
        logger.warning(f"'{MONEY_ICON_FILENAME}' nicht geladen.")

    # Spielobjekte erstellen (inkl. Laden)
    player_start_x=WORLD_WIDTH//2; player_start_y=WORLD_HEIGHT//2
    player_radius=TILE_SIZE//3; spawn_x,spawn_y=player_start_x,player_start_y
    player_money = 0.0
    loaded_player_data = load_data(PLAYER_POS_SAVE_FILE) # Laden von Pos & Geld
    if isinstance(loaded_player_data, dict):
        try:
            spawn_x=int(loaded_player_data.get('x',spawn_x))
            spawn_y=int(loaded_player_data.get('y',spawn_y))
        except ValueError: logger.warning("Ungültige Pos-Daten.")
        try:
            player_money=float(loaded_player_data.get('money',player_money))
        except ValueError: logger.warning("Ungültige Money-Daten.")
    else: logger.info("Keine Spielerdatei. Standardwerte.")
    player = Player(spawn_x, spawn_y, player_radius, RED)
    logger.info(f"Spieler erstellt bei ({spawn_x},{spawn_y}), Geld: {player_money:.2f}")

    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
    cam_x = max(0, min(player.rect.centerx - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
    cam_y = max(0, min(player.rect.centery - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))
    camera.camera_rect.topleft = (cam_x, cam_y); logger.info("Kamera ausgerichtet.")

    inventory = Inventory(filepath=INVENTORY_SAVE_FILE); logger.info("Inventar erstellt/geladen.")
    if not inventory.has_item("Blumentopf"): inventory.add_item("Blumentopf", 3) # etc.

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
                    images=placed_item_images.get(item_type, {}); fallback=fallback_placed_image
                    new=items.PlacedItem(item_x,item_y,item_type,images,fallback,GROW_TIME_SECONDS,item_state,item_timer)
                    if new.rect: all_sprites.add(new); placed_items.add(new); loaded_item_count+=1
                    else: logger.error(f"PlacedItem Laden Fehler: {item_data}")
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Ungültiger Item-Eintrag: {item_data} -> {e}", exc_info=True)
            else: logger.warning(f"Ungültiger Typ in {PLACED_ITEMS_FILENAME}: {type(item_data)}")
        logger.info(f"{loaded_item_count} Items geladen.")
    else: logger.warning(f"'{PLACED_ITEMS_FILENAME}' war keine Liste.")

    npc_radius=TILE_SIZE//3
    npc_g=NPC(WORLD_WIDTH-TILE_SIZE*10,TILE_SIZE*15,npc_radius,GREEN,"generic","generic_hallo")
    npc_m=NPC(2400, 1000, npc_radius, BLUE, "merchant", "händler_start")
    all_sprites.add(player, npc_g, npc_m); npcs.add(npc_g, npc_m)
    logger.debug("NPCs hinzugefügt.")

    # UI & Button Rect anpassen
    if platform_utils.IS_ANDROID and button_image_normal:
        btn_w_act,btn_h_act = button_image_normal.get_size()
    else: btn_w_act,btn_h_act = BTN_DEF_W,BTN_DEF_H
    BUTTON_Y=CENTERED_INVENTORY_Y_POS - btn_h_act - BUTTON_PADDING
    BUTTON_RECT.size=(btn_w_act,btn_h_act); BUTTON_RECT.topleft=(BUTTON_X,BUTTON_Y)
    logger.debug(f"Button Rect: {BUTTON_RECT}")

    if platform_utils.IS_ANDROID:
        platform_utils.set_android_immersive_mode(); logger.info("Immersive Mode.")

except Exception as e:
    logger.critical("Init/Setup Fehler", exc_info=True); pygame.quit(); sys.exit()


# === Spiel-Loop ===
running = True; logger.info("Spiel-Loop startet.")
while running:
    try:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos_screen = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # --- Nur im Play-Zustand Updates & Interaktionsziel ---
        if current_game_state == GAME_STATE_PLAY:
            # Interaktionsziel finden
            closest_target=None; min_dist_sq=(INTERACTION_RADIUS*1.1)**2
            player_cx=player.rect.centerx; player_cy=player.rect.centery; closest_type=None
            # Items
            for item in placed_items:
                dist_sq=(player_cx-item.rect.centerx)**2+(player_cy-item.rect.centery)**2
                if dist_sq<min_dist_sq: min_dist_sq=dist_sq; closest_target=item; closest_type="item"
            # NPCs
            for npc_obj in npcs:
                 dist_sq=(player_cx-npc_obj.rect.centerx)**2+(player_cy-npc_obj.rect.centery)**2
                 if dist_sq<min_dist_sq: min_dist_sq=dist_sq; closest_target=npc_obj; closest_type="npc"
            potential_interaction_target=closest_target; target_type=closest_type
            interaction_possible_now=potential_interaction_target is not None
            # Ziel verloren?
            if interaction_active and potential_interaction_target!=closest_target:
                logger.debug("Ziel verloren.")
                potential_interaction_target=None; interaction_start_time=0.0
                interaction_active=False; target_type=None
            # Updates
            player.update(keys, camera.get_current_screen_rect())
            camera.update(player)
            npcs.update()
            placed_items.update(dt)
            # Aufheben (Langes Halten)
            if (interaction_active and target_type=="item" and potential_interaction_target and
                time.time() - interaction_start_time >= LONG_PRESS_THRESHOLD):
                item_type=potential_interaction_target.item_type
                logger.info(f"Pickup '{item_type}'")
                if inventory.add_item(item_type, 1):
                    logger.info(f"'{item_type}' zum Inventar.")
                    potential_interaction_target.kill(); logger.info("Item entfernt.")
                else: logger.warning("Aufheben fehlgeschlagen: Inventar voll?")
                # Interaktion immer beenden nach Aufheben
                potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False

        # --- Event Handling (Alle Zustände) ---
        interaction_press_event_handled = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False; logger.info("QUIT Event.")

            # --- Keyboard Events ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC im Dialog/Shop: Zurück zum Spiel
                    if current_game_state in [GAME_STATE_DIALOG, GAME_STATE_SHOP]:
                        logger.info("ESC: Zurück zum Spiel.")
                        current_game_state=GAME_STATE_PLAY; active_npc=None; current_dialog_node_id=None
                    # ESC im Spiel (Nicht-Android): Zurück zum Hauptmenü
                    elif not platform_utils.IS_ANDROID:
                        logger.info("ESC: Zurück zum Menü...")
                        save_game_state(); pygame.quit(); logger.info("Game beendet.")
                        try:
                            args=[sys.executable, MAIN_SCRIPT_PATH]; logger.info(f"Exec: {args}")
                            os.execv(sys.executable, args)
                        except Exception as e: logger.critical("Exec Fehler", exc_info=True); sys.exit(1)

                # Leertaste Interaktion Start (Play State, Nicht-Android)
                elif (event.key == pygame.K_SPACE and
                      current_game_state == GAME_STATE_PLAY and
                      not platform_utils.IS_ANDROID):
                    if not interaction_active and interaction_possible_now:
                        interaction_active=True; interaction_press_event_handled=True
                        interaction_start_time=time.time()
                        target_name=getattr(potential_interaction_target, 'item_type',
                                            getattr(potential_interaction_target, 'npc_type', '?'))
                        logger.info(f"Start Interaktion (SPACE) mit {target_type} '{target_name}'")

            elif event.type == pygame.KEYUP:
                 # Leertaste Loslassen -> Kurze Interaktion (Play State, Nicht-Android)
                 if (event.key == pygame.K_SPACE and
                     current_game_state == GAME_STATE_PLAY and
                     not platform_utils.IS_ANDROID):
                     if interaction_active and potential_interaction_target:
                         # Prüfe ob Druck kurz war
                         if time.time() - interaction_start_time < LONG_PRESS_THRESHOLD:
                             logger.debug(f"Kurz (SPACE) auf {target_type}")
                             if target_type == "item": # --- Item Interaktion ---
                                 item = potential_interaction_target
                                 logger.debug(f"-> Aktion {item.state}")
                                 if item.state == 'ohneErde': # Minispiel starten
                                     req="Sack Erde"; has=inventory.has_item(req, 1); logger.debug(f"Check '{req}': {has}")
                                     if has and inventory.remove_item(req, 1):
                                         logger.info(f"'{req}' verbraucht. Starte Minispiel...")
                                         save_game_state(); success = False
                                         try:
                                             result=subprocess.run([sys.executable, MINIGAME_GROW1_PATH],
                                                                   capture_output=True, text=True, check=False,
                                                                   cwd=project_root_dir)
                                             logger.info(f"Minispiel Ende. RC={result.returncode}.")
                                             if result.returncode == 0: success = True
                                             else: logger.warning(f"Minispiel nicht OK (RC={result.returncode}).")
                                         except FileNotFoundError: logger.error(f"Minispiel Skript fehlt: {MINIGAME_GROW1_PATH}")
                                         except Exception: logger.exception("Fehler Ausführung Minispiel:")
                                         if success:
                                             logger.info("Minispiel OK! -> 'ohneSeed'.")
                                             item.state = 'ohneSeed'; item.update_appearance()
                                         else: logger.info("Minispiel nicht OK.")
                                     elif has: logger.error(f"Konnte '{req}' nicht entfernen?")
                                     else: logger.info(f"Fehlt: '{req}'.")
                                 elif item.state == 'ohneSeed': # Samen setzen
                                     req="Weed Seeds"; ok=False
                                     if inventory.has_item(req,1) and inventory.remove_item(req,1): ok=True; logger.info(f"'{req}' verbraucht.")
                                     else: logger.info(f"Fehlt: '{req}'.")
                                     if ok: item.interact()
                                 elif item.state in ['giessen','readyToEarn','growing']: item.interact() # Giessen/Ernten
                             elif target_type == "npc": # --- NPC Interaktion ---
                                 active_npc=potential_interaction_target; logger.info(f"Interagiere mit NPC '{active_npc.npc_type}'")
                                 if active_npc.dialog_id:
                                     current_dialog_node_id=active_npc.dialog_id
                                     current_game_state=GAME_STATE_DIALOG
                                     logger.info(f"-> DIALOG (Start: {current_dialog_node_id})")
                                 else: logger.warning("NPC hat keine Dialog-ID."); active_npc=None
                         # Reset Interaktion nach Loslassen (egal ob kurz/lang)
                         potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False; target_type=None

            # --- Maus Events ---
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_game_state == GAME_STATE_PLAY:
                    # Android Button Interaktion Start
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
                            slot_x=CENTERED_INVENTORY_X_POS+i*(SCALED_BOX_SIZE+SCALED_PADDING)
                            slot_y=CENTERED_INVENTORY_Y_POS
                            slot_rect=pygame.Rect(slot_x,slot_y,SCALED_BOX_SIZE,SCALED_BOX_SIZE)
                            if slot_rect.collidepoint(mouse_pos_screen) and i<len(inv_list):
                                try:
                                    name_t, qty_t = inv_list[i]
                                    logger.debug(f"Slot {i} C: '{name_t}', Q:{qty_t}")
                                    # Prüfe ob Item ziehbar ist
                                    if name_t=="Blumentopf" and qty_t>0:
                                        is_dragging=True; dragged_item_type="Blumentopf"
                                        img_key='ohneErde'
                                        dragged_item_image=placed_item_images.get("Blumentopf",{}).get(img_key,fallback_placed_image)
                                        logger.info(f"Starte Drag: {dragged_item_type}"); break
                                except ValueError: logger.exception(f"Inv unpack Error:{inv_list[i]}")
                                except Exception as e: logger.exception(f"Drag Start Error:{e}")

                elif current_game_state == GAME_STATE_DIALOG: # Dialog Klick
                    for i,rect in enumerate(dialog_response_rects):
                        if rect.collidepoint(mouse_pos_screen):
                            logger.debug(f"Dialog Antwort {i}."); node=dialog.get_dialog_node(current_dialog_node_id)
                            if node and i<len(node["responses"]):
                                r=node["responses"][i]; a=r.get("action"); n=r.get("next_node")
                                if a=="open_shop": logger.info("Aktion: Shop."); current_game_state=GAME_STATE_SHOP
                                elif a=="end_dialog": logger.info("Aktion: Ende."); current_game_state=GAME_STATE_PLAY; current_dialog_node_id=None; active_npc=None
                                elif n: logger.info(f"-> Dialog: {n}"); current_dialog_node_id=n
                                elif not a: logger.info("Keine Aktion->Ende."); current_game_state=GAME_STATE_PLAY; current_dialog_node_id=None; active_npc=None
                            break # Nur eine Antwort

                elif current_game_state == GAME_STATE_SHOP: # Shop Klick
                    item_clicked=False; available=shop_items.get_available_items()
                    # Prüfe Klick auf Items
                    for i, rect in enumerate(shop_item_rects):
                        if rect.collidepoint(mouse_pos_screen):
                            item_clicked=True; logger.debug(f"Shop Slot {i}.")
                            if i<len(available):
                                item_buy=available[i]; name=item_buy["name"]; price=item_buy["price"]
                                logger.info(f"Kaufversuch:'{name}'({price:.2f}).")
                                if player_money>=price:
                                    if inventory.add_item(name,1): player_money-=price; logger.info(f"Gekauft! Neu:{player_money:.2f}")
                                    else: logger.warning("Inventar voll?")
                                else: logger.warning("Zu wenig Geld.")
                            else: logger.error(f"Shop-Klick Fehler: Index {i}")
                            break # Klick auf Slot verarbeitet
                    # Prüfe Klick auf Exit Button (nur wenn kein Item geklickt wurde)
                    if not item_clicked and shop_exit_button_rect and shop_exit_button_rect.collidepoint(mouse_pos_screen):
                        logger.info("Shop -> Spiel."); current_game_state=GAME_STATE_PLAY; active_npc=None; current_dialog_node_id=None

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: # Linksklick Loslassen
                if current_game_state == GAME_STATE_PLAY:
                    # Android Button Loslassen -> Kurze Interaktion
                    if platform_utils.IS_ANDROID and interaction_active:
                        logger.debug("Android Button losgelassen")
                        if potential_interaction_target and time.time()-interaction_start_time<LONG_PRESS_THRESHOLD:
                            logger.debug(f"Kurz (Button) auf {target_type}")
                            if target_type=="item": # Item Interaktion (Android)
                                item=potential_interaction_target; logger.debug(f"-> Aktion {item.state}")
                                if item.state=='ohneErde': # Minispiel Start
                                    req="Sack Erde"; has=inventory.has_item(req,1); logger.debug(f"Android Check '{req}': {has}")
                                    if has and inventory.remove_item(req,1):
                                        logger.info(f"'{req}' verbraucht (A). Starte Minispiel..."); save_game_state(); success=False;
                                        try:
                                            result=subprocess.run([sys.executable,MINIGAME_GROW1_PATH],capture_output=True,text=True,check=False,cwd=project_root_dir)
                                            logger.info(f"Minispiel (A) Ende. RC={result.returncode}.")
                                            if result.returncode==0: success=True
                                            else: logger.warning(f"Minispiel (A) nicht OK (RC={result.returncode}).")
                                        except Exception: logger.exception("Fehler Minispiel (A):")
                                        if success: logger.info("Minispiel (A) OK! -> 'ohneSeed'."); item.state='ohneSeed'; item.update_appearance()
                                        else: logger.info("Minispiel (A) nicht OK.")
                                    elif has: logger.error("Konnte '{req}' nicht entfernen (A)?")
                                    else: logger.info(f"Fehlt: '{req}' (A).")
                                elif item.state=='ohneSeed': req="Weed Seeds"; ok=False; 
                                if inventory.has_item(req,1) and inventory.remove_item(req,1): ok=True; logger.info(f"'{req}' verbraucht.") 
                                else: logger.info(f"Fehlt: '{req}'."); 
                                if ok: item.interact()
                                elif item.state in ['giessen','readyToEarn','growing']: item.interact() # Giessen/Ernten
                            elif target_type=="npc": # NPC Interaktion
                                active_npc=potential_interaction_target; logger.info(f"Interagiere mit NPC '{active_npc.npc_type}'");
                                if active_npc.dialog_id: current_dialog_node_id=active_npc.dialog_id; current_game_state=GAME_STATE_DIALOG; logger.info(f"-> DIALOG (Start: {current_dialog_node_id})")
                                else: logger.warning("NPC hat keine Dialog-ID."); active_npc=None
                        potential_interaction_target=None; interaction_start_time=0.0; interaction_active=False; target_type=None # Reset
                    # Drag Ende
                    elif is_dragging:
                         world_x,world_y=camera.screen_to_world(mouse_pos_screen[0],mouse_pos_screen[1])
                         snapped_tl_x=(world_x//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE; snapped_tl_y=(world_y//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE
                         snapped_center_x=snapped_tl_x+PLACED_ITEM_SIZE/2; snapped_center_y=snapped_tl_y+PLACED_ITEM_SIZE/2
                         can_place=True; temp_rect=pygame.Rect(snapped_tl_x,snapped_tl_y,PLACED_ITEM_SIZE,PLACED_ITEM_SIZE)
                         for item in placed_items:
                             if temp_rect.colliderect(item.rect): can_place=False; logger.info("Platzieren blockiert."); break
                         if can_place:
                             if inventory.remove_item(dragged_item_type,1):
                                 images=placed_item_images.get(dragged_item_type,{})
                                 fallback=fallback_placed_image
                                 new_item=items.PlacedItem(snapped_center_x,snapped_center_y,dragged_item_type,images,fallback,GROW_TIME_SECONDS,state='ohneErde')
                                 if new_item.rect: all_sprites.add(new_item); placed_items.add(new_item); logger.info(f"'{dragged_item_type}' platziert.")
                                 else: logger.error("Fehler PlacedItem Erstellung!"); inventory.add_item(dragged_item_type,1)
                             else: logger.warning("Platzieren fehlgeschlagen (Inventar?)")
                         is_dragging=False; dragged_item_type=None; dragged_item_image=None # Immer Drag beenden

        # --- Draw ---
        # 1. Spielwelt (nur Play State)
        if current_game_state == GAME_STATE_PLAY:
            if background_image: screen.blit(background_image, (0,0)) 
            else: screen.fill(BLACK)
            # Sprites zeichnen
            for sprite in all_sprites:
                if camera.get_current_screen_rect().colliderect(sprite.rect):
                    screen.blit(sprite.image, camera.apply(sprite))
            # Interaktions-UI
            if interaction_active and potential_interaction_target:
                 try:
                     p_rect_s=camera.apply(player); c_s=p_rect_s.center
                     pygame.draw.circle(screen,WHITE,c_s,int(INTERACTION_RADIUS),1)
                     # Fortschrittsbalken (nur für Items)
                     if interaction_start_time>0 and target_type=="item":
                         hold_dur=time.time()-interaction_start_time; prog=min(1.0,hold_dur/LONG_PRESS_THRESHOLD);
                         if prog>0:
                             bar_w=50;bar_h=5;bar_x=c_s[0]-bar_w//2;bar_y=p_rect_s.top-bar_h-5
                             pygame.draw.rect(screen,(50,50,50),(bar_x,bar_y,bar_w,bar_h))
                             pygame.draw.rect(screen,RED,(bar_x,bar_y,int(bar_w*prog),bar_h))
                 except Exception: logger.exception("Zeichenfehler Interaktion:")
            # UI Text
            try:
                if ui_font:
                    pos_txt=f"P({player.rect.x},{player.rect.y}) C({camera.camera_rect.x},{camera.camera_rect.y})"
                    surf=ui_font.render(pos_txt,True,WHITE); screen.blit(surf,(10,10))
            except Exception: logger.exception("Zeichenfehler UI-Text:")
            # Inventar + Geld zeichnen
            try:
                inv_list=inventory.get_item_list_for_display()
                for i in range(MAX_SLOTS):
                    slot_x=CENTERED_INVENTORY_X_POS+i*(SCALED_BOX_SIZE+SCALED_PADDING)
                    slot_y=CENTERED_INVENTORY_Y_POS
                    slot_rect=pygame.Rect(slot_x,slot_y,SCALED_BOX_SIZE,SCALED_BOX_SIZE)
                    # Geld-Slot (letzter Slot)
                    if i == MAX_SLOTS-1:
                        if money_slot_background_img: screen.blit(money_slot_background_img,slot_rect.topleft)
                        else: pygame.draw.rect(screen,(100,100,100,180),slot_rect) # Fallback BG
                        pygame.draw.rect(screen,WHITE,slot_rect,2) # Rand
                        if inventory_font:
                            try: money_txt=locale.currency(player_money,grouping=True)
                            except: money_txt=f"{player_money:.2f}" # Fallback Format
                            m_surf=inventory_font.render(money_txt,True,GREEN)
                            m_rect=m_surf.get_rect(center=slot_rect.center)
                            screen.blit(m_surf,m_rect)
                    # Item Slot (alle anderen)
                    elif i<len(inv_list):
                        pygame.draw.rect(screen,(100,100,100,180),slot_rect) # BG
                        pygame.draw.rect(screen,WHITE,slot_rect,2) # Rand
                        name,qty=inv_list[i]; icon_surf=item_icons.get(name)
                        if icon_surf: # Icon
                            i_rect=icon_surf.get_rect(center=slot_rect.center); screen.blit(icon_surf,i_rect)
                        else: # Text Fallback
                            if inventory_font:
                                fb_surf=inventory_font.render(name,True,WHITE)
                                fb_rect=fb_surf.get_rect(center=slot_rect.center)
                                screen.blit(fb_surf,fb_rect)
                        if qty>0 and inventory_font: # Menge
                            q_surf=inventory_font.render(str(qty),True,WHITE)
                            q_rect=q_surf.get_rect(bottomright=(slot_rect.right-SCALED_PADDING//2, slot_rect.bottom-SCALED_PADDING//2))
                            screen.blit(q_surf,q_rect)
                    # Leerer Slot
                    else:
                        pygame.draw.rect(screen,(100,100,100,180),slot_rect)
                        pygame.draw.rect(screen,WHITE,slot_rect,2)
            except Exception: logger.exception("Fehler Inventar-Anzeige:")
            # Drag Preview
            if is_dragging and dragged_item_image:
                world_x,world_y = camera.screen_to_world(*mouse_pos_screen)
                snapped_tl_x=(world_x//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE
                snapped_tl_y=(world_y//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE
                temp_rect_w=pygame.Rect(snapped_tl_x,snapped_tl_y,PLACED_ITEM_SIZE,PLACED_ITEM_SIZE)
                snapped_rect_s=camera.apply_rect(temp_rect_w)
                drag_rect=dragged_item_image.get_rect(center=snapped_rect_s.center)
                screen.blit(dragged_item_image,drag_rect)
                pygame.draw.rect(screen,WHITE,snapped_rect_s,1)
            # Android Button
            if platform_utils.IS_ANDROID:
                if button_image_normal: screen.blit(button_image_normal, BUTTON_RECT.topleft)
                else: pygame.draw.rect(screen,BUTTON_COLOR_NORMAL,BUTTON_RECT); pygame.draw.rect(screen,BUTTON_BORDER_COLOR,BUTTON_RECT,2)
                if not button_image_normal and pygame.font.get_init() and button_font:
                    try: btn_surf=button_font.render("Interact",True,WHITE); btn_rect=btn_surf.get_rect(center=BUTTON_RECT.center); screen.blit(btn_surf,btn_rect)
                    except Exception as e: logger.error(f"Fehler Button-Text:{e}",exc_info=True)

        # 2. Dialog-UI
        elif current_game_state == GAME_STATE_DIALOG:
             dialog_response_rects.clear(); node = dialog.get_dialog_node(current_dialog_node_id)
             if node and dialog_font:
                 # Panel
                 dlg_h=SCREEN_HEIGHT//3; dlg_rect=pygame.Rect(0,SCREEN_HEIGHT-dlg_h,SCREEN_WIDTH,dlg_h)
                 pygame.draw.rect(screen,DARK_BLUE,dlg_rect); pygame.draw.rect(screen,WHITE,dlg_rect,3)
                 # NPC Text
                 npc_txt_rect=pygame.Rect(dlg_rect.left+20,dlg_rect.top+20,dlg_rect.width-40,dlg_rect.height//2-30)
                 wrap_text(screen,node["npc_text"],dialog_font,WHITE,npc_txt_rect)
                 # Antworten
                 resp_y=npc_txt_rect.bottom+15; resp_h=35; resp_sp=10; btn_w=dlg_rect.width//2-30
                 for i,response in enumerate(node["responses"]):
                     btn_x=dlg_rect.left+20; btn_y=resp_y+i*(resp_h+resp_sp)
                     resp_rect=pygame.Rect(btn_x,btn_y,btn_w,resp_h); dialog_response_rects.append(resp_rect)
                     # Button zeichnen
                     hover=resp_rect.collidepoint(mouse_pos_screen); btn_col=LIGHT_GREY if hover else GREY
                     pygame.draw.rect(screen,btn_col,resp_rect); pygame.draw.rect(screen,WHITE,resp_rect,1)
                     # Text
                     resp_surf=dialog_font.render(response["text"],True,BLACK)
                     resp_rect_txt=resp_surf.get_rect(center=resp_rect.center); screen.blit(resp_surf,resp_rect_txt)
             else:
                 logger.error(f"Dialog-Knoten '{current_dialog_node_id}' Fehler.")
                 current_game_state=GAME_STATE_PLAY; active_npc=None; current_dialog_node_id=None

        # 3. Shop-UI
        elif current_game_state == GAME_STATE_SHOP:
            shop_item_rects.clear(); margin=50
            shop_rect=pygame.Rect(margin,margin,SCREEN_WIDTH-2*margin,SCREEN_HEIGHT-2*margin)
            pygame.draw.rect(screen,DARK_BLUE,shop_rect); pygame.draw.rect(screen,WHITE,shop_rect,3)
            # Titel
            if ui_font: title_surf=ui_font.render("Shop",True,YELLOW); title_rect=title_surf.get_rect(centerx=shop_rect.centerx,top=shop_rect.top+15); screen.blit(title_surf,title_rect)
            # Geld
            if inventory_font:
                try: money_txt_shop=locale.currency(player_money,grouping=True)
                except: money_txt_shop=f"{player_money:.2f}"
                m_surf_s=inventory_font.render(f"Geld: {money_txt_shop}",True,GREEN)
                m_rect_s=m_surf_s.get_rect(right=shop_rect.right-20,top=shop_rect.top+20); screen.blit(m_surf_s,m_rect_s)
            # Item Grid
            cols=4; rows=8; shop_list=shop_items.get_available_items()
            grid_x=shop_rect.left+30; grid_y=shop_rect.top+70
            cell_w=(shop_rect.width-60)//cols; cell_h=(shop_rect.height-120)//rows # Platz für Exit
            icon_size=min(cell_w//2,cell_h//2) # Icon Größe für Shop
            for i,item_data in enumerate(shop_list):
                if i>=cols*rows: break # Grid voll
                row=i//cols; col=i%cols
                cell_x=grid_x+col*cell_w; cell_y=grid_y+row*cell_h
                cell_rect=pygame.Rect(cell_x,cell_y,cell_w-10,cell_h-10); shop_item_rects.append(cell_rect)
                # Zelle zeichnen
                hover=cell_rect.collidepoint(mouse_pos_screen); cell_col=LIGHT_GREY if hover else GREY
                pygame.draw.rect(screen,cell_col,cell_rect); pygame.draw.rect(screen,WHITE,cell_rect,1)
                # Icon
                name=item_data["name"]; s_icon=load_image_asset(items.ICON_FILES.get(name),alpha=True,scale_to=(icon_size,icon_size))
                if s_icon: i_rect=s_icon.get_rect(centerx=cell_rect.centerx,top=cell_rect.top+5); screen.blit(s_icon,i_rect)
                # Preis
                if shop_font:
                    try: price_txt=locale.currency(item_data["price"],grouping=True)
                    except: price_txt=f"{item_data['price']:.2f}"
                    p_surf=shop_font.render(price_txt,True,YELLOW)
                    p_rect=p_surf.get_rect(centerx=cell_rect.centerx,bottom=cell_rect.bottom-5); screen.blit(p_surf,p_rect)
            # Exit Button
            exit_w=100; exit_h=40; exit_x=shop_rect.centerx-exit_w//2; exit_y=shop_rect.bottom-exit_h-15
            shop_exit_button_rect=pygame.Rect(exit_x,exit_y,exit_w,exit_h)
            hover=shop_exit_button_rect.collidepoint(mouse_pos_screen); exit_col=RED if hover else DARK_BLUE
            pygame.draw.rect(screen,exit_col,shop_exit_button_rect); pygame.draw.rect(screen,WHITE,shop_exit_button_rect,2)
            if button_font: # Reuse button_font
                 exit_surf=button_font.render("Verlassen",True,WHITE)
                 exit_rect=exit_surf.get_rect(center=shop_exit_button_rect.center); screen.blit(exit_surf,exit_rect)

        # Flip am Ende der Draw-Sektion
        pygame.display.flip()

    # Fehler in der Hauptschleife abfangen
    except Exception as e_game_loop:
        logger.critical("Unerwarteter Fehler in Spielschleife:", exc_info=True)
        running = False # Beende bei schwerem Fehler

# --- Spiel beenden ---
logger.info("Spiel-Loop beendet.")
save_game_state() # Spielstand speichern
if pygame.get_init():
    pygame.quit(); logger.info("Pygame beendet.")
else: logger.info("Pygame war bereits beendet.")
sys.exit()