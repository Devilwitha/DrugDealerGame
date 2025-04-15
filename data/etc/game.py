# game.py (Komplett, Refaktoriert & Korrigiert v2)
# Stand: 2025-04-15
# Formatiert für maximale Lesbarkeit

# ========= SYSTEM PATH & MINIMALES SETUP =========
import sys
import os
import logging
import time
import traceback
import pygame

# --- Projekt-Root ermitteln ---
try:
    script_dir_game = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir_game = os.path.abspath(".")
project_root_dir_game = os.path.abspath(os.path.join(script_dir_game, "..", ".."))
if project_root_dir_game not in sys.path:
    sys.path.insert(0, project_root_dir_game)
    print(f"DEBUG [game.py]: '{project_root_dir_game}' zum sys.path hinzugefügt.")

# --- Minimales Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)
logger = logging.getLogger(__name__)

# ========= IMPORT DER EIGENEN MODULE =========
try:
    from data.etc import config
    from data.etc import setup
    from data.etc import persistence
    from data.etc import ui_manager
    from data.etc import items
    from data.etc import inventory as inventory_module
    from data.etc import platform_utils
    from data.etc import dialog
    # Importiere die NPC Klasse direkt für type checking
    from data.etc.npc import NPC # <-- HINZUGEFÜGT
    # Importiere spezifische Minispiel-Funktionen
    from data.miniGame.zipWeed.zipWeed import run_zip_weed_game

except ImportError as e:
    logger.critical(f"FATAL ERROR: Modul '{e.name}' nicht gefunden beim Import in game.py. Prüfe Pfade und PYTHONPATH. sys.path: {sys.path}. Traceback:\n{traceback.format_exc()}", exc_info=True)
    if pygame.get_init(): pygame.quit()
    sys.exit(f"FEHLER: Modul '{e.name}' fehlt. Spiel kann nicht starten.")
except Exception as e:
    logger.critical(f"FATAL ERROR: Unerwarteter Fehler beim Importieren eigener Module in game.py. Traceback:\n{traceback.format_exc()}", exc_info=True)
    if pygame.get_init(): pygame.quit()
    sys.exit("FEHLER: Unerwarteter Import-Fehler. Spiel kann nicht starten.")


# ========= SPIEL INITIALISIEREN =========
logger.info("Initialisiere Spiel über setup.initialize_game...")
game_data = setup.initialize_game(project_root_dir_game)

if game_data is None:
    logger.critical("Spielinitialisierung fehlgeschlagen (setup gab None zurück). Programm wird beendet.")
    if pygame.get_init(): pygame.quit()
    sys.exit("FEHLER: Initialisierung fehlgeschlagen.")


# ========= SPIELOBJEKTE & ZUSTAND AUSPACKEN =========
try:
    screen = game_data.get('screen')
    clock = game_data.get('clock')
    fonts = game_data.get('fonts', {})
    assets = game_data.get('assets', {})
    settings = game_data.get('settings', {})
    layout = game_data.get('layout', {})
    player = game_data.get('player')
    player_money = game_data.get('player_money', 0.0)
    camera = game_data.get('camera')
    inventory = game_data.get('inventory')
    all_sprites = game_data.get('all_sprites')
    placed_items = game_data.get('placed_items')
    npcs = game_data.get('npcs')
    locale_set = game_data.get('locale_set', False)
    screen_width = game_data.get('screen_width')
    screen_height = game_data.get('screen_height')

    if not all([screen, clock, player, camera, inventory, all_sprites, placed_items, npcs]):
         raise ValueError("Einige kritische Spielobjekte fehlen nach der Initialisierung!")

    background_image = assets.get('background')
    item_icons = assets.get('item_icons', {})
    button_rect = layout.get('button_rect')
    inv_pos = layout.get('inv_pos')

except KeyError as e:
    logger.critical(f"Fehlender Schlüssel im von setup.py zurückgegebenen game_data: {e}", exc_info=True)
    if pygame.get_init(): pygame.quit()
    sys.exit("FEHLER: Unvollständige Initialisierungsdaten.")
except ValueError as e:
     logger.critical(str(e), exc_info=True)
     if pygame.get_init(): pygame.quit()
     sys.exit("FEHLER: Unvollständige Initialisierung.")


