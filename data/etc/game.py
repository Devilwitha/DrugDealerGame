# game.py (Fix für BUTTON_DEFAULT_WIDTH NameError)
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
logging.basicConfig(level=log_level, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info("Spiel wird initialisiert...")

# --- Eigene Module importieren ---
try:
    import platform_utils # Nutzt jetzt dieses Modul für Android-Check
    from player import Player
    from npc import NPC
    from camera import Camera
    from inventory import Inventory, BOX_SIZE, PADDING, MAX_SLOTS
    from persistence import load_data, save_data
    logger.info("Eigene Module importiert.")
except ImportError as e: logger.critical(f"Fehler Import Modul: {e}."); sys.exit()
except Exception as e: logger.critical(f"Unerwarteter Import-Fehler: {e}"); sys.exit()

# --- Konstanten ---
SCREEN_WIDTH = 800; SCREEN_HEIGHT = 600; TILE_SIZE = 32; FPS = 60
WORLD_WIDTH = SCREEN_WIDTH * 3; WORLD_HEIGHT = SCREEN_HEIGHT * 2
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREEN = (0, 255, 0); RED = (255, 0, 0); BLUE = (0, 0, 255)
PLACED_ITEM_COLOR = GREEN
PLACED_ITEM_SIZE = TILE_SIZE
INTERACTION_RADIUS = TILE_SIZE
LONG_PRESS_THRESHOLD = 1.0 # Sekunden Schwelle für Aufheben
GROW_TIME_SECONDS = 10 # Zum Testen verkürzt! Original: 5 * 60

# Inventar Padding
INVENTORY_BOTTOM_PADDING = 20; INVENTORY_LEFT_PADDING = 20

# Interaktions-Button
BUTTON_DEFAULT_WIDTH = 60  # KORREKTUR: Fehlende Konstante hinzugefügt
BUTTON_DEFAULT_HEIGHT = 60 # KORREKTUR: Fehlende Konstante hinzugefügt
BUTTON_PADDING = 15
BUTTON_X = BUTTON_PADDING
# Y-Position und finales BUTTON_RECT werden später berechnet/angepasst
BUTTON_RECT = pygame.Rect(BUTTON_X, 0, BUTTON_DEFAULT_WIDTH, BUTTON_DEFAULT_HEIGHT) # Nutzt jetzt Konstanten
BUTTON_COLOR_NORMAL = (80, 80, 80); BUTTON_BORDER_COLOR = WHITE

# --- Dateipfade & Asset-Namen ---
try: script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError: script_dir = os.path.abspath("."); logger.warning(f"__file__ nicht verfügbar, nutze: {script_dir}")
# Gehe eine Ebene höher von 'data/etc' zu 'data'
data_dir = os.path.normpath(os.path.join(script_dir, ".."))
logger.info(f"'data' Ordner angenommen als: {data_dir}")
IMAGE_FOLDER = os.path.join(data_dir, "bilder"); SOUND_FOLDER = os.path.join(data_dir, "sounds")
SAVE_DATA_DIR_ABS = os.path.join(data_dir, "savedata")
BACKGROUND_FILENAME = "background.png" # PLATZHALTER
BUTTON_FILENAME = "interact_button.png"   # PLATZHALTER
INVENTORY_FILENAME="inventar.json"; INVENTORY_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, INVENTORY_FILENAME)
PLAYER_POS_FILENAME="player_position.json"; PLAYER_POS_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, PLAYER_POS_FILENAME)
PLACED_ITEMS_FILENAME="placed_items.json"; PLACED_ITEMS_SAVE_FILE=os.path.join(SAVE_DATA_DIR_ABS, PLACED_ITEMS_FILENAME)
logger.info(f"Bild-Ordner: {IMAGE_FOLDER}"); logger.info(f"Speicher-Ordner: {SAVE_DATA_DIR_ABS}")
# ... (Logging Speicherpfade) ...

# --- Asset Ladefunktion ---
def load_image_asset(filename, alpha=True):
    path = os.path.join(IMAGE_FOLDER, filename)
    try: image = pygame.image.load(path); image = image.convert_alpha() if alpha else image.convert(); logger.info(f"Bild '{filename}' geladen."); return image
    except Exception as e: logger.error(f"Fehler Laden Bild '{path}': {e}"); return None

