# data/etc/setup.py
# Stand: 2025-04-15 (Neu erstellt für Refactoring)
# Formatiert für maximale Lesbarkeit

import pygame
import os
import sys
import logging
import locale
import time
import traceback

# Eigene Module importieren (ggf. anpassen)
try:
    from . import config
    from . import items
    from . import inventory as inventory_module # Umbenannt, um Kollision zu vermeiden
    from . import persistence
    from . import settings_utils
    from . import platform_utils
    from . import player as player_module
    from . import npc as npc_module
    from . import camera as camera_module
    # Dialog und Shop werden hier nicht direkt benötigt, aber game.py braucht sie
except ImportError:
    import config
    import items
    import inventory as inventory_module
    import persistence
    import settings_utils
    import platform_utils
    import player as player_module
    import npc as npc_module
    import camera as camera_module

# Logging für dieses Modul
logger = logging.getLogger(__name__)

# ========= HILFSFUNKTIONEN FÜR ASSET LOADING (aus game.py verschoben) =========
# Diese könnten auch in ein eigenes 'asset_loader.py' Modul

def load_image_asset(filename, image_folder, alpha=True, scale_to=None):
    """Lädt ein Bild aus dem IMAGE_FOLDER, konvertiert es und skaliert es optional."""
    if not filename:
        logger.warning("Leerer Dateiname in load_image_asset.")
        return None
    path = os.path.join(image_folder, filename)
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
                # Prüfen ob Bild gültige Dimensionen hat vor Skalierung
                if image.get_width() > 0 and image.get_height() > 0:
                     image = pygame.transform.smoothscale(image, scale_to_int)
                else:
                     logger.warning(f"Bild '{filename}' hat ungültige Dimensionen {image.get_size()} und kann nicht skaliert werden.")
            except ValueError as e: # Fehler tritt auf wenn eine Dimension 0 ist
                 logger.error(f"ValueError beim Skalieren von '{filename}' zu {scale_to_int} (Dimensionen: {image.get_size()}): {e}")
            except Exception as e:
                logger.error(f"Fehler Skalieren '{filename}' zu {scale_to_int}", exc_info=True)
    return image

def load_sound_asset(filename, sound_folder):
    """Lädt eine Sounddatei aus dem SOUND_FOLDER."""
    if not filename:
        logger.warning("Leerer Dateiname in load_sound_asset.")
        return None
    # Mixer muss initialisiert sein, bevor Sounds geladen werden!
    if not pygame.mixer.get_init():
         logger.error("Versuch, Sound zu laden, bevor pygame.mixer initialisiert wurde.")
         return None

    path = os.path.join(sound_folder, filename)
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


# ========= SETUP-HILFSFUNKTIONEN =========

def setup_locale():
    """Versucht, das deutsche Locale zu setzen."""
    locale_set = False
    try:
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
        locale_set = True
        logger.info("Locale 'de_DE.UTF-8' erfolgreich gesetzt.")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'German_Germany.1252') # Fallback Windows
            locale_set = True
            logger.info("Locale 'German_Germany.1252' erfolgreich gesetzt.")
        except locale.Error:
            logger.warning("Weder 'de_DE.UTF-8' noch 'German_Germany.1252' Locale verfügbar.")
    return locale_set

def setup_logging(log_dir, project_root_dir):
    """Konfiguriert das Logging (Konsole und Datei)."""
    log_level = logging.getLevelName(config.DEFAULT_LOG_LEVEL)
    logging.basicConfig(level=log_level, format=config.LOG_FORMAT, datefmt=config.DATE_FMT, force=True)
    logger.info(f"Logging Level gesetzt auf: {config.DEFAULT_LOG_LEVEL}")

    # File Logging hinzufügen
    try:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        # Verwende den Namen des Hauptskripts für die Logdatei, falls möglich
        main_script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0] if sys.argv else "game"
        log_filename = f"{main_script_name}_{timestamp}.log"
        log_file_path = os.path.join(log_dir, log_filename)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(log_level) # Gleiches Level wie Konsole oder spezifisch
        formatter = logging.Formatter(config.LOG_FORMAT, datefmt=config.DATE_FMT)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler) # Füge Handler zum Root-Logger hinzu
        logger.info(f"File logging initialisiert: {log_file_path}")
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des File Logging: {e}", exc_info=True)

