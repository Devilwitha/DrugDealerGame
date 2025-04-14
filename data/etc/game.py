# game.py (ESC startet main.py neu, mit Speichern)
import pygame
import sys
import logging
import os
import math
import time
import traceback

# --- Logging Konfiguration ---
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
log_level = logging.DEBUG
date_fmt = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=log_level, format=log_format, datefmt=date_fmt)
logger = logging.getLogger(__name__)

# --- Pfade ---
try: script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError: script_dir = os.path.abspath(".")
project_root_dir = os.path.normpath(os.path.join(script_dir, "..", "..")) # Wichtig für main.py Pfad
data_dir_root = os.path.join(project_root_dir, "data")
log_dir = os.path.join(data_dir_root, "logs")
IMAGE_FOLDER = os.path.join(data_dir_root, "bilder")
SAVE_DATA_DIR_ABS = os.path.join(data_dir_root, "savedata")
SETTINGS_DIR = os.path.join(data_dir_root, "settings")
SETTINGS_FILE_PATH = os.path.join(SETTINGS_DIR, "settings.json")
MAIN_SCRIPT_PATH = os.path.join(project_root_dir, "main.py") # NEU: Pfad zu main.py

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
    logger.info(f"File logging für game.py initialisiert. Log-Datei: {log_file_path}")
except Exception as e_log_setup: logger.error(f"Fehler File Logging: {e_log_setup}", exc_info=True)

logger.info("Spiel wird initialisiert...")
logger.debug(f"Game Script Verzeichnis: {script_dir}")
logger.debug(f"Root Verzeichnis: {project_root_dir}")
logger.debug(f"Bild-Ordner: {IMAGE_FOLDER}"); logger.debug(f"Speicher-Ordner: {SAVE_DATA_DIR_ABS}"); logger.debug(f"Settings-Datei Pfad: {SETTINGS_FILE_PATH}"); logger.debug(f"Main Script Pfad: {MAIN_SCRIPT_PATH}")


# --- Eigene Module importieren ---
try:
    import platform_utils
    from player import Player
    from npc import NPC
    from camera import Camera
    from inventory import Inventory, BOX_SIZE, PADDING, MAX_SLOTS
    from persistence import load_data, save_data
    import settings_utils
    logger.info("Eigene Module importiert.")
except ImportError as e: logger.critical(f"Fehler Import Modul: {e}.", exc_info=True); sys.exit()
except Exception as e: logger.critical(f"Unerwarteter Import-Fehler: {e}", exc_info=True); sys.exit()

# --- Einstellungen laden ---
try:
    current_settings = settings_utils.load_settings(SETTINGS_FILE_PATH)
    logger.info(f"Einstellungen geladen: {current_settings}")
except Exception as e_load_settings:
    logger.error(f"FEHLER beim Laden der Einstellungen: {e_load_settings}", exc_info=True)
    current_settings = {'music_volume': 0.5, 'sfx_volume': 0.5, 'master_volume': 0.5}
    logger.warning(f"Fallback-Einstellungen werden verwendet: {current_settings}")

# --- Konstanten ---
TILE_SIZE = 32; FPS = 60
WHITE = (255, 255, 255); 
BLACK = (0, 0, 0); 
GREEN = (0, 255, 0); 
RED = (255, 0, 0); 
BLUE = (0, 0, 255); 
MAGENTA = (255, 0, 255)
PLACED_ITEM_SIZE = TILE_SIZE
INTERACTION_RADIUS = TILE_SIZE; 
LONG_PRESS_THRESHOLD = 1.0; 
GROW_TIME_SECONDS = 10
INVENTORY_SCALE_FACTOR = 2.0; 
SCALED_BOX_SIZE = int(BOX_SIZE * INVENTORY_SCALE_FACTOR); 
SCALED_PADDING = int(PADDING * INVENTORY_SCALE_FACTOR); 
SCALED_ICON_SIZE = (SCALED_BOX_SIZE - SCALED_PADDING * 2, SCALED_BOX_SIZE - SCALED_PADDING * 2);
logger.debug(f"Berechnete SCALED_ICON_SIZE: {SCALED_ICON_SIZE}"); 
INVENTORY_BOTTOM_PADDING = 20
BUTTON_DEFAULT_WIDTH_PERCENT = 0.08; 
BUTTON_DEFAULT_HEIGHT_PERCENT = 0.13; 
BUTTON_PADDING = 15; 
BUTTON_X = BUTTON_PADDING; 
BUTTON_COLOR_NORMAL = (80, 80, 80); 
BUTTON_BORDER_COLOR = WHITE
FONT_SIZE_REF_H = 600.0; 
BASE_UI_FONT_SIZE = 28; 
BASE_BUTTON_FONT_SIZE = 18; 
BASE_INV_QTY_FONT_SIZE = 16