# ========= SPIEL-LOOP ZUSTANDSVARIABLEN =========
running = True
current_game_state = config.GAME_STATE_PLAY
active_npc = None
current_dialog_node_id = None
clickable_ui_elements = []
ui_exit_button_rect = None
is_dragging = False
dragged_item_type = None
dragged_item_image = None
interaction_active = False
interaction_start_time = 0.0
potential_interaction_target = None
target_type = None
interaction_press_event_handled = False


# ========= HILFSFUNKTIONEN für den Game Loop =========

def find_interaction_target(player_obj, items_group, npc_group, radius):
    """Findet das nächstgelegene interagierbare Objekt (Item oder NPC) im Radius."""
    closest_target = None
    min_dist_sq = (radius ** 2)
    player_cx = player_obj.rect.centerx
    player_cy = player_obj.rect.centery
    target_type_found = None
    for item in items_group:
        dist_sq = (player_cx - item.rect.centerx)**2 + (player_cy - item.rect.centery)**2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            closest_target = item
            target_type_found = "item"
    for npc_obj in npc_group:
        dist_sq = (player_cx - npc_obj.rect.centerx)**2 + (player_cy - npc_obj.rect.centery)**2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            closest_target = npc_obj
            target_type_found = "npc"
    return closest_target, target_type_found

def handle_npc_interaction(npc_target, current_inventory):
    """Startet einen Dialog oder eine andere NPC-spezifische Aktion."""
    global current_game_state, current_dialog_node_id, active_npc

    # Verwende die direkt importierte NPC Klasse für den Check
    if not isinstance(npc_target, NPC): # <-- KORRIGIERT
        logger.warning("handle_npc_interaction mit ungültigem Target aufgerufen.")
        return

    logger.info(f"Interagiere mit NPC '{npc_target.npc_type}' ID: {npc_target.dialog_id}")
    active_npc = npc_target

    if not active_npc.dialog_id:
        logger.warning(f"NPC '{active_npc.npc_type}' hat keine Dialog-ID.")
        active_npc = None
        play_game_sound("error")
        return

    start_node_id = active_npc.dialog_id
    if active_npc.npc_type == "client" and not current_inventory.has_item(items.ITEM_WEED, 1):
        alternative_node = "client_nichts_da"
        if dialog.get_dialog_node(alternative_node):
            start_node_id = alternative_node
            logger.info("Client angesprochen, aber kein Weed dabei. Starte mit Knoten: " + start_node_id)
        else:
             logger.warning(f"Alternativknoten '{alternative_node}' für Client nicht gefunden.")

    current_dialog_node_id = start_node_id
    current_game_state = config.GAME_STATE_DIALOG
    logger.info(f"-> Wechsle zu GAME_STATE_DIALOG (Startknoten: {current_dialog_node_id})")

def play_game_sound(sound_name):
    """Spielt einen Sound aus dem Assets-Dictionary ab."""
    sound_to_play = assets.get('sounds', {}).get(sound_name)
    if sound_to_play:
        try:
            sound_to_play.play()
        except Exception as e:
            logger.error(f"Fehler beim Abspielen von Sound '{sound_name}': {e}", exc_info=False)
    else:
        # Wenn der 'error' Sound fehlt, logge das als Warnung
        if sound_name == 'error':
             logger.warning(f"Sound '{sound_name}' (error.wav?) nicht gefunden oder nicht geladen.")
        else:
             logger.debug(f"Angeforderter Sound '{sound_name}' nicht gefunden oder nicht geladen.")


# ========= HAUPT-SPIELSCHLEIFE =========
logger.info("Initialisierung abgeschlossen, starte Spiel-Loop...")