# --- PlacedItem Klasse ---
class PlacedItem(pygame.sprite.Sprite): # Definition bleibt gleich
    STATES = ['ohneErde', 'ohneSeed', 'giessen', 'growing', 'readyToEarn']
    def __init__(self, world_x, world_y, size, color, item_type="Blumentopf", state='ohneErde', timer_end_timestamp=None):
        super().__init__()
        self.item_type = item_type; self.size = size; self.base_color = color; self.state = state if state in self.STATES else 'ohneErde'
        try: self.timer_end_timestamp = float(timer_end_timestamp) if timer_end_timestamp else None
        except: self.timer_end_timestamp = None; logger.warning(f"Ungültiger Timer-TS '{timer_end_timestamp}'")
        self.image = pygame.Surface((size, size)); self.update_appearance()
        self.rect = self.image.get_rect(center=(world_x, world_y))
    def update_appearance(self): state_colors = {'ohneErde':(139,69,19),'ohneSeed':(160,82,45),'giessen':(100,149,237),'growing':(34,139,34),'readyToEarn':(0,255,0)}; color = state_colors.get(self.state, self.base_color); self.image.fill(color)
    def update(self, dt):
        if self.state == 'growing' and self.timer_end_timestamp is not None:
            if time.time() >= self.timer_end_timestamp: logger.info(f"Item '{self.item_type}' fertig!"); self.state = 'readyToEarn'; self.timer_end_timestamp = None; self.update_appearance()
    def interact(self):
        initial_state = self.state; action_taken = False
        if self.state == 'ohneErde': self.state = 'ohneSeed'; action_taken = True
        elif self.state == 'ohneSeed': self.state = 'giessen'; action_taken = True
        elif self.state == 'giessen': self.state = 'growing'; self.timer_end_timestamp = time.time() + GROW_TIME_SECONDS; logger.info(f"Item Wachsen gestartet."); action_taken = True
        elif self.state == 'growing': remaining = self.timer_end_timestamp - time.time(); logger.info(f"Item wächst (ca. {max(0, remaining):.0f}s)."); action_taken = False
        elif self.state == 'readyToEarn': logger.info(f"Item Ernte-Interaktion."); self.state = 'ohneErde'; logger.info(f"Item -> 'ohneErde'."); action_taken = True # Reset
        else: logger.warning(f"Unbek. Zustand '{self.state}'"); action_taken = False
        if self.state != initial_state: self.update_appearance(); logger.info(f"Item State: '{initial_state}' -> '{self.state}'.")
        return action_taken

# --- Pygame Initialisierung & Bildschirm ---
try:
    pygame.init()
    # Versuche Immersive Mode NUR wenn Android erkannt wurde
    if platform_utils.IS_ANDROID: platform_utils.set_android_immersive_mode()
    logger.info("Pygame initialisiert.")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("NameError Fix")
    clock = pygame.time.Clock()
    logger.info("Screen & Clock erstellt.")
except Exception as e: logger.critical(f"Init/Screen Fehler: {e}"); pygame.quit(); sys.exit()

# --- Assets Laden ---
background_image = load_image_asset(BACKGROUND_FILENAME, alpha=False)
if background_image and background_image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
    try: background_image = pygame.transform.smoothscale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e: logger.error(f"BG Skalierung fehlgeschlagen: {e}"); background_image = None
button_image_normal = load_image_asset(BUTTON_FILENAME, alpha=True)