# --- Asset-Dateinamen ---
BACKGROUND_FILENAME = "background.png"; 
BUTTON_FILENAME = "interact_button.png"
ICON_FILES = {
    "Blumentopf":"blumentopf_icon.png",
    "Sack Erde":"sack_erde_icon.png", 
    "Weed Seeds":"item_weed_seeds.png"
    }
PLACED_ITEM_STATE_FILES = {
    "Blumentopf": {
        'ohneErde': "blumentopf_ohneErde.png", 
        'ohneSeed': "blumentopf_ohneSeed.png", 
        'giessen': "blumentopf_giessen.png", 
        'growing': "blumentopf_growing.png", 
        'readyToEarn': "blumentopf_ready.png"
        }
    }
INVENTORY_FILENAME="inventar.json"; INVENTORY_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, INVENTORY_FILENAME)
PLAYER_POS_FILENAME="player_position.json"; PLAYER_POS_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, PLAYER_POS_FILENAME)
PLACED_ITEMS_FILENAME="placed_items.json"; PLACED_ITEMS_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, PLACED_ITEMS_FILENAME)

# --- Asset Ladefunktion ---
def load_image_asset(filename, alpha=True, scale_to=None):
    path = os.path.join(IMAGE_FOLDER, filename)
    try: image = pygame.image.load(path); image = image.convert_alpha() if alpha else image.convert()
    except Exception as e_load: logger.error(f"Fehler Laden Bild '{path}': {e_load}", exc_info=True); return None
    if scale_to:
        if scale_to[0] <= 0 or scale_to[1] <= 0: logger.error(f"Ungültige Skalierungsgröße für '{filename}': {scale_to}. Skalierung übersprungen.")
        else:
            try: image = pygame.transform.smoothscale(image, scale_to)
            except Exception as e_scale: logger.error(f"Fehler Skalieren '{filename}' zu {scale_to}: {e_scale}", exc_info=True)
    return image

# --- PlacedItem Klasse ---
class PlacedItem(pygame.sprite.Sprite):
    STATES = ['ohneErde', 'ohneSeed', 'giessen', 'growing', 'readyToEarn']
    def __init__(self, world_x, world_y, item_type, images_for_states, fallback_image, state='ohneErde', timer_end_timestamp=None):
        super().__init__()
        self.item_type = item_type; self.images_for_states = images_for_states
        self.fallback_image = fallback_image if fallback_image else pygame.Surface((PLACED_ITEM_SIZE, PLACED_ITEM_SIZE))
        if not fallback_image: self.fallback_image.fill(MAGENTA)
        self.state = state if state in self.STATES else 'ohneErde'
        try: self.timer_end_timestamp = float(timer_end_timestamp) if timer_end_timestamp else None
        except: self.timer_end_timestamp = None; logger.warning(f"Ungültiger Timer-TS '{timer_end_timestamp}' für {item_type}")
        self.image = None; self.rect = None; self.update_appearance()
        if self.rect: self.rect.center = (world_x, world_y)
        else: logger.error(f"Konnte Rect für PlacedItem {item_type} nicht initial setzen!"); self.kill()
    def update_appearance(self):
        center = self.rect.center if hasattr(self, 'rect') and self.rect else None
        self.image = self.images_for_states.get(self.state, self.fallback_image)
        if not self.image: logger.critical(f"Kein Bild für State '{self.state}' in {self.item_type} ODER Fallback!"); self.image = pygame.Surface((PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)); self.image.fill(RED)
        self.rect = self.image.get_rect()
        if center: self.rect.center = center
    def update(self, dt):
        if self.state == 'growing' and self.timer_end_timestamp is not None and time.time() >= self.timer_end_timestamp:
            logger.info(f"Item '{self.item_type}' fertig!"); self.state = 'readyToEarn'; self.timer_end_timestamp = None; self.update_appearance()
    def interact(self):
        initial_state = self.state; action_taken = False
        if self.state == 'ohneErde': self.state = 'ohneSeed'; action_taken = True
        elif self.state == 'ohneSeed': self.state = 'giessen'; action_taken = True
        elif self.state == 'giessen': self.state = 'growing'; self.timer_end_timestamp = time.time() + GROW_TIME_SECONDS; logger.info(f"{self.item_type} Wachsen gestartet."); action_taken = True
        elif self.state == 'growing': remaining = self.timer_end_timestamp - time.time(); logger.info(f"{self.item_type} wächst (ca. {max(0, remaining):.0f}s)."); action_taken = False
        elif self.state == 'readyToEarn': logger.info(f"{self.item_type} Ernte-Interaktion."); self.state = 'ohneErde'; logger.info(f"{self.item_type} -> 'ohneErde'."); action_taken = True
        else: logger.warning(f"Unbek. Zustand '{self.state}' für {self.item_type}"); action_taken = False
        if self.state != initial_state: self.update_appearance(); logger.info(f"{self.item_type} State: '{initial_state}' -> '{self.state}'.")
        return action_taken