while running:
    try:
        # --- Frame Setup ---
        dt = clock.tick(config.FPS) / 1000.0
        mouse_pos_screen = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        interaction_press_event_handled_this_frame = False # Zurücksetzen für jeden Frame

        # === EVENT HANDLING ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False; logger.info("QUIT Event."); continue

            # --- UI Event Handling (Mausklicks in UI-Zuständen) ---
            ui_result = None
            click_handled_by_ui = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Nur prüfen, wenn wir uns in einem UI-Zustand befinden
                if current_game_state == config.GAME_STATE_DIALOG:
                    ui_result = ui_manager.handle_dialog_click(mouse_pos_screen, clickable_ui_elements, inventory)
                    click_handled_by_ui = ui_result is not None
                elif current_game_state == config.GAME_STATE_SHOP:
                    ui_result = ui_manager.handle_shop_click(mouse_pos_screen, clickable_ui_elements, ui_exit_button_rect, inventory, player_money, play_game_sound)
                    click_handled_by_ui = ui_result is not None
                elif current_game_state == config.GAME_STATE_SELL:
                    sell_btn_rect_arg = clickable_ui_elements[0][0] if clickable_ui_elements else None
                    ui_result = ui_manager.handle_sell_click(mouse_pos_screen, sell_btn_rect_arg, ui_exit_button_rect, inventory, play_game_sound)
                    click_handled_by_ui = ui_result is not None

                # --- Ergebnis des UI-Klicks verarbeiten ---
                if ui_result:
                    logger.debug(f"UI Click Result: {ui_result}")
                    # 1. Zustandswechsel prüfen
                    next_state = ui_result.get('next_state')
                    if next_state:
                        previous_state = current_game_state
                        current_game_state = next_state
                        # Kontext zurücksetzen beim Verlassen eines UI-Zustands
                        if current_game_state == config.GAME_STATE_PLAY:
                            active_npc = None; current_dialog_node_id = None; clickable_ui_elements = []; ui_exit_button_rect = None; logger.info(f"Zurück zum Spiel-Zustand von {previous_state}.")
                        else: # Reset für den neuen UI-Zustand
                             clickable_ui_elements = []; ui_exit_button_rect = None; logger.info(f"Wechsle von {previous_state} zu UI-Zustand: {current_game_state}")
                    # 2. Dialog-Navigation prüfen
                    next_node = ui_result.get('next_dialog_node')
                    if next_node: current_dialog_node_id = next_node; clickable_ui_elements = []; logger.debug(f"Nächster Dialogknoten: {current_dialog_node_id}")
                    # 3. Geldänderung verarbeiten
                    money_change = ui_result.get('money_change')
                    if money_change is not None: player_money = round(player_money + money_change, 2); logger.info(f"Geld geändert um {money_change:.2f}. Neues Geld: {player_money:.2f}")
                    # 4. Spezielle Aktionen aus UI (Minispiel)
                    if ui_result.get('action') == 'start_zipweed':
                         initial_weed = ui_result.get('initial_weed', 0); initial_grips = ui_result.get('initial_grips', 0)
                         if initial_weed > 0 and initial_grips > 0:
                            logger.info("Speichere Spielstand vor Start von ZipWeed (UI)...")
                            try:
                                save_data_dir = os.path.join(project_root_dir_game, config.SAVE_DATA_DIR_NAME) # Korrekter Pfad ohne doppeltes 'data'
                                player_pos_save_file = os.path.join(save_data_dir, config.PLAYER_POS_SAVE_FILENAME)
                                placed_items_save_file = os.path.join(save_data_dir, config.PLACED_ITEMS_SAVE_FILENAME)
                                inventory.save_inventory(); persistence.save_data({'x': player.rect.x, 'y': player.rect.y, 'money': player_money}, player_pos_save_file); items.save_placed_items(placed_items, placed_items_save_file)
                            except Exception as e_save: logger.error(f"Fehler beim Speichern vor ZipWeed: {e_save}", exc_info=True); play_game_sound("error"); continue
                            try:
                                final_weed, final_grips, packed_count, outcome = run_zip_weed_game(screen, initial_weed, initial_grips, "Normal", settings)
                                logger.info(f"ZipWeed beendet: Weed={final_weed}, Grips={final_grips}, Packed={packed_count}, Outcome={outcome}")
                                weed_consumed = initial_weed - final_weed; grips_consumed = initial_grips - final_grips
                                if weed_consumed > 0: inventory.remove_item(items.ITEM_WEED, weed_consumed)
                                if grips_consumed > 0: inventory.remove_item(items.ITEM_GRIPS, grips_consumed)
                                if packed_count > 0 and not inventory.add_item(items.ITEM_VERPACKTES_WEED, packed_count): logger.warning("Konnte nicht alle 'VerpacktesWeed' hinzufügen.")
                            except Exception as e_minigame: logger.error(f"Fehler während Ausführung von ZipWeed: {e_minigame}", exc_info=True); play_game_sound("error")
                         else: logger.warning("ZipWeed Start-Aktion, aber initiale Ressourcen 0?"); play_game_sound("error")

            # --- Gameplay Event Handling (nur wenn nicht von UI behandelt) ---
            if not click_handled_by_ui:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if current_game_state != config.GAME_STATE_PLAY:
                            logger.info(f"ESC: Schließe {current_game_state}.")
                            current_game_state = config.GAME_STATE_PLAY; active_npc = None; current_dialog_node_id = None; clickable_ui_elements = []; ui_exit_button_rect = None
                        elif not platform_utils.IS_ANDROID: running = False; logger.info("ESC im Spiel (Desktop): Beende.")
                    elif event.key == pygame.K_SPACE and current_game_state == config.GAME_STATE_PLAY and not platform_utils.IS_ANDROID:
                        if not interaction_active and potential_interaction_target:
                            interaction_active = True; interaction_press_event_handled_this_frame = True; interaction_start_time = time.time()
                            target_id = getattr(potential_interaction_target, 'item_type', getattr(potential_interaction_target, 'npc_type', '?'))
                            logger.info(f"Start Interaktion (SPACE gedrückt) mit {target_type} '{target_id}'")
                            interaction_press_event_handled = True # Flag setzen

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE and interaction_active and not platform_utils.IS_ANDROID:
                        if current_game_state == config.GAME_STATE_PLAY and potential_interaction_target:
                            if time.time() - interaction_start_time < config.LONG_PRESS_THRESHOLD: # Kurzer Druck?
                                logger.debug(f"Kurze Interaktion (SPACE) mit {target_type}")
                                if target_type == "item":
                                    item_interaction_result = potential_interaction_target.interact(inventory, play_game_sound)
                                    if isinstance(item_interaction_result, tuple) and len(item_interaction_result) == 2:
                                        action_taken, result_data = item_interaction_result
                                        if result_data and result_data.get('action') == 'start_zipweed':
                                            initial_weed = result_data.get('initial_weed', 0); initial_grips = result_data.get('initial_grips', 0)
                                            if initial_weed > 0 and initial_grips > 0:
                                                logger.info("Speichere Spielstand vor Start von ZipWeed (Item)...")
                                                try:
                                                     save_data_dir = os.path.join(project_root_dir_game, config.SAVE_DATA_DIR_NAME) # Korrekter Pfad
                                                     player_pos_save_file = os.path.join(save_data_dir, config.PLAYER_POS_SAVE_FILENAME)
                                                     placed_items_save_file = os.path.join(save_data_dir, config.PLACED_ITEMS_SAVE_FILENAME)
                                                     inventory.save_inventory(); persistence.save_data({'x': player.rect.x, 'y': player.rect.y, 'money': player_money}, player_pos_save_file); items.save_placed_items(placed_items, placed_items_save_file)
                                                except Exception as e_save: logger.error(f"Fehler Speichern vor ZipWeed: {e_save}", exc_info=True); play_game_sound("error"); continue
                                                try:
                                                    final_weed, final_grips, packed_count, outcome = run_zip_weed_game(screen, initial_weed, initial_grips, "Normal", settings)
                                                    logger.info(f"ZipWeed beendet: Weed={final_weed}, Grips={final_grips}, Packed={packed_count}, Outcome={outcome}")
                                                    weed_consumed = initial_weed - final_weed; grips_consumed = initial_grips - final_grips
                                                    if weed_consumed > 0: inventory.remove_item(items.ITEM_WEED, weed_consumed)
                                                    if grips_consumed > 0: inventory.remove_item(items.ITEM_GRIPS, grips_consumed)
                                                    if packed_count > 0 and not inventory.add_item(items.ITEM_VERPACKTES_WEED, packed_count): logger.warning("Konnte nicht alle 'VerpacktesWeed' hinzufügen.")
                                                except Exception as e_minigame: logger.error(f"Fehler während Ausführung von ZipWeed: {e_minigame}", exc_info=True); play_game_sound("error")
                                            else: logger.warning("ZipWeed Start-Aktion (Item), aber initiale Ressourcen 0?"); play_game_sound("error")
                                elif target_type == "npc": handle_npc_interaction(potential_interaction_target, inventory)
                        interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Linksklick im Play State
                    if current_game_state == config.GAME_STATE_PLAY:
                        if platform_utils.IS_ANDROID and button_rect and button_rect.collidepoint(mouse_pos_screen):
                            if not interaction_active and potential_interaction_target:
                                interaction_active = True; interaction_press_event_handled_this_frame = True; interaction_start_time = time.time()
                                target_id = getattr(potential_interaction_target, 'item_type', getattr(potential_interaction_target, 'npc_type', '?'))
                                logger.info(f"Start Interaktion (Android Button gedrückt) mit {target_type} '{target_id}'")
                                interaction_press_event_handled = True
                        elif not is_dragging and (not platform_utils.IS_ANDROID or not (button_rect and button_rect.collidepoint(mouse_pos_screen))):
                            inv_list_display = inventory.get_item_list_for_display(); s_box_size = inventory_module.get_scaled_box_size(); s_padding = inventory_module.get_scaled_padding()
                            for i in range(1, inventory_module.MAX_SLOTS):
                                slot_x = inv_pos[0] + i * (s_box_size + s_padding); slot_y = inv_pos[1]; slot_rect = pygame.Rect(slot_x, slot_y, s_box_size, s_box_size)
                                item_display_index = i - 1
                                if slot_rect.collidepoint(mouse_pos_screen) and item_display_index < len(inv_list_display):
                                    item_name_inv, item_qty_inv = inv_list_display[item_display_index]
                                    if item_name_inv in items.PLACEABLE_ITEMS and item_qty_inv > 0:
                                        is_dragging = True; dragged_item_type = item_name_inv
                                        drag_image_src = assets['item_icons'].get(dragged_item_type)
                                        if not drag_image_src: start_state = 'default' if dragged_item_type == items.ITEM_VERPACKSTATION else items.STATE_OHNE_ERDE; drag_image_src = assets.get('placed_item_images',{}).get(dragged_item_type,{}).get(start_state)
                                        if drag_image_src:
                                             try: dragged_item_image = pygame.transform.smoothscale(drag_image_src.copy(), (items.PLACED_ITEM_SIZE, items.PLACED_ITEM_SIZE))
                                             except Exception as e_scale_drag: logger.error(f"Fehler Skalieren Drag-Image: {e_scale_drag}"); dragged_item_image = assets.get('fallback_placed_image')
                                        else: dragged_item_image = assets.get('fallback_placed_image'); logger.warning(f"Kein Quellbild für Drag-Vorschau von '{dragged_item_type}'.")
                                        logger.info(f"Starte Drag & Drop für: {dragged_item_type}"); break

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: # Linksklick loslassen
                    if interaction_active and interaction_press_event_handled and platform_utils.IS_ANDROID:
                        if current_game_state == config.GAME_STATE_PLAY and potential_interaction_target:
                            if time.time() - interaction_start_time < config.LONG_PRESS_THRESHOLD: # Kurzer Druck?
                                logger.debug(f"Kurze Interaktion (Button) mit {target_type}")
                                if target_type == "item":
                                    item_interaction_result = potential_interaction_target.interact(inventory, play_game_sound)
                                    if isinstance(item_interaction_result, tuple) and len(item_interaction_result) == 2:
                                        action_taken, result_data = item_interaction_result
                                        if result_data and result_data.get('action') == 'start_zipweed':
                                             initial_weed = result_data.get('initial_weed', 0); initial_grips = result_data.get('initial_grips', 0)
                                             if initial_weed > 0 and initial_grips > 0:
                                                logger.info("Speichere Spielstand vor Start von ZipWeed (Item/Button)...")
                                                try:
                                                     save_data_dir = os.path.join(project_root_dir_game, config.SAVE_DATA_DIR_NAME) # Korrekter Pfad
                                                     player_pos_save_file = os.path.join(save_data_dir, config.PLAYER_POS_SAVE_FILENAME)
                                                     placed_items_save_file = os.path.join(save_data_dir, config.PLACED_ITEMS_SAVE_FILENAME)
                                                     inventory.save_inventory(); persistence.save_data({'x': player.rect.x, 'y': player.rect.y, 'money': player_money}, player_pos_save_file); items.save_placed_items(placed_items, placed_items_save_file)
                                                except Exception as e_save: logger.error(f"Fehler Speichern vor ZipWeed: {e_save}", exc_info=True); play_game_sound("error"); continue
                                                try:
                                                    final_weed, final_grips, packed_count, outcome = run_zip_weed_game(screen, initial_weed, initial_grips, "Normal", settings)
                                                    logger.info(f"ZipWeed beendet: Weed={final_weed}, Grips={final_grips}, Packed={packed_count}, Outcome={outcome}")
                                                    weed_consumed = initial_weed - final_weed; grips_consumed = initial_grips - final_grips
                                                    if weed_consumed > 0: inventory.remove_item(items.ITEM_WEED, weed_consumed)
                                                    if grips_consumed > 0: inventory.remove_item(items.ITEM_GRIPS, grips_consumed)
                                                    if packed_count > 0 and not inventory.add_item(items.ITEM_VERPACKTES_WEED, packed_count): logger.warning("Konnte nicht alle 'VerpacktesWeed' hinzufügen.")
                                                except Exception as e_minigame: logger.error(f"Fehler während Ausführung von ZipWeed: {e_minigame}", exc_info=True); play_game_sound("error")
                                             else: logger.warning("ZipWeed Start-Aktion (Item/Button), aber initiale Ressourcen 0?"); play_game_sound("error")
                                elif target_type == "npc": handle_npc_interaction(potential_interaction_target, inventory)
                        interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False
                    elif is_dragging:
                        inv_rect_check = pygame.Rect(inv_pos[0], inv_pos[1], inventory_module.get_inventory_display_width(), inventory_module.get_scaled_box_size())
                        button_collide_check = platform_utils.IS_ANDROID and button_rect and button_rect.collidepoint(mouse_pos_screen)
                        can_drop_here = not inv_rect_check.collidepoint(mouse_pos_screen) and not button_collide_check
                        if can_drop_here:
                            world_x, world_y = camera.screen_to_world(*mouse_pos_screen); snapped_center_x = round(world_x / items.PLACED_ITEM_SIZE) * items.PLACED_ITEM_SIZE + items.PLACED_ITEM_SIZE / 2; snapped_center_y = round(world_y / items.PLACED_ITEM_SIZE) * items.PLACED_ITEM_SIZE + items.PLACED_ITEM_SIZE / 2; snapped_tl_x = snapped_center_x - items.PLACED_ITEM_SIZE / 2; snapped_tl_y = snapped_center_y - items.PLACED_ITEM_SIZE / 2
                            can_place = True; temp_rect = pygame.Rect(snapped_tl_x, snapped_tl_y, items.PLACED_ITEM_SIZE, items.PLACED_ITEM_SIZE)
                            for item in placed_items:
                                if temp_rect.colliderect(item.rect): can_place = False; logger.info(f"Platzieren blockiert durch '{item.item_type}'."); break
                            if can_place:
                                if inventory.remove_item(dragged_item_type, 1):
                                    try:
                                        images_for_item = assets.get('placed_item_images', {}).get(dragged_item_type, {}); fallback_img = assets.get('fallback_placed_image'); start_state = 'default' if dragged_item_type == items.ITEM_VERPACKSTATION else items.STATE_OHNE_ERDE; grow_time = items.DEFAULT_GROW_TIME_SECONDS if dragged_item_type == items.ITEM_BLUMENTOPF else 0
                                        new_item = items.PlacedItem(snapped_center_x, snapped_center_y, dragged_item_type, images_for_item, fallback_img, grow_time, start_state, None)
                                        if not new_item or not new_item.rect: raise ValueError("Item Erstellung fehlgeschlagen")
                                        all_sprites.add(new_item); placed_items.add(new_item); logger.info(f"'{dragged_item_type}' platziert."); play_game_sound("place_item")
                                    except Exception as e_place: logger.error(f"FEHLER Platzieren '{dragged_item_type}': {e_place}", exc_info=True); inventory.add_item(dragged_item_type, 1); play_game_sound("error")
                                else: logger.warning(f"Platzieren fehlgeschlagen: Item entfernen?"); play_game_sound("error")
                            else: play_game_sound("error") # Platz blockiert
                        else: logger.debug("Drag&Drop über UI beendet.")
                        is_dragging = False; dragged_item_type = None; dragged_item_image = None
                    elif interaction_active and interaction_press_event_handled: # Reset falls Button gedrückt aber Klick ins Leere etc.
                           interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False

        # --- Ende der Event-Verarbeitung für diesen Frame ---


        # === UPDATES (Logik pro Frame) ===
        if current_game_state == config.GAME_STATE_PLAY:
            # 1. Interaktionsziel finden
            potential_interaction_target, target_type = find_interaction_target(player, placed_items, npcs, config.INTERACTION_RADIUS)
            interaction_possible_now = (potential_interaction_target is not None)

            # 2. Interaktion abbrechen, wenn Ziel verloren (nur wenn nicht gerade aktiv aufgehoben wird?)
            if interaction_active and not interaction_possible_now and time.time() - interaction_start_time < config.LONG_PRESS_THRESHOLD:
                 interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False

            # 3. Spielobjekte updaten
            player.update(keys, camera.get_current_screen_rect())
            camera.update(player)
            npcs.update()
            placed_items.update(dt) # Wichtig für Timer etc.

            # 4. Aufheben-Logik (Langes Drücken auswerten)
            if (interaction_active and target_type == "item" and
                    potential_interaction_target and potential_interaction_target in placed_items and
                    time.time() - interaction_start_time >= config.LONG_PRESS_THRESHOLD):
                item_to_pickup = potential_interaction_target
                if item_to_pickup.item_type in items.PLACEABLE_ITEMS:
                    if inventory.add_item(item_to_pickup.item_type, 1):
                        logger.info(f"'{item_to_pickup.item_type}' aufgehoben (Long Press)."); item_to_pickup.kill(); play_game_sound("pickup")
                        interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False; potential_interaction_target = None; target_type = None
                    else: logger.warning(f"Aufheben fehlgeschlagen: Inventar voll?"); play_game_sound("error"); interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False
                else: logger.warning(f"Item '{item_to_pickup.item_type}' nicht aufhebbar."); interaction_active = False; interaction_start_time = 0.0; interaction_press_event_handled = False


        # === ZEICHNEN ===
        # 1. Hintergrund / UI-Overlay
        if current_game_state == config.GAME_STATE_PLAY:
            if background_image: screen.blit(background_image, (0, 0))
            else: screen.fill(config.BLACK)
        else: # UI-Overlay Modus
            if background_image: screen.blit(background_image, (0, 0))
            else: screen.fill(config.BLACK)
            dark_overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA); dark_overlay.fill((0, 0, 0, 150)); screen.blit(dark_overlay, (0, 0))

        # 2. Zeichnen im Spielzustand (Sprites, Interaktion, Gameplay-UI)
        if current_game_state == config.GAME_STATE_PLAY:
            # Sprites zeichnen
            for sprite in all_sprites:
                try:
                    if camera.get_current_screen_rect().colliderect(sprite.rect) and hasattr(sprite, 'image') and sprite.image: screen.blit(sprite.image, camera.apply(sprite))
                except Exception: pass # Fehler sollten schon geloggt sein
            # Interaktionsanzeige
            if potential_interaction_target:
                 try:
                    target_rect_screen = camera.apply_rect(potential_interaction_target.rect); pygame.draw.rect(screen, config.YELLOW, target_rect_screen, 2)
                    if interaction_active and target_type == "item" and interaction_start_time > 0 and time.time() - interaction_start_time < config.LONG_PRESS_THRESHOLD:
                        progress = min(1.0, (time.time() - interaction_start_time) / config.LONG_PRESS_THRESHOLD)
                        if progress > 0: bar_w = 50; bar_h = 5; bar_x = target_rect_screen.centerx - bar_w // 2; bar_y = target_rect_screen.top - bar_h - 5; pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h)); pygame.draw.rect(screen, config.RED, (bar_x, bar_y, int(bar_w * progress), bar_h))
                 except Exception: pass # Fehler sollten schon geloggt sein
            # UI-Texte
            if fonts.get('ui'): ui_font = fonts['ui']; screen.blit(ui_font.render(f"FPS: {clock.get_fps():.1f}", True, config.WHITE), (10, 10)); # etc.
            # Inventar
            if inventory: inventory.display(screen, inv_pos, item_icons, fonts['inventory'], player_money, locale_set)
            # Drag-Vorschau
            if is_dragging and dragged_item_image:
                 try:
                    world_x_drag, world_y_drag = camera.screen_to_world(*mouse_pos_screen); snapped_center_x = round(world_x_drag / items.PLACED_ITEM_SIZE) * items.PLACED_ITEM_SIZE + items.PLACED_ITEM_SIZE / 2; snapped_center_y = round(world_y_drag / items.PLACED_ITEM_SIZE) * items.PLACED_ITEM_SIZE + items.PLACED_ITEM_SIZE / 2; snapped_tl_x = snapped_center_x - items.PLACED_ITEM_SIZE / 2; snapped_tl_y = snapped_center_y - items.PLACED_ITEM_SIZE / 2; snapped_rect_screen_drag = camera.apply_rect(pygame.Rect(snapped_tl_x, snapped_tl_y, items.PLACED_ITEM_SIZE, items.PLACED_ITEM_SIZE))
                    dragged_item_image.set_alpha(180); drag_rect_preview = dragged_item_image.get_rect(center=snapped_rect_screen_drag.center); screen.blit(dragged_item_image, drag_rect_preview); dragged_item_image.set_alpha(255); pygame.draw.rect(screen, config.WHITE, snapped_rect_screen_drag, 1)
                 except Exception: pass # Fehler sollten schon geloggt sein
            # Android Button
            if platform_utils.IS_ANDROID and button_rect:
                 try:
                    button_img_to_draw = assets.get('button_image'); screen.blit(button_img_to_draw, button_rect.topleft) if button_img_to_draw else pygame.draw.rect(screen, config.BUTTON_COLOR_NORMAL, button_rect); pygame.draw.rect(screen, config.BUTTON_BORDER_COLOR, button_rect, 2)
                 except Exception: pass # Fehler sollten schon geloggt sein

        # 3. Zeichnen in UI-Zuständen (ruft ui_manager auf)
        elif current_game_state == config.GAME_STATE_DIALOG: clickable_ui_elements = ui_manager.draw_dialog_ui(screen, screen_width, screen_height, current_dialog_node_id, fonts); ui_exit_button_rect = None
        elif current_game_state == config.GAME_STATE_SHOP: clickable_ui_elements, ui_exit_button_rect = ui_manager.draw_shop_ui(screen, screen_width, screen_height, player_money, locale_set, item_icons, fonts)
        elif current_game_state == config.GAME_STATE_SELL: sell_button_rect, ui_exit_button_rect = ui_manager.draw_sell_ui(screen, screen_width, screen_height, player_money, locale_set, inventory, item_icons, fonts); clickable_ui_elements = []; sell_data = {'action': 'sell_item'}; clickable_ui_elements.append((sell_button_rect, sell_data)) if sell_button_rect else None


        # --- Bildschirm aktualisieren ---
        pygame.display.flip()

    # --- Fehlerbehandlung für die Hauptschleife ---
    except Exception as e_game_loop:
        logger.critical("Unerwarteter Fehler in der Haupt-Spielschleife:", exc_info=True)
        running = False # Beendet den Loop nach dem Fehler