# --- Spielobjekte erstellen ---
try:
    # Spielerposition laden/setzen
    player_start_x=WORLD_WIDTH//2; player_start_y=WORLD_HEIGHT//2; player_radius=TILE_SIZE//3; spawn_x,spawn_y=player_start_x,player_start_y
    loaded_pos_data = load_data(PLAYER_POS_SAVE_FILE)
    if isinstance(loaded_pos_data, dict) and 'x' in loaded_pos_data and 'y' in loaded_pos_data:
        try: spawn_x=int(loaded_pos_data['x']); spawn_y=int(loaded_pos_data['y']); logger.info(f"Spieler Spawn(TL):({spawn_x},{spawn_y})")
        except: logger.warning(f"Ungültige Pos-Daten. Standard ({spawn_x},{spawn_y})")
    else: logger.info(f"Keine Pos-Datei. Standard ({spawn_x},{spawn_y})")
    player = Player(spawn_x, spawn_y, player_radius, RED) # TODO: Bild

    # Kamera erstellen und initial ausrichten
    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
    initial_cam_x=(player.rect.centerx//SCREEN_WIDTH)*SCREEN_WIDTH; initial_cam_y=(player.rect.centery//SCREEN_HEIGHT)*SCREEN_HEIGHT
    initial_cam_x=max(0,min(initial_cam_x, WORLD_WIDTH-SCREEN_WIDTH)); initial_cam_y=max(0,min(initial_cam_y, WORLD_HEIGHT-SCREEN_HEIGHT))
    camera.camera_rect.topleft=(initial_cam_x, initial_cam_y); logger.info(f"Kamera ausgerichtet: {camera.camera_rect.topleft}")

    # Inventar erstellen (lädt intern)
    inventory = Inventory(filepath=INVENTORY_SAVE_FILE); logger.info(f"Inventar erstellt.")
    if not inventory.has_item("Blumentopf"): inventory.add_item("Blumentopf", 3)
    if not inventory.has_item("Sack Erde"): inventory.add_item("Sack Erde", 5)
    if not inventory.has_item("Weed Seeds"): inventory.add_item("Weed Seeds", 5)

    # Sprite-Gruppen
    all_sprites = pygame.sprite.Group(); npcs = pygame.sprite.Group(); placed_items = pygame.sprite.Group()

    # Platzierte Items laden (mit State und Timer)
    # ... (Ladelogik bleibt gleich) ...
    logger.debug(f"Lade platzierte Items...")
    loaded_items_list = load_data(PLACED_ITEMS_SAVE_FILE, default_data=[])
    loaded_item_count = 0
    if isinstance(loaded_items_list, list):
        for item_data in loaded_items_list:
            if isinstance(item_data, dict):
                try: item_type=item_data.get('type','?'); item_x=int(item_data['x']); item_y=int(item_data['y']); item_state=item_data.get('state','ohneErde'); item_timer_end=item_data.get('timer_end', None)
                except (KeyError, ValueError, TypeError) as e: logger.warning(f"Ungültiger Eintrag in '{PLACED_ITEMS_SAVE_FILE}': {item_data} -> {e}"); continue
                if item_type == "Blumentopf":
                    item_color=PLACED_ITEM_COLOR; item_size=PLACED_ITEM_SIZE # TODO: Bild
                    new_item = PlacedItem(item_x,item_y,item_size,item_color,item_type,state=item_state,timer_end_timestamp=item_timer_end)
                    all_sprites.add(new_item); placed_items.add(new_item); loaded_item_count += 1
                else: logger.warning(f"Unbekannter Typ '{item_type}' geladen.")
            else: logger.warning(f"Ungültiger Eintragstyp in '{PLACED_ITEMS_SAVE_FILE}': {type(item_data)}")
        logger.info(f"{loaded_item_count} platzierte Items geladen.")
    else: logger.warning(f"'{PLACED_ITEMS_SAVE_FILE}' enthielt keine Liste.")


    # NPCs erstellen und hinzufügen
    npc_radius=TILE_SIZE//3; npc1=NPC(TILE_SIZE*10,TILE_SIZE*8,npc_radius,BLUE); npc2=NPC(WORLD_WIDTH-TILE_SIZE*10,TILE_SIZE*15,npc_radius,GREEN) # TODO: Bilder
    all_sprites.add(player, npc1, npc2); npcs.add(npc1, npc2)
    logger.debug(f"Spieler und NPCs hinzugefügt.")

except Exception as e: logger.critical(f"Fehler Objekt-Erstellung: {e}", exc_info=True); pygame.quit(); sys.exit()

# --- UI Positionen & Button Rect Anpassen ---
INVENTORY_Y_POS = SCREEN_HEIGHT - BOX_SIZE - INVENTORY_BOTTOM_PADDING; INVENTORY_X_POS = INVENTORY_LEFT_PADDING
inventory_pos = (INVENTORY_X_POS, INVENTORY_Y_POS)
# Passe Button-Größe an Bild an, wenn vorhanden, sonst Fallback
if platform_utils.IS_ANDROID and button_image_normal:
    button_width_actual = button_image_normal.get_width()
    button_height_actual = button_image_normal.get_height()
else: # Fallback-Größe verwenden (jetzt definiert)
    button_width_actual = BUTTON_DEFAULT_WIDTH
    button_height_actual = BUTTON_DEFAULT_HEIGHT
BUTTON_Y = INVENTORY_Y_POS - button_height_actual - BUTTON_PADDING # Oberhalb Inventar
BUTTON_RECT.size = (button_width_actual, button_height_actual); BUTTON_RECT.topleft = (BUTTON_X, BUTTON_Y)
logger.debug(f"Inventar Pos: {inventory_pos}"); logger.debug(f"Interaktions-Button Rect: {BUTTON_RECT}")

# --- Spiel-Zustände ---
is_dragging = False; dragged_item_type = None; dragged_item_image = None
interaction_active = False; interaction_start_time = 0.0; potential_interaction_item = None

# --- Spiel-Loop ---
running = True; logger.info("Spiel-Loop startet.")
while running:
    # (Rest des Spiel-Loops bleibt unverändert zur letzten Version)
    # ... (dt, mouse_pos, keys) ...
    # ... (Finde potenzielles Interaktionsobjekt) ...
    # ... (Event Handling mit platform_utils.IS_ANDROID checks) ...
    # ... (Update Logik mit interaction_active check) ...
    # ... (Draw Logik mit platform_utils.IS_ANDROID check für Button-Zeichnung) ...
    # ------ START KOPIERTER TEIL (Rest des Loops) ------
    dt = clock.tick(FPS) / 1000.0
    mouse_pos_screen = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()

    # --- Finde potenzielles Interaktionsobjekt (JEDEN FRAME) ---
    current_closest_item = None; min_dist = float('inf')
    player_cx = player.rect.centerx; player_cy = player.rect.centery
    for item in placed_items:
        item_cx = item.rect.centerx; item_cy = item.rect.centery
        distance = math.sqrt((player_cx - item_cx)**2 + (player_cy - item_cy)**2)
        if distance < INTERACTION_RADIUS + item.rect.width / 2:
             if distance < min_dist: min_dist = distance; current_closest_item = item
    interaction_possible_now = current_closest_item is not None
    if interaction_active and potential_interaction_item != current_closest_item:
        logger.info("Interaktionsziel verloren/geändert."); potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False

    # --- Event Handling ---
    interaction_press_event_handled = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        # --- Keyboard Events (Nur NICHT-Android) ---
        if not platform_utils.IS_ANDROID:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_SPACE and not interaction_active and interaction_possible_now:
                    interaction_active = True; interaction_press_event_handled = True
                    potential_interaction_item = current_closest_item; interaction_start_time = time.time()
                    logger.info(f"Beginne Interaktion (SPACE) mit: '{potential_interaction_item.item_type}' St: '{potential_interaction_item.state}'")

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    if interaction_active and potential_interaction_item:
                        hold_duration = time.time() - interaction_start_time
                        if hold_duration < LONG_PRESS_THRESHOLD: # Kurzes Drücken
                            item_to_interact = potential_interaction_item; logger.debug(f"Kurz (SPACE) -> Versuch Interaktion mit State '{item_to_interact.state}'")
                            interaction_possible_prereq = False
                            if item_to_interact.state=='ohneErde':
                                if inventory.has_item("Sack Erde", 1):
                                    if inventory.remove_item("Sack Erde", 1): interaction_possible_prereq=True; logger.info("Sack Erde verbraucht.")
                                    else: logger.error("Fehler: Erde entfernen")
                                else: logger.info("Fehlt: 'Sack Erde'.")
                            elif item_to_interact.state=='ohneSeed':
                                if inventory.has_item("Weed Seeds", 1):
                                    if inventory.remove_item("Weed Seeds", 1): interaction_possible_prereq=True; logger.info("Weed Seeds verbraucht.")
                                    else: logger.error("Fehler: Seeds entfernen")
                                else: logger.info("Fehlt: 'Weed Seeds'.")
                            elif item_to_interact.state in ['giessen', 'readyToEarn', 'growing']: interaction_possible_prereq = True
                            if interaction_possible_prereq: item_to_interact.interact()
                        # else: Langes Drücken wird im Update behandelt
                    potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False # Immer Reset

        # --- Maus Events ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Linksklick
                button_clicked_this_event = False
                # 1. Button-Klick (NUR auf Android)
                if platform_utils.IS_ANDROID and BUTTON_RECT.collidepoint(mouse_pos_screen) and not interaction_active and interaction_possible_now:
                    button_clicked_this_event = True; logger.debug("Interaktions-Button GEDRÜCKT (Android)")
                    interaction_active = True; interaction_press_event_handled = True
                    potential_interaction_item = current_closest_item; interaction_start_time = time.time()
                    logger.info(f"Beginne Interaktion (Button) mit: '{potential_interaction_item.item_type}' St: '{potential_interaction_item.state}'")

                # 2. Inventar-Klick für Drag & Drop?
                elif not is_dragging and not button_clicked_this_event:
                     inv_items_list = inventory.get_item_list_for_display()
                     for i in range(MAX_SLOTS):
                         slot_rect=pygame.Rect(INVENTORY_X_POS+i*(BOX_SIZE+PADDING),INVENTORY_Y_POS,BOX_SIZE,BOX_SIZE)
                         if slot_rect.collidepoint(mouse_pos_screen):
                             if i<len(inv_items_list):
                                 item_name, quantity = inv_items_list[i]
                                 if item_name == "Blumentopf" and quantity > 0:
                                     is_dragging=True; dragged_item_type="Blumentopf"; dragged_item_image=pygame.Surface((PLACED_ITEM_SIZE, PLACED_ITEM_SIZE)); dragged_item_image.fill(PLACED_ITEM_COLOR)
                                     logger.info(f"Starte Drag: {dragged_item_type}"); break

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Linksklick Loslassen
                # 1. Button Loslassen (NUR auf Android)
                if platform_utils.IS_ANDROID and interaction_active:
                    logger.debug("Interaktions-Button LOSGELASSEN (Android)")
                    if potential_interaction_item:
                         hold_duration = time.time() - interaction_start_time
                         if hold_duration < LONG_PRESS_THRESHOLD: # Kurzes Drücken
                             item_to_interact = potential_interaction_item; logger.debug(f"Kurz (Button) -> Versuch Interaktion mit State '{item_to_interact.state}'")
                             interaction_possible_prereq = False # Prüfe Voraussetzungen
                             if item_to_interact.state=='ohneErde':
                                 if inventory.has_item("Sack Erde", 1):
                                     if inventory.remove_item("Sack Erde", 1): interaction_possible_prereq=True; logger.info("Sack Erde verbraucht.")
                                     else: logger.error("Fehler: Erde entfernen")
                                 else: logger.info("Fehlt: 'Sack Erde'.")
                             elif item_to_interact.state=='ohneSeed':
                                 if inventory.has_item("Weed Seeds", 1):
                                     if inventory.remove_item("Weed Seeds", 1): interaction_possible_prereq=True; logger.info("Weed Seeds verbraucht.")
                                     else: logger.error("Fehler: Seeds entfernen")
                                 else: logger.info("Fehlt: 'Weed Seeds'.")
                             elif item_to_interact.state in ['giessen', 'readyToEarn', 'growing']: interaction_possible_prereq = True
                             if interaction_possible_prereq: item_to_interact.interact() # Führe Aktion im Item aus
                         # else: Langes Drücken wird im Update behandelt
                    potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False # Immer Reset

                # 2. Drag & Drop Ende?
                if is_dragging:
                     world_x,world_y=camera.screen_to_world(mouse_pos_screen[0],mouse_pos_screen[1])
                     snapped_tl_x=(world_x//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE; snapped_tl_y=(world_y//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE
                     snapped_center_x=snapped_tl_x+PLACED_ITEM_SIZE/2; snapped_center_y=snapped_tl_y+PLACED_ITEM_SIZE/2
                     can_place=True; temp_rect=pygame.Rect(0,0,PLACED_ITEM_SIZE,PLACED_ITEM_SIZE); temp_rect.center=(snapped_center_x,snapped_center_y)
                     for item in placed_items:
                         if temp_rect.colliderect(item.rect): can_place=False; logger.info(f"Platzieren blockiert."); break
                     if can_place:
                         if inventory.remove_item(dragged_item_type, 1):
                             new_item = PlacedItem(snapped_center_x, snapped_center_y, PLACED_ITEM_SIZE, PLACED_ITEM_COLOR, dragged_item_type, state='ohneErde')
                             all_sprites.add(new_item); placed_items.add(new_item); logger.info(f"'{dragged_item_type}' platziert.")
                         else: logger.warning(f"Platzieren fehlgeschlagen: Item nicht im Inventar?")
                     is_dragging = False; dragged_item_type = None; dragged_item_image = None

    # --- Update ---
    player.update(keys, camera.get_current_screen_rect())
    camera.update(player)
    npcs.update()
    placed_items.update(dt) # WICHTIG: Update für platzierte Items (Timer!)

    # --- Aufheben-Logik (Langes Halten) ---
    if interaction_active and potential_interaction_item:
        hold_duration = time.time() - interaction_start_time # Aktuelle Haltedauer
        # Prüfe, ob Ziel noch gültig ist
        player_cx=player.rect.centerx; player_cy=player.rect.centery; current_target_valid=False
        if potential_interaction_item.alive():
             item_cx=potential_interaction_item.rect.centerx; item_cy=potential_interaction_item.rect.centery
             distance=math.sqrt((player_cx - item_cx)**2 + (player_cy - item_cy)**2)
             if distance < INTERACTION_RADIUS + potential_interaction_item.rect.width / 2: # Prüfe ob noch im Radius
                 is_still_closest = True # Prüfen ob immer noch das NÄCHSTE im Radius
                 for other_item in placed_items:
                      if other_item==potential_interaction_item: continue
                      other_cx=other_item.rect.centerx; other_cy=other_item.rect.centery; other_distance=math.sqrt((player_cx-other_cx)**2 + (player_cy-other_cy)**2)
                      if other_distance < distance and other_distance < INTERACTION_RADIUS+other_item.rect.width/2: is_still_closest = False; break
                 if is_still_closest: current_target_valid = True

        if current_target_valid:
            # Prüfe, ob Schwelle für langes Drücken (Aufheben) erreicht
            if hold_duration >= LONG_PRESS_THRESHOLD:
                logger.info(f"LANGES DRÜCKEN ({hold_duration:.2f}s) -> Pickup '{potential_interaction_item.item_type}'")
                item_type_to_add = potential_interaction_item.item_type
                if inventory.add_item(item_type_to_add, 1): # Füge zum Inventar hinzu
                    logger.info(f"'{item_type_to_add}' zum Inventar hinzugefügt.")
                    potential_interaction_item.kill(); logger.info(f"Platziertes Item entfernt.")
                else: logger.warning(f"Aufheben fehlgeschlagen: Inventar voll?")
                potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False # Reset nach Aktion
            # else: Noch nicht lange genug gehalten, Timer läuft weiter... (nichts tun)
        else:
             # Ziel ungültig geworden während des Haltens
             if potential_interaction_item: logger.info(f"Interaktions-Ziel verloren."); potential_interaction_item = None; interaction_start_time = 0.0; interaction_active = False # Reset

    # --- Draw ---
    if background_image: screen.blit(background_image, (0, 0))
    else: screen.fill(BLACK)
    for sprite in all_sprites:
        if camera.get_current_screen_rect().colliderect(sprite.rect): screen.blit(sprite.image, camera.apply(sprite))
    if interaction_active: # Interaktionsradius + Fortschrittsbalken
        try:
            player_screen_rect=camera.apply(player); player_screen_center=player_screen_rect.center
            pygame.draw.circle(screen, WHITE, player_screen_center, INTERACTION_RADIUS, 1)
            if potential_interaction_item and interaction_start_time > 0:
                 hold_duration = time.time() - interaction_start_time
                 progress = min(1.0, hold_duration / LONG_PRESS_THRESHOLD)
                 if progress > 0:
                     bar_width=50; bar_height=5; bar_x=player_screen_center[0]-bar_width//2; bar_y=player_screen_rect.top-bar_height-3
                     pygame.draw.rect(screen,(50,50,50),(bar_x,bar_y,bar_width,bar_height)); pygame.draw.rect(screen,(200,0,0),(bar_x,bar_y,int(bar_width*progress),bar_height))
        except Exception as e: logger.error(f"Fehler Zeichnen Interaktionsradius: {e}")
    try: # UI Text
        if pygame.font.get_init(): font=pygame.font.Font(None, 28); pos_text_str=f"P(TL):({player.rect.x},{player.rect.y}) C:({camera.camera_rect.x},{camera.camera_rect.y})"; pos_text_surface=font.render(pos_text_str,True,WHITE); screen.blit(pos_text_surface, (10, 10))
    except Exception as e: logger.error(f"Fehler UI-Text: {e}")
    try: # Inventar
        inventory.display(screen, inventory_pos)
    except Exception as e: logger.error(f"Fehler Inventar-Anzeige: {e}")
    if is_dragging and dragged_item_image: # Gezogenes Item (Vorschau)
        world_x,world_y=camera.screen_to_world(mouse_pos_screen[0],mouse_pos_screen[1]); snapped_tl_x=(world_x//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE; snapped_tl_y=(world_y//PLACED_ITEM_SIZE)*PLACED_ITEM_SIZE
        snapped_center_x=snapped_tl_x+PLACED_ITEM_SIZE/2; snapped_center_y=snapped_tl_y+PLACED_ITEM_SIZE/2; temp_snap_rect_world=pygame.Rect(0,0,1,1); temp_snap_rect_world.center=(snapped_center_x,snapped_center_y)
        snapped_screen_center=camera.apply_rect(temp_snap_rect_world).center; drag_rect=dragged_item_image.get_rect(center=snapped_screen_center); screen.blit(dragged_item_image, drag_rect)
    # Interaktions-Button zeichnen (NUR auf Android)
    if platform_utils.IS_ANDROID:
        if button_image_normal: screen.blit(button_image_normal, BUTTON_RECT.topleft)
        else: pygame.draw.rect(screen, BUTTON_COLOR_NORMAL, BUTTON_RECT); pygame.draw.rect(screen, BUTTON_BORDER_COLOR, BUTTON_RECT, 2)
        try: # Text
            if pygame.font.get_init(): btn_font=pygame.font.Font(None, 18); btn_text=btn_font.render("Interact", True, WHITE); btn_text_rect=btn_text.get_rect(center=BUTTON_RECT.center); screen.blit(btn_text, btn_text_rect)
        except Exception as e: logger.error(f"Fehler Button-Text: {e}")

    pygame.display.flip()

# --- Spiel beenden ---
logger.info("Spiel-Loop beendet.")
# Speichern...
logger.info(f"Speichere Inventar..."); 
try: inventory.save_inventory()
except Exception as e: logger.error(f"Fehler Inv speichern: {e}", exc_info=True)
logger.info(f"Speichere Spielerposition..."); 
try: player_pos_data = {'x': player.rect.x, 'y': player.rect.y}; save_data(player_pos_data, PLAYER_POS_SAVE_FILE)
except Exception as e: logger.error(f"Fehler Pos speichern: {e}", exc_info=True)
logger.info(f"Speichere platzierte Items..."); 
try:
    placed_items_to_save = [{'type':item.item_type, 'x':item.rect.centerx, 'y':item.rect.centery, 'state':item.state, 'timer_end':item.timer_end_timestamp} for item in placed_items]
    save_data(placed_items_to_save, PLACED_ITEMS_SAVE_FILE); logger.info(f"{len(placed_items_to_save)} platzierte Items gespeichert.")
except Exception as e: logger.error(f"Fehler Items speichern: {e}", exc_info=True)

pygame.quit(); logger.info("Pygame beendet."); sys.exit()