# --- Globale Variablen für Pygame Objekte & Spielstand ---
# (Deklaration für Klarheit, Initialisierung im try-Block)
screen = None; clock = None; ui_font = None; button_font = None; inventory_font = None
background_image = None; button_image_normal = None; item_icons = {}; placed_item_images = {}
fallback_placed_image = None; player = None; camera = None; inventory = None
all_sprites = None; npcs = None; placed_items = None
CENTERED_INVENTORY_X_POS = 0; CENTERED_INVENTORY_Y_POS = 0; BUTTON_RECT = None

# --- Speicherfunktion --- NEU
def save_game_state():
    """Speichert Inventar, Spielerposition und platzierte Items."""
    logger.info("Speichere Spielstand...")
    try:
        if inventory:
             logger.info(f"Speichere Inventar..."); inventory.save_inventory()
        else: logger.warning("Inventar nicht initialisiert, kann nicht speichern.")
    except Exception as e: logger.error(f"Fehler Inv speichern: {e}", exc_info=True)

    try:
        if player:
            logger.info(f"Speichere Spielerposition..."); player_pos_data = {'x': player.rect.x, 'y': player.rect.y}; save_data(player_pos_data, PLAYER_POS_SAVE_FILE)
        else: logger.warning("Spieler nicht initialisiert, kann Position nicht speichern.")
    except Exception as e: logger.error(f"Fehler Pos speichern: {e}", exc_info=True)

    try:
        if placed_items is not None: # Prüfen ob Gruppe existiert
             logger.info(f"Speichere platzierte Items...");
             placed_items_to_save = [{'type': item.item_type, 'x': item.rect.centerx, 'y': item.rect.centery, 'state': item.state, 'timer_end': item.timer_end_timestamp} for item in placed_items]
             save_data(placed_items_to_save, PLACED_ITEMS_SAVE_FILE); logger.info(f"{len(placed_items_to_save)} Items gespeichert.")
        else: logger.warning("Placed_items Gruppe nicht initialisiert, kann Items nicht speichern.")
    except Exception as e: logger.error(f"Fehler Items speichern: {e}", exc_info=True)