def init_pygame():
    """Initialisiert Pygame und den Mixer."""
    try:
        pygame.init()
        logger.info("Pygame initialisiert.")
        try:
            pygame.mixer.init()
            logger.info("Pygame Mixer initialisiert.")
        except pygame.error as e_mixer:
            logger.error(f"Pygame Mixer Initialisierung fehlgeschlagen: {e_mixer}", exc_info=True)
            # Weitermachen ohne Sound? Oder hier abbrechen? Aktuell: weitermachen.
    except Exception as e_pygame:
         logger.critical(f"Kritischer Fehler bei pygame.init(): {e_pygame}", exc_info=True)
         raise RuntimeError("Pygame konnte nicht initialisiert werden.") from e_pygame

def create_screen():
    """Erstellt den Pygame-Bildschirm."""
    screen_width, screen_height = 800, 600 # Fallback
    screen = None
    try:
        info = pygame.display.Info()
        screen_width, screen_height = info.current_w, info.current_h
        logger.info(f"Bildschirmgröße erkannt: {screen_width}x{screen_height}")
        # SCALED erlaubt internes Rendering in logischer Größe, RESIZABLE ist gut für Desktop
        # FULLSCREEN für echtes Vollbild (kann auf manchen Systemen Probleme machen)
        # flags = pygame.SCALED | pygame.RESIZABLE | pygame.FULLSCREEN
        flags = pygame.SCALED | pygame.RESIZABLE # Sicherere Variante
        screen = pygame.display.set_mode((screen_width, screen_height), flags)
    except Exception as e_fs:
        logger.warning(f"Vollbild/Resizable-Initialisierung fehlgeschlagen ({e_fs}). Nutze Fallback 800x600.", exc_info=False)
        screen_width, screen_height = 800, 600
        try:
            # Fallback ohne FULLSCREEN
            flags = pygame.SCALED | pygame.RESIZABLE
            screen = pygame.display.set_mode((screen_width, screen_height), flags)
        except Exception as e_fallback:
            logger.critical("Fallback-Bildschirm konnte nicht erstellt werden!", exc_info=True)
            raise RuntimeError("Bildschirm konnte nicht initialisiert werden.") from e_fallback

    if screen is None: # Zusätzliche Sicherheitsprüfung
        logger.critical("Bildschirm konnte nicht initialisiert werden (screen is None).")
        raise RuntimeError("Bildschirm ist None nach Initialisierungsversuchen.")

    pygame.display.set_caption("Drug Dealer Game Refactored") # Titel setzen
    logger.info(f"Screen erstellt ({screen_width}x{screen_height}).")
    return screen, screen_width, screen_height

def load_fonts(screen_height):
    """Lädt und skaliert die Schriften."""
    fonts = {}
    try:
        # Skalierung basierend auf Referenzhöhe und Bildschirmhöhe
        scale_factor = screen_height / config.FONT_SIZE_REF_H
        ui_fs = max(12, int(config.BASE_UI_FONT_SIZE * scale_factor))
        btn_fs = max(10, int(config.BASE_BUTTON_FONT_SIZE * scale_factor))
        inv_fs = max(8, int(config.BASE_INV_QTY_FONT_SIZE * scale_factor))
        dlg_fs = max(14, int(config.BASE_DIALOG_FONT_SIZE * scale_factor))
        shp_fs = max(10, int(config.BASE_SHOP_FONT_SIZE * scale_factor))

        # Verwende Pygame's Standard-Font (None) oder spezifiziere eine .ttf Datei
        fonts['ui'] = pygame.font.Font(None, ui_fs)
        fonts['button'] = pygame.font.Font(None, btn_fs)
        fonts['inventory'] = pygame.font.Font(None, inv_fs)
        fonts['dialog'] = pygame.font.Font(None, dlg_fs)
        fonts['shop'] = pygame.font.Font(None, shp_fs)

        logger.info(f"Fonts erstellt (Größen: UI={ui_fs}, Btn={btn_fs}, Inv={inv_fs}, Dlg={dlg_fs}, Shop={shp_fs}).")
        return fonts
    except Exception as e:
        logger.error(f"Fehler beim Laden der Fonts: {e}", exc_info=True)
        # Das Spiel kann ohne Fonts nicht sinnvoll laufen
        raise RuntimeError("Fonts konnten nicht geladen werden.") from e