# ========= SPIEL BEENDEN =========
logger.info("Spiel-Loop beendet.")

# Spielstand speichern
try:
    logger.info("Speichere Spielstand...")
    # Korrigierte Pfadkonstruktion: Nutze die relativen Pfade aus config.py direkt
    save_data_dir = os.path.join(project_root_dir_game, config.SAVE_DATA_DIR_NAME) # Pfad zum Save-Ordner
    player_pos_save_file = os.path.join(save_data_dir, config.PLAYER_POS_SAVE_FILENAME)
    placed_items_save_file = os.path.join(save_data_dir, config.PLACED_ITEMS_SAVE_FILENAME)
    # inventory.filepath wird beim Initialisieren gesetzt

    if inventory: inventory.save_inventory()
    if player: persistence.save_data({'x': player.rect.x, 'y': player.rect.y, 'money': player_money}, player_pos_save_file)
    if placed_items is not None: items.save_placed_items(placed_items, placed_items_save_file)

except Exception as e_final_save:
    logger.error("Fehler beim finalen Speichern des Spielstands.", exc_info=True)

# Pygame sauber beenden
if pygame.get_init():
    pygame.quit()
    logger.info("Pygame erfolgreich beendet.")

# Programm beenden
logger.info("Programm wird jetzt beendet.")
sys.exit()