# --- Haupt-Initialisierungsblock ---
try:
    pygame.init()
    try: pygame.mixer.init(); logger.info("Pygame Mixer initialisiert.")
    except pygame.error as e_mix: logger.error(f"Mixer Init fehlgeschlagen: {e_mix}", exc_info=True)
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    try:
        info = pygame.display.Info(); detected_w, detected_h = info.current_w, info.current_h
        SCREEN_WIDTH, SCREEN_HEIGHT = detected_w, detected_h; logger.info(f"Spiel Bildschirmgröße erkannt: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
    except Exception as e_display:
        logger.warning(f"Bildschirmgröße/Modus Fehler: {e_display}. Nutze 800x600.", exc_info=True)
        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
        try: screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
        except Exception as e_fallback_display: logger.critical(f"Fallback-Bildschirm Fehler: {e_fallback_display}", exc_info=True); pygame.quit(); sys.exit()
    if screen is None: logger.critical("Bildschirm konnte nicht initialisiert werden."); pygame.quit(); sys.exit()
    pygame.display.set_caption("Das Spiel"); clock = pygame.time.Clock(); logger.info("Screen & Clock erstellt.")
    WORLD_WIDTH = SCREEN_WIDTH * 3; WORLD_HEIGHT = SCREEN_HEIGHT * 2; logger.info(f"Weltgröße: {WORLD_WIDTH}x{WORLD_HEIGHT}")
    ui_font_size = max(12, int(SCREEN_HEIGHT*(BASE_UI_FONT_SIZE/FONT_SIZE_REF_H))); button_font_size = max(10, int(SCREEN_HEIGHT*(BASE_BUTTON_FONT_SIZE/FONT_SIZE_REF_H))); inventory_font_size = max(8, int(SCREEN_HEIGHT*(BASE_INV_QTY_FONT_SIZE/FONT_SIZE_REF_H)))
    try: ui_font = pygame.font.Font(None, ui_font_size); button_font = pygame.font.Font(None, button_font_size); inventory_font = pygame.font.Font(None, inventory_font_size); logger.info(f"Fonts erstellt: UI={ui_font_size}, Btn={button_font_size}, Inv={inventory_font_size}")
    except Exception as e_font: logger.error(f"Fehler beim Erstellen der Fonts: {e_font}", exc_info=True); ui_font=pygame.font.Font(None, 28); button_font=pygame.font.Font(None,18); inventory_font=pygame.font.Font(None, 16)
    BUTTON_DEFAULT_WIDTH = int(SCREEN_WIDTH*BUTTON_DEFAULT_WIDTH_PERCENT); BUTTON_DEFAULT_HEIGHT = int(SCREEN_HEIGHT*BUTTON_DEFAULT_HEIGHT_PERCENT); BUTTON_RECT = pygame.Rect(BUTTON_X, 0, BUTTON_DEFAULT_WIDTH, BUTTON_DEFAULT_HEIGHT); logger.info(f"Button Default Size: {BUTTON_DEFAULT_WIDTH}x{BUTTON_DEFAULT_HEIGHT}")
    total_inventory_width = MAX_SLOTS * SCALED_BOX_SIZE + (MAX_SLOTS - 1) * SCALED_PADDING; CENTERED_INVENTORY_X_POS = (SCREEN_WIDTH - total_inventory_width) // 2; CENTERED_INVENTORY_Y_POS = SCREEN_HEIGHT - SCALED_BOX_SIZE - INVENTORY_BOTTOM_PADDING; logger.info(f"Inventar berechnet: Breite={total_inventory_width}, Pos=({CENTERED_INVENTORY_X_POS},{CENTERED_INVENTORY_Y_POS})")

    # Assets Laden
    logger.info("Lade Assets...")
    background_image = load_image_asset(BACKGROUND_FILENAME, alpha=False)
    if background_image:
        try:
            if background_image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT): background_image = pygame.transform.smoothscale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT)); logger.info("BG skaliert.")
        except Exception as e: logger.error(f"BG Skalierung fehlgeschlagen: {e}", exc_info=True); background_image = None
    button_image_normal = load_image_asset(BUTTON_FILENAME, alpha=True)
    item_icons = {name: load_image_asset(filename, alpha=True, scale_to=SCALED_ICON_SIZE) for name, filename in ICON_FILES.items()}; item_icons = {k: v for k, v in item_icons.items() if v is not None}
    placed_item_images = {}; fallback_placed_image = pygame.Surface((PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)); fallback_placed_image.fill(MAGENTA)
    for item_type, state_files in PLACED_ITEM_STATE_FILES.items():
        placed_item_images[item_type] = {}
        for state_name, filename in state_files.items():
            img = load_image_asset(filename, alpha=True, scale_to=(PLACED_ITEM_SIZE, PLACED_ITEM_SIZE))
            if img: placed_item_images[item_type][state_name] = img
            else: logger.warning(f"Fehlendes Zustandsbild: {item_type} -> {state_name}")

    # Spielobjekte erstellen (inkl. Laden)
    player_start_x=WORLD_WIDTH//2; player_start_y=WORLD_HEIGHT//2; player_radius=TILE_SIZE//3; spawn_x,spawn_y=player_start_x,player_start_y
    loaded_pos_data = load_data(PLAYER_POS_SAVE_FILE)
    if isinstance(loaded_pos_data, dict) and 'x' in loaded_pos_data and 'y' in loaded_pos_data:
        try: spawn_x=int(loaded_pos_data['x']); spawn_y=int(loaded_pos_data['y']); logger.info(f"Spieler Spawn(TL):({spawn_x},{spawn_y})")
        except: logger.warning(f"Ungültige Pos-Daten. Standard ({spawn_x},{spawn_y})")
    else: logger.info(f"Keine Pos-Datei. Standard ({spawn_x},{spawn_y})")
    player = Player(spawn_x, spawn_y, player_radius, RED)
    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT); initial_cam_x = max(0, min(player.rect.centerx - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH)); initial_cam_y = max(0, min(player.rect.centery - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT)); camera.camera_rect.topleft = (initial_cam_x, initial_cam_y); logger.info(f"Kamera ausgerichtet: {camera.camera_rect.topleft}")
    inventory = Inventory(filepath=INVENTORY_SAVE_FILE); logger.info(f"Inventar erstellt/geladen.");
    if not inventory.has_item("Blumentopf"): inventory.add_item("Blumentopf", 3)
    if not inventory.has_item("Sack Erde"): inventory.add_item("Sack Erde", 5)
    if not inventory.has_item("Weed Seeds"): inventory.add_item("Weed Seeds", 5)
    all_sprites = pygame.sprite.Group(); npcs = pygame.sprite.Group(); placed_items = pygame.sprite.Group()
    logger.debug(f"Lade platzierte Items...")
    loaded_items_list = load_data(PLACED_ITEMS_SAVE_FILE, default_data=[]); loaded_item_count = 0
    if isinstance(loaded_items_list, list):
        for item_data in loaded_items_list:
            if isinstance(item_data, dict):
                try: item_type=item_data.get('type','?'); item_x=int(item_data['x']); item_y=int(item_data['y']); item_state=item_data.get('state','ohneErde'); item_timer_end=item_data.get('timer_end', None)
                except (KeyError, ValueError, TypeError) as e: logger.warning(f"Ungültiger Eintrag in '{PLACED_ITEMS_FILENAME}': {item_data} -> {e}", exc_info=True); continue
                images = placed_item_images.get(item_type, {}); fallback_img = fallback_placed_image
                new_item = PlacedItem(item_x,item_y, item_type, images, fallback_img, state=item_state, timer_end_timestamp=item_timer_end)
                if new_item.rect: all_sprites.add(new_item); placed_items.add(new_item); loaded_item_count += 1
                else: logger.error(f"Konnte PlacedItem beim Laden nicht erstellen: {item_data}")
            else: logger.warning(f"Ungültiger Eintragstyp in '{PLACED_ITEMS_FILENAME}': {type(item_data)}")
        logger.info(f"{loaded_item_count} platzierte Items geladen.")
    else: logger.warning(f"'{PLACED_ITEMS_FILENAME}' enthielt keine Liste.")
    npc_radius=TILE_SIZE//3; npc1=NPC(TILE_SIZE*10,TILE_SIZE*8,npc_radius,BLUE); npc2=NPC(WORLD_WIDTH-TILE_SIZE*10,TILE_SIZE*15,npc_radius,GREEN)
    all_sprites.add(player, npc1, npc2); npcs.add(npc1, npc2); logger.debug(f"Spieler und NPCs hinzugefügt.")

    # UI Positionen & Button Rect Anpassen
    if platform_utils.IS_ANDROID and button_image_normal:
        button_width_actual = button_image_normal.get_width(); button_height_actual = button_image_normal.get_height()
    else: button_width_actual = BUTTON_DEFAULT_WIDTH; button_height_actual = BUTTON_DEFAULT_HEIGHT
    BUTTON_Y = CENTERED_INVENTORY_Y_POS - button_height_actual - BUTTON_PADDING; BUTTON_RECT.size = (button_width_actual, button_height_actual); BUTTON_RECT.topleft = (BUTTON_X, BUTTON_Y)
    logger.debug(f"Interaktions-Button Rect: {BUTTON_RECT}")

    if platform_utils.IS_ANDROID: platform_utils.set_android_immersive_mode(); logger.info("Android Immersive Mode aktiviert.")