def calculate_ui_layout(screen_width, screen_height):
    """Berechnet Layout-Informationen wie Button-Position und Inventar-Position."""
    layout = {}

    # Android Button Position/Größe
    btn_def_w = int(screen_width * config.BUTTON_DEFAULT_WIDTH_PERCENT)
    btn_def_h = int(screen_height * config.BUTTON_DEFAULT_HEIGHT_PERCENT)
    # Die tatsächliche Größe hängt vom geladenen Bild ab, dies ist nur Fallback/Basis
    layout['button_base_size'] = (btn_def_w, btn_def_h)
    layout['button_rect'] = pygame.Rect(config.BUTTON_X, 0, btn_def_w, btn_def_h) # Y wird später gesetzt

    # Inventar Position (Zentriert)
    inv_display_width = inventory_module.get_inventory_display_width()
    inv_bottom_clearance = inventory_module.get_required_bottom_padding()
    layout['inv_pos_x'] = (screen_width - inv_display_width) // 2
    layout['inv_pos_y'] = screen_height - inv_bottom_clearance
    layout['inv_pos'] = (layout['inv_pos_x'], layout['inv_pos_y'])

    logger.info(f"Inventar Position berechnet: X={layout['inv_pos_x']}, Y={layout['inv_pos_y']}")
    logger.debug(f"Basis Button Rect berechnet: {layout['button_rect']}")

    return layout

def load_main_assets(image_folder, sound_folder, screen_width, screen_height, current_settings):
    """Lädt die Haupt-Assets wie Hintergrund, Button-Bild, Sounds und Item-Assets."""
    assets = {}
    logger.info("Lade Haupt-Assets...")

    # Lade Item-Assets (Icons, platzierte Bilder)
    # Muss hier geschehen, da item_icons für andere Assets (Shop) benötigt wird
    try:
         # Definiere eine Wrapper-Funktion für load_image_asset, die image_folder übergibt
         def image_loader(filename, alpha=True, scale_to=None):
             return load_image_asset(filename, image_folder, alpha, scale_to)

         assets['item_icons'], assets['placed_item_images'], assets['fallback_placed_image'] = items.load_item_assets(
            image_folder, items.PLACED_ITEM_SIZE, inventory_module.get_scaled_icon_size(), image_loader
         )
         # Füge hier ggf. noch die Logik hinzu, um spezifische Icons (Grips, PackedWeed) zu laden,
         # falls sie nicht von load_item_assets abgedeckt werden und die Dateien existieren.
         # Beispiel (aus game.py):
         if items.ITEM_GRIPS not in assets['item_icons']:
             grips_icon = image_loader(config.GRIPS_ICON_FILENAME, alpha=True, scale_to=inventory_module.get_scaled_icon_size())
             if grips_icon: assets['item_icons'][items.ITEM_GRIPS] = grips_icon
             else: logger.warning(f"Icon für '{items.ITEM_GRIPS}' konnte nicht geladen werden.")
         if items.ITEM_VERPACKTES_WEED not in assets['item_icons']:
             packed_icon = image_loader(config.PACKED_WEED_ICON_FILENAME, alpha=True, scale_to=inventory_module.get_scaled_icon_size())
             if packed_icon: assets['item_icons'][items.ITEM_VERPACKTES_WEED] = packed_icon
             else: logger.warning(f"Icon für '{items.ITEM_VERPACKTES_WEED}' konnte nicht geladen werden.")

    except Exception as e:
        logger.error(f"Fehler beim Laden der Item-Assets: {e}", exc_info=True)
        raise RuntimeError("Item-Assets konnten nicht geladen werden.") from e


    # Hintergrundbild
    bg_image = load_image_asset(config.BACKGROUND_FILENAME, image_folder, alpha=False)
    if bg_image:
        try:
             # Skalieren, falls nötig (wenn nicht SCALED Flag verwendet wird oder zur Sicherheit)
            if bg_image.get_size() != (screen_width, screen_height):
                 bg_image = pygame.transform.smoothscale(bg_image, (screen_width, screen_height))
                 logger.info("Hintergrundbild skaliert.")
            assets['background'] = bg_image
        except Exception as e_scale_bg:
             logger.error(f"Fehler beim Skalieren des Hintergrundbildes: {e_scale_bg}")
             assets['background'] = None # Fallback auf Farbe
    else:
        assets['background'] = None

    # Android Button Bild
    assets['button_image'] = load_image_asset(config.BUTTON_FILENAME, image_folder, alpha=True)
    # Hinweis: Geld-Icon wird in Inventory.__init__ geladen

    # Sounds laden
    sfx_vol = current_settings.get('sfx_volume', 0.5)
    master_vol = current_settings.get('master_volume', 1.0)
    final_sfx_vol = sfx_vol * master_vol

    assets['sounds'] = {}
    no_res_sound = load_sound_asset(config.NO_RESOURCE_SOUND_FILENAME, sound_folder)
    if no_res_sound:
        try:
            no_res_sound.set_volume(final_sfx_vol * 0.7) # Etwas leiser?
            assets['sounds']['error'] = no_res_sound
            assets['sounds']['no_resource'] = no_res_sound # Alias
        except Exception as e:
             logger.error(f"Fehler beim Setzen der Lautstärke für '{config.NO_RESOURCE_SOUND_FILENAME}': {e}")
    else:
        logger.warning(f"Sound '{config.NO_RESOURCE_SOUND_FILENAME}' nicht geladen.")

    # Hier weitere Sounds laden...
    # sell_success_sound = load_sound_asset("sell.wav", sound_folder)
    # if sell_success_sound:
    #      sell_success_sound.set_volume(final_sfx_vol)
    #      assets['sounds']['sell_success'] = sell_success_sound

    logger.info(f"Haupt-Assets geladen. {len(assets.get('item_icons', {}))} Icons geladen.")
    return assets