except Exception as e: logger.critical(f"Init/Setup Fehler: {e}", exc_info=True); pygame.quit(); sys.exit()


# --- Spiel-Zustände ---
is_dragging = False; dragged_item_type = None; dragged_item_image = None
interaction_active = False; interaction_start_time = 0.0; potential_interaction_item = None

# --- Spiel-Loop ---
running = True; logger.info("Spiel-Loop startet.")
while running:
    try: # try/except um die Gameloop
        dt = clock.tick(FPS) / 1000.0
        mouse_pos_screen = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # --- Interaktionsziel finden ---
        current_closest_item = None; min_dist = float('inf'); player_cx = player.rect.centerx; player_cy = player.rect.centery
        for item in placed_items:
            item_cx = item.rect.centerx; item_cy = item.rect.centery
            distance = math.hypot(player_cx - item_cx, player_cy - item_cy)
            if distance < INTERACTION_RADIUS + item.rect.width / 2:
                 if distance < min_dist: min_dist = distance; current_closest_item = item
        interaction_possible_now = current_closest_item is not None
        if interaction_active and potential_interaction_item != current_closest_item:
            logger.debug("Interaktionsziel verloren/geändert."); potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False

        # --- Event Handling ---
        interaction_press_event_handled = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False; logger.info("QUIT Event.")
            # --- Keyboard Events ---
            if not platform_utils.IS_ANDROID:
                if event.type == pygame.KEYDOWN:
                    # --- ESC Taste -> Zurück zum Menü --- NEU
                    if event.key == pygame.K_ESCAPE:
                        logger.info("ESC gedrückt -> Speichern und zurück zum Hauptmenü...")
                        save_game_state() # Spielstand speichern
                        pygame.quit()     # Aktuelles Pygame beenden
                        logger.info("Game-Pygame beendet.")
                        try:
                            # main.py starten und aktuellen Prozess ersetzen
                            args_for_exec = [sys.executable, MAIN_SCRIPT_PATH]
                            logger.info(f"Führe os.execv aus mit: {args_for_exec}")
                            os.execv(sys.executable, args_for_exec)
                            # Wird bei Erfolg nie erreicht
                        except FileNotFoundError:
                            logger.critical(f"FEHLER: Python Interpreter '{sys.executable}' oder Main-Skript '{MAIN_SCRIPT_PATH}' nicht gefunden.", exc_info=True)
                            sys.exit(1) # Beenden, wenn exec fehlschlägt
                        except Exception as e_exec:
                            logger.critical(f"FEHLER beim Versuch, os.execv für main.py auszuführen: {e_exec}", exc_info=True)
                            sys.exit(1)
                    # --- Leertaste für Interaktion ---
                    elif event.key == pygame.K_SPACE and not interaction_active and interaction_possible_now:
                        interaction_active = True; interaction_press_event_handled = True; potential_interaction_item = current_closest_item; interaction_start_time = time.time(); logger.info(f"Beginne Interaktion (SPACE) mit {potential_interaction_item.item_type}")
                # --- KEYUP für Leertaste ---
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE and interaction_active and potential_interaction_item:
                        if time.time() - interaction_start_time < LONG_PRESS_THRESHOLD: # Kurzer Druck
                            item_to_interact = potential_interaction_item; logger.debug(f"Kurz (SPACE) -> Aktion {item_to_interact.state}")
                            required_item = None; interaction_possible_prereq = False
                            if item_to_interact.state=='ohneErde': required_item = "Sack Erde"
                            elif item_to_interact.state=='ohneSeed': required_item = "Weed Seeds"
                            elif item_to_interact.state in ['giessen', 'readyToEarn', 'growing']: interaction_possible_prereq = True
                            if required_item and inventory.has_item(required_item, 1) and inventory.remove_item(required_item, 1): interaction_possible_prereq=True; logger.info(f"'{required_item}' verbraucht.")
                            elif required_item: logger.info(f"Fehlt: '{required_item}'.")
                            if interaction_possible_prereq: item_to_interact.interact()
                        potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False # Reset nach Loslassen

            # --- Maus Events ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Linksklick
                button_clicked_this_event = False
                if platform_utils.IS_ANDROID and BUTTON_RECT.collidepoint(mouse_pos_screen):
                    if not interaction_active and interaction_possible_now: button_clicked_this_event = True; interaction_active = True; interaction_press_event_handled = True; potential_interaction_item = current_closest_item; interaction_start_time = time.time(); logger.info(f"Beginne Interaktion (Button) mit {potential_interaction_item.item_type}")
                    else: logger.debug("Button Klick ignoriert.")
                elif not is_dragging and not button_clicked_this_event:
                    inv_items_list = inventory.get_item_list_for_display()
                    for i in range(MAX_SLOTS):
                        slot_x = CENTERED_INVENTORY_X_POS + i * (SCALED_BOX_SIZE + SCALED_PADDING); slot_y = CENTERED_INVENTORY_Y_POS
                        slot_rect = pygame.Rect(slot_x, slot_y, SCALED_BOX_SIZE, SCALED_BOX_SIZE)
                        if slot_rect.collidepoint(mouse_pos_screen) and i < len(inv_items_list):
                            item_name, quantity = inv_items_list[i]
                            if item_name == "Blumentopf" and quantity > 0: is_dragging=True; dragged_item_type="Blumentopf"; dragged_item_image = placed_item_images.get("Blumentopf", {}).get('ohneErde', fallback_placed_image); logger.info(f"Starte Drag: {dragged_item_type}"); break
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1: # Linksklick Loslassen
                if platform_utils.IS_ANDROID and interaction_active:
                    logger.debug("Interaktions-Button LOSGELASSEN (Android)")
                    if potential_interaction_item and time.time() - interaction_start_time < LONG_PRESS_THRESHOLD: # Kurzer Druck
                        item_to_interact = potential_interaction_item; logger.debug(f"Kurz (Button) -> Aktion {item_to_interact.state}")
                        required_item = None; interaction_possible_prereq = False
                        if item_to_interact.state=='ohneErde': required_item = "Sack Erde"
                        elif item_to_interact.state=='ohneSeed': required_item = "Weed Seeds"
                        elif item_to_interact.state in ['giessen', 'readyToEarn', 'growing']: interaction_possible_prereq = True
                        if required_item and inventory.has_item(required_item, 1) and inventory.remove_item(required_item, 1): interaction_possible_prereq=True; logger.info(f"'{required_item}' verbraucht.")
                        elif required_item: logger.info(f"Fehlt: '{required_item}'.")
                        if interaction_possible_prereq: item_to_interact.interact()
                    potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False # Reset nach Loslassen
                if is_dragging:
                    world_x, world_y = camera.screen_to_world(mouse_pos_screen[0], mouse_pos_screen[1])
                    snapped_tl_x = (world_x // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE; snapped_tl_y = (world_y // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
                    snapped_center_x = snapped_tl_x + PLACED_ITEM_SIZE / 2; snapped_center_y = snapped_tl_y + PLACED_ITEM_SIZE / 2
                    can_place = True; temp_rect = pygame.Rect(snapped_tl_x, snapped_tl_y, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)
                    for item in placed_items:
                        if temp_rect.colliderect(item.rect): can_place = False; logger.info("Platzieren blockiert."); break
                    if can_place and inventory.remove_item(dragged_item_type, 1):
                        images = placed_item_images.get(dragged_item_type, {}); fallback_img = fallback_placed_image
                        new_item = PlacedItem(snapped_center_x, snapped_center_y, dragged_item_type, images, fallback_img, state='ohneErde')
                        if new_item.rect: all_sprites.add(new_item); placed_items.add(new_item); logger.info(f"'{dragged_item_type}' platziert.")
                        else: logger.error("Fehler Erstellen PlacedItem nach Drag!"); inventory.add_item(dragged_item_type, 1)
                    elif can_place: logger.warning(f"Platzieren fehlgeschlagen (Inventar?)")
                    is_dragging = False; dragged_item_type = None; dragged_item_image = None

        # --- Update ---
        player.update(keys, camera.get_current_screen_rect())
        camera.update(player)
        npcs.update()
        placed_items.update(dt)

        # --- Aufheben-Logik (Langes Halten) ---
        if interaction_active and potential_interaction_item and time.time() - interaction_start_time >= LONG_PRESS_THRESHOLD:
            logger.info(f"LANGES DRÜCKEN -> Pickup '{potential_interaction_item.item_type}'")
            item_type_to_add = potential_interaction_item.item_type
            if inventory.add_item(item_type_to_add, 1): logger.info(f"'{item_type_to_add}' zum Inventar."); potential_interaction_item.kill(); logger.info(f"Item entfernt.")
            else: logger.warning(f"Aufheben fehlgeschlagen: Inventar voll?")
            potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False

        # --- Draw ---
        if background_image: screen.blit(background_image, (0, 0))
        else: screen.fill(BLACK)
        for sprite in all_sprites:
            if camera.get_current_screen_rect().colliderect(sprite.rect): screen.blit(sprite.image, camera.apply(sprite))
        if interaction_active and potential_interaction_item:
            try:
                player_screen_rect = camera.apply(player); player_screen_center = player_screen_rect.center
                pygame.draw.circle(screen, WHITE, player_screen_center, INTERACTION_RADIUS, 1)
                if interaction_start_time > 0:
                    hold_duration = time.time() - interaction_start_time; progress = min(1.0, hold_duration / LONG_PRESS_THRESHOLD)
                    if progress > 0: bar_width = 50; bar_height = 5; bar_x = player_screen_center[0] - bar_width // 2; bar_y = player_screen_rect.top - bar_height - 5; pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height)); pygame.draw.rect(screen, RED, (bar_x, bar_y, int(bar_width * progress), bar_height))
            except Exception as e: logger.error(f"Zeichenfehler Interaktion: {e}", exc_info=True)
        try: # UI Text
            if pygame.font.get_init() and ui_font: pos_text_str = f"P({player.rect.x},{player.rect.y}) C({camera.camera_rect.x},{camera.camera_rect.y})"; pos_text_surface = ui_font.render(pos_text_str, True, WHITE); screen.blit(pos_text_surface, (10, 10))
        except Exception as e: logger.error(f"Zeichenfehler UI-Text: {e}", exc_info=True)

        # --- Inventar zeichnen (Manuell, mit Text-Fallback) ---
        try:
            items_for_display = inventory.get_item_list_for_display()
            for i in range(MAX_SLOTS):
                slot_x = CENTERED_INVENTORY_X_POS + i * (SCALED_BOX_SIZE + SCALED_PADDING); slot_y = CENTERED_INVENTORY_Y_POS
                slot_rect = pygame.Rect(slot_x, slot_y, SCALED_BOX_SIZE, SCALED_BOX_SIZE)
                pygame.draw.rect(screen, (100, 100, 100, 180), slot_rect); pygame.draw.rect(screen, WHITE, slot_rect, 2)
                if i < len(items_for_display):
                    item_name, quantity = items_for_display[i]; icon_surface = item_icons.get(item_name)
                    if icon_surface:
                        icon_rect = icon_surface.get_rect(center=slot_rect.center); screen.blit(icon_surface, icon_rect)
                    else: # Text Fallback
                        logger.warning(f"Slot {i} ({item_name}): KEIN Icon gefunden! Zeichne Text.")
                        if inventory_font:
                            fallback_text_surface = inventory_font.render(item_name, True, WHITE)
                            fallback_text_rect = fallback_text_surface.get_rect(center=slot_rect.center)
                            screen.blit(fallback_text_surface, fallback_text_rect)
                        else: logger.error(f"Slot {i} ({item_name}): Kann Text nicht zeichnen, inventory_font ist None.")
                    if quantity > 0 and inventory_font: # Menge
                        qty_surface = inventory_font.render(str(quantity), True, WHITE); qty_rect = qty_surface.get_rect(bottomright=(slot_rect.right - SCALED_PADDING // 2, slot_rect.bottom - SCALED_PADDING // 2)); screen.blit(qty_surface, qty_rect)
                    elif quantity > 0: logger.warning(f"Slot {i} ({item_name}): Menge > 0, aber inventory_font ist None.")
        except Exception as e: logger.error(f"Fehler Inventar-Anzeige (manuell): {e}", exc_info=True)

        # Drag Preview & Android Button & Flip
        if is_dragging and dragged_item_image:
            world_x, world_y = camera.screen_to_world(mouse_pos_screen[0], mouse_pos_screen[1]); snapped_tl_x = (world_x // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE; snapped_tl_y = (world_y // PLACED_ITEM_SIZE) * PLACED_ITEM_SIZE
            temp_snap_rect_world = pygame.Rect(snapped_tl_x, snapped_tl_y, PLACED_ITEM_SIZE, PLACED_ITEM_SIZE); snapped_screen_rect = camera.apply_rect(temp_snap_rect_world)
            drag_rect = dragged_item_image.get_rect(center=snapped_screen_rect.center); screen.blit(dragged_item_image, drag_rect); pygame.draw.rect(screen, WHITE, snapped_screen_rect, 1)
        if platform_utils.IS_ANDROID:
            if button_image_normal: screen.blit(button_image_normal, BUTTON_RECT.topleft)
            else: pygame.draw.rect(screen, BUTTON_COLOR_NORMAL, BUTTON_RECT); pygame.draw.rect(screen, BUTTON_BORDER_COLOR, BUTTON_RECT, 2)
            if not button_image_normal and pygame.font.get_init() and button_font:
                try: btn_text_surf = button_font.render("Interact", True, WHITE); btn_text_rect = btn_text_surf.get_rect(center=BUTTON_RECT.center); screen.blit(btn_text_surf, btn_text_rect)
                except Exception as e: logger.error(f"Zeichenfehler Button-Text: {e}", exc_info=True)
        pygame.display.flip()

    except Exception as e_game_loop:
        logger.critical(f"Unerwarteter Fehler in der Spielschleife: {e_game_loop}", exc_info=True)
        running = False # Beende bei Fehler

# --- Spiel beenden (wird nur bei normalem Loop-Ende erreicht, z.B. QUIT) ---
logger.info("Spiel-Loop beendet.")
save_game_state() # Spielstand auch hier speichern
if pygame.get_init(): pygame.quit(); logger.info("Pygame beendet.")
else: logger.info("Pygame war bereits beendet.")
sys.exit()