def create_player(player_pos_save_file, world_width, world_height):
    """Lädt Spielerdaten oder erstellt einen neuen Spieler."""
    player_start_x = world_width // 2
    player_start_y = world_height // 2
    player_radius = config.TILE_SIZE // 3 # Beispielradius
    spawn_x, spawn_y = player_start_x, player_start_y
    player_money = 0.0 # Standard-Geld

    loaded_player_data = persistence.load_data(player_pos_save_file)
    if isinstance(loaded_player_data, dict):
        try:
            spawn_x = int(loaded_player_data.get('x', spawn_x))
            spawn_y = int(loaded_player_data.get('y', spawn_y))
            player_money = float(loaded_player_data.get('money', player_money))
            logger.info("Spielerdaten (Position & Geld) erfolgreich geladen.")
        except (ValueError, TypeError) as e:
            logger.warning(f"Ungültige Spielerdaten geladen ({e}). Nutze Standardwerte.", exc_info=False)
            spawn_x, spawn_y = player_start_x, player_start_y
            player_money = 0.0
    else:
        logger.info("Keine Speicherdatei für Spielerdaten gefunden. Nutze Standardwerte.")

    try:
        player = player_module.Player(spawn_x, spawn_y, player_radius, config.RED)
        logger.info(f"Spieler erstellt bei ({spawn_x},{spawn_y}), Geld: {player_money:.2f}")
        return player, player_money
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Player-Objekts: {e}", exc_info=True)
        raise RuntimeError("Spieler konnte nicht erstellt werden.") from e


def create_camera(world_width, world_height, screen_width, screen_height, player):
    """Erstellt die Kamera und positioniert sie initial."""
    try:
        camera = camera_module.Camera(world_width, world_height, screen_width, screen_height)
        # Kamera initial auf Spieler zentrieren
        cam_x = max(0, min(player.rect.centerx - screen_width // 2, world_width - screen_width))
        cam_y = max(0, min(player.rect.centery - screen_height // 2, world_height - screen_height))
        camera.camera_rect.topleft = (cam_x, cam_y)
        logger.info("Kamera initialisiert.")
        return camera
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Camera-Objekts: {e}", exc_info=True)
        raise RuntimeError("Kamera konnte nicht erstellt werden.") from e


def create_inventory(inventory_save_file, image_folder):
    """Erstellt das Inventar und fügt ggf. Startitems hinzu."""
    try:
        # Definiere eine Wrapper-Funktion für load_image_asset, die image_folder übergibt
        # Wird benötigt, damit Inventory das Geld-Icon laden kann
        def image_loader(filename, alpha=True, scale_to=None):
            return load_image_asset(filename, image_folder, alpha, scale_to)

        inventory = inventory_module.Inventory(
            filepath=inventory_save_file,
            image_folder=image_folder,
            image_loader_func=image_loader
        )
        logger.info("Inventar erstellt/geladen.")

        # Start-Items hinzufügen, falls nicht vorhanden (nur beim ersten Start relevant)
        # Verwende Konstanten aus items.py
        if not inventory.has_item(items.ITEM_BLUMENTOPF): inventory.add_item(items.ITEM_BLUMENTOPF, 3)
        if not inventory.has_item(items.ITEM_SACK_ERDE): inventory.add_item(items.ITEM_SACK_ERDE, 5)
        if not inventory.has_item(items.ITEM_WEED_SEEDS): inventory.add_item(items.ITEM_WEED_SEEDS, 10)
        if not inventory.has_item(items.ITEM_VERPACKSTATION): inventory.add_item(items.ITEM_VERPACKSTATION, 1)
        if not inventory.has_item(items.ITEM_GRIPS): inventory.add_item(items.ITEM_GRIPS, 20) # Start-Grips

        return inventory
    except Exception as e:
         logger.error(f"Fehler beim Erstellen des Inventory-Objekts: {e}", exc_info=True)
         raise RuntimeError("Inventar konnte nicht erstellt werden.") from e

def load_world_objects(placed_items_save_file, assets, player_spawn_x, player_spawn_y, world_width, world_height):
    """Lädt platzierte Items und erstellt NPCs."""
    all_sprites = pygame.sprite.Group()
    npcs = pygame.sprite.Group()
    placed_items_group = pygame.sprite.Group()

    # Platzierte Items laden (nutzt Funktion aus items.py)
    try:
        loaded_item_objects = items.load_placed_items(
            placed_items_save_file,
            assets.get('placed_item_images', {}),
            assets.get('fallback_placed_image')
        )
        for item_obj in loaded_item_objects:
             placed_items_group.add(item_obj)
             all_sprites.add(item_obj) # Auch zur Hauptgruppe hinzufügen
    except Exception as e:
         logger.error(f"Fehler beim Laden platzierter Items durch items.load_placed_items: {e}", exc_info=True)
         # Weitermachen ohne geladene Items? Oder abbrechen? Aktuell: weitermachen.

    # NPCs erstellen
    try:
        npc_radius = config.TILE_SIZE // 3
        # Beispiel-NPCs (Positionen anpassen!)
        npc_g = npc_module.NPC(world_width - config.TILE_SIZE * 10, config.TILE_SIZE * 15, npc_radius, config.GREY, "generic", "generic_hallo")

        # Händler in der Nähe des Spieler-Spawns
        merchant_x = max(npc_radius, min(player_spawn_x + config.TILE_SIZE * 5, world_width - npc_radius))
        merchant_y = max(npc_radius, min(player_spawn_y + config.TILE_SIZE * 3, world_height - npc_radius))
        npc_m = npc_module.NPC(merchant_x, merchant_y, npc_radius, config.BLUE, "merchant", "händler_start")

        # Kunde etwas neben dem Händler
        client_x = max(npc_radius, min(merchant_x + 200, world_width - npc_radius))
        client_y = merchant_y # Gleiche Höhe wie Händler
        npc_client = npc_module.NPC(client_x, client_y, npc_radius, config.DARK_GREEN, "client", "client_start")

        npcs.add(npc_g, npc_m, npc_client)
        all_sprites.add(npcs) # Füge die NPC-Gruppe zur Haupt-Gruppe hinzu
        logger.info(f"NPCs erstellt. Gesamt Sprites in all_sprites: {len(all_sprites)}")
    except Exception as e:
         logger.error(f"Fehler beim Erstellen der NPCs: {e}", exc_info=True)
         # Weitermachen ohne NPCs?

    return all_sprites, placed_items_group, npcs

# ========= HAUPT-INITIALISIERUNGSFUNKTION =========

def initialize_game(project_root_dir):
    """
    Führt alle Schritte zur Initialisierung des Spiels aus.

    Args:
        project_root_dir (str): Der absolute Pfad zum Projekt-Stammverzeichnis.

    Returns:
        dict: Ein Dictionary mit allen initialisierten Spielobjekten und Zuständen,
              oder None bei einem kritischen Fehler.
    """
    game_state = {}
    try:
        # 1. Pfade konstruieren
        image_folder = os.path.join(project_root_dir, config.IMAGE_DIR_NAME)
        sound_folder = os.path.join(project_root_dir, config.SOUND_DIR_NAME)
        log_dir = os.path.join(project_root_dir, config.LOG_DIR_NAME)
        save_data_dir = os.path.join(project_root_dir, config.SAVE_DATA_DIR_NAME)
        settings_dir = os.path.join(project_root_dir, config.SETTINGS_DIR_NAME)
        settings_file = os.path.join(settings_dir, config.SETTINGS_FILENAME)
        inventory_save_file = os.path.join(save_data_dir, config.INVENTORY_SAVE_FILENAME)
        player_pos_save_file = os.path.join(save_data_dir, config.PLAYER_POS_SAVE_FILENAME)
        placed_items_save_file = os.path.join(save_data_dir, config.PLACED_ITEMS_SAVE_FILENAME)

        # 2. Logging & Locale Setup
        setup_logging(log_dir, project_root_dir) # Muss früh sein
        game_state['locale_set'] = setup_locale()

        logger.info("Starte Spielinitialisierung...")
        logger.debug(f"Project Root: {project_root_dir}")
        logger.debug(f"Image Folder: {image_folder}")
        logger.debug(f"Sound Folder: {sound_folder}")
        logger.debug(f"Save Folder: {save_data_dir}")

        # 3. Einstellungen laden
        try:
             game_state['settings'] = settings_utils.load_settings(settings_file)
             logger.info(f"Einstellungen geladen: {game_state['settings']}")
        except Exception as e_cfg:
            logger.exception("FEHLER beim Laden der Einstellungen:")
            game_state['settings'] = {'music_volume': 0.5, 'sfx_volume': 0.5, 'master_volume': 1.0} # Fallback
            logger.warning(f"Nutze Fallback-Einstellungen: {game_state['settings']}")

        # 4. Pygame initialisieren
        init_pygame()
        game_state['clock'] = pygame.time.Clock()

        # 5. Bildschirm erstellen
        screen, screen_w, screen_h = create_screen()
        game_state['screen'] = screen
        game_state['screen_width'] = screen_w
        game_state['screen_height'] = screen_h

        # Weltgröße definieren (Beispiel)
        world_width = screen_w * 3
        world_height = screen_h * 2
        game_state['world_width'] = world_width
        game_state['world_height'] = world_height
        logger.info(f"Weltgröße: {world_width}x{world_height}")

        # 6. Fonts laden
        game_state['fonts'] = load_fonts(screen_h)

        # 7. UI Layout berechnen
        # Muss nach Screen-Erstellung und Font-Laden erfolgen (falls Font-Größen benötigt)
        # und nach Inventory-Modul-Import
        game_state['layout'] = calculate_ui_layout(screen_w, screen_h)

        # 8. Haupt-Assets laden (Hintergrund, Sounds, Item-Assets etc.)
        game_state['assets'] = load_main_assets(
            image_folder, sound_folder, screen_w, screen_h, game_state['settings']
        )

        # 9. Spieler erstellen/laden
        player, player_money = create_player(player_pos_save_file, world_width, world_height)
        game_state['player'] = player
        game_state['player_money'] = player_money

        # 10. Kamera erstellen
        game_state['camera'] = create_camera(world_width, world_height, screen_w, screen_h, player)

        # 11. Inventar erstellen
        game_state['inventory'] = create_inventory(inventory_save_file, image_folder)

        # 12. Weltobjekte laden/erstellen (NPCs, platzierte Items)
        all_sprites, placed_items, npcs = load_world_objects(
             placed_items_save_file,
             game_state['assets'],
             player.rect.centerx, # Startposition für NPC-Platzierung
             player.rect.centery,
             world_width,
             world_height
        )
        game_state['all_sprites'] = all_sprites
        game_state['placed_items'] = placed_items
        game_state['npcs'] = npcs

        # Füge Spieler zur all_sprites Gruppe hinzu (falls nicht schon in load_world_objects)
        if player not in all_sprites:
             all_sprites.add(player)

        # 13. Finale UI-Anpassungen (z.B. Button-Position basierend auf geladenem Bild)
        layout_info = game_state['layout']
        button_image = game_state['assets'].get('button_image')
        if platform_utils.IS_ANDROID and button_image:
            btn_w_actual, btn_h_actual = button_image.get_size()
        else:
            btn_w_actual, btn_h_actual = layout_info['button_base_size']

        # Y-Position des Buttons über dem Inventar
        button_y = layout_info['inv_pos_y'] - btn_h_actual - config.BUTTON_PADDING
        # Aktualisiere Button Rect im Layout Dictionary
        layout_info['button_rect'].size = (btn_w_actual, btn_h_actual)
        layout_info['button_rect'].topleft = (config.BUTTON_X, button_y)
        logger.debug(f"Finale Button Rect Position angepasst: {layout_info['button_rect']}")

        # 14. Android Immersive Mode
        if platform_utils.IS_ANDROID:
            platform_utils.set_android_immersive_mode()
            logger.info("Android Immersive Mode aktiviert.")

        logger.info("Spielinitialisierung erfolgreich abgeschlossen.")
        return game_state

    except Exception as e:
        logger.critical("Kritischer Fehler während der Spielinitialisierung:", exc_info=True)
        # Versuche Pygame zu beenden, falls es schon lief
        if pygame.get_init():
            pygame.quit()
        return None # Signalisiert Fehler an Hauptskript