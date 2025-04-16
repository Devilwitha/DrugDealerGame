# -*- coding: utf-8 -*-
# map_editor_gui.py (Version 10 - Robusterer Palette Check + erneute Font-Korrektur)
# (Identisch zu V10 aus vorheriger Antwort)
import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog, simpledialog
import json
import traceback
import math

# --- Pygame GUI Import ---
import pygame_gui

# --- Konstanten und Konfiguration ---
TILE_WIDTH = 32; TILE_HEIGHT = 32
DEFAULT_SOURCE_TILE_W = 32; DEFAULT_SOURCE_TILE_H = 32
DEFAULT_MAP_WIDTH_TILES = 25; DEFAULT_MAP_HEIGHT_TILES = 20
PALETTE_WIDTH_TILES = 6; TOOLBAR_HEIGHT = 60
MAP_WIDTH_TILES = DEFAULT_MAP_WIDTH_TILES; MAP_HEIGHT_TILES = DEFAULT_MAP_HEIGHT_TILES
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200); RED = (255, 0, 0); BLUE = (0, 0, 255)
GREEN = (0, 255, 0); TRANSPARENT_RED = (255, 0, 0, 128)
FPS = 60

# --- Globale Variablen ---
screen = None; background_surface = None; clock = None; ui_manager = None
loaded_tilesets = []; all_tile_images_flat = []; all_tile_mapping = []
map_tileset_indices = []; map_tile_indices = []; map_collision_data = []
current_tileset_index = -1; current_tile_index_in_tileset = -1; current_flat_palette_index = -1
is_mouse_down_left = False; is_mouse_down_right = False; last_painted_tile_coords = None
edit_mode = 'tile'
toolbar_panel = None; mode_button = None; palette_container = None
palette_scrollbar = None; palette_scroll_offset_y = 0
palette_data_needs_rebuild = True # Flag für Daten-Update
resize_map_window = None

# Platzhalter für Layout-Rechtecke
MAP_AREA_WIDTH = 10; MAP_AREA_HEIGHT = 10; SCREEN_WIDTH = 100; SCREEN_HEIGHT = 100
MAP_AREA_RECT = pygame.Rect(0, 0, 10, 10); PALETTE_AREA_RECT = pygame.Rect(0, 0, 10, 10)
PALETTE_AREA_WIDTH = PALETTE_WIDTH_TILES * TILE_WIDTH

# --- Hilfsfunktionen ---

def update_layout_dimensions():
    """Berechnet Screen-Grösse und Layout-Rechtecke neu."""
    # (Unverändert zu V10)
    global SCREEN_WIDTH, SCREEN_HEIGHT, MAP_AREA_WIDTH, MAP_AREA_HEIGHT
    global MAP_AREA_RECT, PALETTE_AREA_RECT
    MAP_AREA_WIDTH = MAP_WIDTH_TILES * TILE_WIDTH
    MAP_AREA_HEIGHT = MAP_HEIGHT_TILES * TILE_HEIGHT
    SCREEN_WIDTH = MAP_AREA_WIDTH + PALETTE_AREA_WIDTH
    SCREEN_HEIGHT = TOOLBAR_HEIGHT + MAP_AREA_HEIGHT
    MAP_AREA_RECT = pygame.Rect(0, TOOLBAR_HEIGHT, MAP_AREA_WIDTH, MAP_AREA_HEIGHT)
    PALETTE_AREA_RECT = pygame.Rect(MAP_AREA_WIDTH, TOOLBAR_HEIGHT, PALETTE_AREA_WIDTH, MAP_AREA_HEIGHT)

def initialize_map_data(width=DEFAULT_MAP_WIDTH_TILES, height=DEFAULT_MAP_HEIGHT_TILES):
    """Initialisiert Map-Daten, aktualisiert globale Grössen und Layout."""
    # (Unverändert zu V10)
    global map_tileset_indices, map_tile_indices, map_collision_data
    global MAP_WIDTH_TILES, MAP_HEIGHT_TILES
    MAP_WIDTH_TILES = max(1, width); MAP_HEIGHT_TILES = max(1, height)
    map_tileset_indices = [[-1 for _ in range(MAP_WIDTH_TILES)] for _ in range(MAP_HEIGHT_TILES)]
    map_tile_indices = [[-1 for _ in range(MAP_WIDTH_TILES)] for _ in range(MAP_HEIGHT_TILES)]
    map_collision_data = [[False for _ in range(MAP_WIDTH_TILES)] for _ in range(MAP_HEIGHT_TILES)]
    update_layout_dimensions()
    print(f"Map Daten initialisiert ({MAP_WIDTH_TILES}x{MAP_HEIGHT_TILES} Tiles)")

def resize_map_data(new_width, new_height):
    """Passt die Grösse der Map-Daten an, behält alte Inhalte bei."""
    # (Unverändert zu V10)
    global map_tileset_indices, map_tile_indices, map_collision_data
    global MAP_WIDTH_TILES, MAP_HEIGHT_TILES
    new_width = max(1, new_width); new_height = max(1, new_height)
    new_tsi = [[-1 for _ in range(new_width)] for _ in range(new_height)]
    new_ti = [[-1 for _ in range(new_width)] for _ in range(new_height)]
    new_coll = [[False for _ in range(new_width)] for _ in range(new_height)]
    max_row = min(MAP_HEIGHT_TILES, new_height); max_col = min(MAP_WIDTH_TILES, new_width)
    for r in range(max_row):
        for c in range(max_col):
            new_tsi[r][c] = map_tileset_indices[r][c]
            new_ti[r][c] = map_tile_indices[r][c]
            new_coll[r][c] = map_collision_data[r][c]
    map_tileset_indices = new_tsi; map_tile_indices = new_ti; map_collision_data = new_coll
    MAP_WIDTH_TILES = new_width; MAP_HEIGHT_TILES = new_height
    update_layout_dimensions()
    print(f"Map-Daten auf {new_width}x{new_height} angepasst.")

def load_tileset_images(filepath, source_tile_width, source_tile_height, target_tile_width, target_tile_height):
    """Lädt Tileset, extrahiert mit Source-Grösse, skaliert auf Target-Grösse."""
    # (Unverändert zu V10)
    if not os.path.exists(filepath): print(f"Fehler: Tileset nicht gefunden: {filepath}"); return None, 0, 0
    print(f"Lade '{os.path.basename(filepath)}': Quelle {source_tile_width}x{source_tile_height}, Ziel {target_tile_width}x{target_tile_height}")
    try: tileset_image = pygame.image.load(filepath)
    except pygame.error as e: print(f"Fehler Bildladen '{filepath}': {e}"); return None, 0, 0
    img_w, img_h = tileset_image.get_size(); tile_images = []; any_scaled = False
    if source_tile_width <= 0 or source_tile_height <= 0: print(f"Fehler: Ungültige Quellgrösse ({source_tile_width}x{source_tile_height})"); return None, 0, 0
    cols = img_w // source_tile_width; rows = img_h // source_tile_height
    if img_w % source_tile_width != 0 or img_h % source_tile_height != 0: print(f"Warnung: Bild ({img_w}x{img_h}) nicht durch Quelle ({source_tile_width}x{source_tile_height}) teilbar.")
    for row in range(rows):
        for col in range(cols):
            tile_rect = pygame.Rect(col*source_tile_width, row*source_tile_height, source_tile_width, source_tile_height)
            try:
                tile_surface = tileset_image.subsurface(tile_rect); scaled_tile = tile_surface
                if source_tile_width != target_tile_width or source_tile_height != target_tile_height:
                    any_scaled = True
                    try: scaled_tile = pygame.transform.smoothscale(tile_surface, (target_tile_width, target_tile_height))
                    except ValueError: print(f"Warnung: smoothscale fehlgeschlagen ({row},{col}). Scale."); scaled_tile = pygame.transform.scale(tile_surface, (target_tile_width, target_tile_height))
                try: tile_images.append(scaled_tile.convert_alpha())
                except pygame.error: tile_images.append(scaled_tile.convert())
            except ValueError as e: print(f"Fehler Subsurface ({row},{col}): {e}"); continue
    if any_scaled: print(f"Hinweis: Tiles aus '{os.path.basename(filepath)}' wurden skaliert.")
    print(f"{len(tile_images)} Tiles aus '{os.path.basename(filepath)}' verarbeitet."); return tile_images, len(tile_images), cols

def rebuild_palette_data():
    """Erstellt flache Liste aller Tiles und Mapping. Setzt Daten-Update Flag."""
    # (Unverändert zu V10)
    global all_tile_images_flat, all_tile_mapping, palette_data_needs_rebuild
    all_tile_images_flat = []; all_tile_mapping = []
    for ts_idx, tileset in enumerate(loaded_tilesets):
        if isinstance(tileset.get('images'), list):
            for tile_idx, img in enumerate(tileset['images']):
                all_tile_images_flat.append(img); all_tile_mapping.append((ts_idx, tile_idx))
        else: print(f"Warnung: Fehlende 'images' für Tileset Index {ts_idx}")
    print(f"Palette Daten neu aufgebaut ({len(all_tile_images_flat)} Tiles)."); palette_data_needs_rebuild = True

def ask_source_tile_size(parent_tk_window, filepath):
    """Fragt Benutzer nach originaler Tile-Grösse."""
    # (Unverändert zu V10)
    title = f"Original Tile-Grösse für: {os.path.basename(filepath)}"
    w = simpledialog.askinteger("Original Breite", f"Breite in '{os.path.basename(filepath)}'?", parent=parent_tk_window, initialvalue=DEFAULT_SOURCE_TILE_W, minvalue=1)
    if w is None: return None, None
    h = simpledialog.askinteger("Original Höhe", f"Höhe in '{os.path.basename(filepath)}'?", parent=parent_tk_window, initialvalue=DEFAULT_SOURCE_TILE_H, minvalue=1)
    if h is None: return None, None
    return w, h

def select_tilesets_and_load():
    """Öffnet Dialog, fragt ggf. nach Tile-Grössen und lädt Tilesets."""
    # (Unverändert zu V10)
    global loaded_tilesets, palette_data_needs_rebuild
    root = tk.Tk(); root.withdraw()
    print("Öffne Dialog zur Auswahl von Tileset-Dateien...");
    filepaths = filedialog.askopenfilenames(title="Wähle ein oder mehrere Tilesets", initialdir=os.path.dirname(__file__) if "__file__" in locals() else ".", filetypes=[("Bilddateien", "*.png *.jpg *.jpeg"), ("Alle Dateien", "*.*")])
    if not filepaths: print("Keine Dateien ausgewählt."); root.destroy(); return False
    new_tilesets_to_add = []
    for fp in filepaths:
        print(f"Verarbeite: {fp}"); source_w, source_h = DEFAULT_SOURCE_TILE_W, DEFAULT_SOURCE_TILE_H
        try:
            img = pygame.image.load(fp); img_w, img_h = img.get_size(); del img
            if img_w % TILE_WIDTH != 0 or img_h % TILE_HEIGHT != 0:
                 print(f"Dimensionen ({img_w}x{img_h}) nicht durch Editor-Ziel ({TILE_WIDTH}x{TILE_HEIGHT}) teilbar.")
                 source_w, source_h = ask_source_tile_size(root, fp)
                 if source_w is None or source_h is None: print(f"Grössenauswahl abgebrochen."); continue
            else: source_w, source_h = TILE_WIDTH, TILE_HEIGHT; print(f"Dimensionen passen, nehme {source_w}x{source_h} an.")
            images, count, cols = load_tileset_images(fp, source_w, source_h, TILE_WIDTH, TILE_HEIGHT)
            if images: new_tilesets_to_add.append({'path': fp, 'images': images, 'tile_count': count, 'cols': cols, 'source_w': source_w, 'source_h': source_h})
            else: print(f"Konnte Tileset '{fp}' nicht verarbeiten.")
        except pygame.error as e: print(f"Pygame Fehler bei '{fp}': {e}")
        except Exception as e: print(f"Allg. Fehler bei '{fp}': {e}"); traceback.print_exc()
    root.destroy()
    if not new_tilesets_to_add: print("Keine neuen Tilesets hinzugefügt."); return False
    loaded_tilesets.extend(new_tilesets); rebuild_palette_data(); return True

def clear_all_tilesets():
     """Entfernt alle geladenen Tilesets und leert die Map."""
     # (Unverändert zu V10)
     global loaded_tilesets, all_tile_images_flat, all_tile_mapping, current_flat_palette_index, current_tileset_index, current_tile_index_in_tileset, palette_data_needs_rebuild
     if not loaded_tilesets: print("Keine Tilesets zum Löschen vorhanden."); return
     print(f"Lösche {len(loaded_tilesets)} Tileset(s)...")
     loaded_tilesets = []; all_tile_images_flat = []; all_tile_mapping = []
     current_flat_palette_index = -1; current_tileset_index = -1; current_tile_index_in_tileset = -1
     for r in range(MAP_HEIGHT_TILES):
          for c in range(MAP_WIDTH_TILES):
               map_tileset_indices[r][c] = -1; map_tile_indices[r][c] = -1
     print("Map-Referenzen auf Tilesets gelöscht."); palette_data_needs_rebuild = True

def save_map():
    """Speichert die aktuelle Karte inkl. Original-Tilegrössen."""
    # (Unverändert zu V10)
    root = tk.Tk(); root.withdraw()
    filepath = filedialog.asksaveasfilename(title="Karte speichern unter...", initialdir=os.path.dirname(__file__) if "__file__" in locals() else ".", defaultextension=".json", filetypes=[("Karten-Dateien", "*.json"), ("Alle Dateien", "*.*")])
    root.destroy();
    if not filepath: print("Speichern abgebrochen."); return
    script_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
    relative_tileset_paths = []; source_tileset_sizes = []
    for ts in loaded_tilesets:
        try: rel_path = os.path.relpath(ts['path'], script_dir); relative_tileset_paths.append(rel_path.replace("\\", "/"))
        except ValueError: print(f"Warnung: Pfad {ts['path']} nicht relativ."); relative_tileset_paths.append(ts['path'].replace("\\", "/"))
        source_tileset_sizes.append([ts.get('source_w', TILE_WIDTH), ts.get('source_h', TILE_HEIGHT)])
    map_save_data = { "tile_width": TILE_WIDTH, "tile_height": TILE_HEIGHT, "map_width_tiles": MAP_WIDTH_TILES, "map_height_tiles": MAP_HEIGHT_TILES, "tileset_paths": relative_tileset_paths, "source_tileset_sizes": source_tileset_sizes, "map_tileset_indices": map_tileset_indices, "map_tile_indices": map_tile_indices, "map_collision_data": map_collision_data, }
    try:
        with open(filepath, 'w') as f: json.dump(map_save_data, f, indent=4)
        print(f"Karte gespeichert: {filepath}")
    except Exception as e: print(f"Fehler beim Speichern: {e}"); traceback.print_exc()

def load_map():
    """Lädt eine Karte und passt Editor an."""
    # (Unverändert zu V10)
    global map_tileset_indices, map_tile_indices, map_collision_data, loaded_tilesets, MAP_WIDTH_TILES, MAP_HEIGHT_TILES, screen, ui_manager, palette_data_needs_rebuild, background_surface
    root = tk.Tk(); root.withdraw()
    filepath = filedialog.askopenfilename(title="Karte laden", initialdir=os.path.dirname(__file__) if "__file__" in locals() else ".", filetypes=[("Karten-Dateien", "*.json"), ("Alle Dateien", "*.*")])
    root.destroy();
    if not filepath: print("Laden abgebrochen."); return
    try:
        with open(filepath, 'r') as f: map_load_data = json.load(f)
    except Exception as e: print(f"Fehler Lesen: '{filepath}': {e}"); traceback.print_exc(); return
    try:
        loaded_tw = map_load_data.get('tile_width', TILE_WIDTH); loaded_th = map_load_data.get('tile_height', TILE_HEIGHT)
        if loaded_tw != TILE_WIDTH or loaded_th != TILE_HEIGHT: print(f"Info: Karte Ziel-Grösse {loaded_tw}x{loaded_th}. Editor nutzt {TILE_WIDTH}x{TILE_HEIGHT}.")
        new_map_w = map_load_data['map_width_tiles']; new_map_h = map_load_data['map_height_tiles']
        required_paths = map_load_data['tileset_paths']; source_tileset_sizes = map_load_data.get('source_tileset_sizes', [])
        temp_loaded_tilesets = []
        script_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
        print("Lade Tilesets für Karte...");
        for i, rel_path in enumerate(required_paths):
            abs_path = os.path.normpath(os.path.join(script_dir, rel_path))
            if not os.path.exists(abs_path): abs_path = os.path.normpath(rel_path)
            if not os.path.exists(abs_path): print(f"FEHLER: Tileset '{rel_path}' nicht gefunden! Platzhalter."); temp_loaded_tilesets.append({'path': rel_path, 'images': [], 'tile_count': 0, 'cols': 0, 'source_w': TILE_WIDTH, 'source_h': TILE_HEIGHT}); continue
            source_w, source_h = TILE_WIDTH, TILE_HEIGHT
            if i < len(source_tileset_sizes) and isinstance(source_tileset_sizes[i], list) and len(source_tileset_sizes[i])==2: source_w, source_h = source_tileset_sizes[i]
            else: print(f"Warnung: Keine Grösse für '{os.path.basename(abs_path)}' gefunden. Fallback.")
            images, count, cols = load_tileset_images(abs_path, source_w, source_h, TILE_WIDTH, TILE_HEIGHT)
            if images: temp_loaded_tilesets.append({'path': abs_path, 'images': images, 'tile_count': count, 'cols': cols, 'source_w': source_w, 'source_h': source_h})
            else: print(f"Fehler Laden '{abs_path}'. Platzhalter."); temp_loaded_tilesets.append({'path': abs_path, 'images': [], 'tile_count': 0, 'cols': 0, 'source_w': source_w, 'source_h': source_h})
        loaded_tilesets = temp_loaded_tilesets; rebuild_palette_data()
        initialize_map_data(new_map_w, new_map_h) # Setzt globale Map-Grössen
        map_tileset_indices = map_load_data['map_tileset_indices']; map_tile_indices = map_load_data['map_tile_indices']; map_collision_data = map_load_data['map_collision_data']
        if len(map_tile_indices) != MAP_HEIGHT_TILES or any(len(row) != MAP_WIDTH_TILES for row in map_tile_indices): raise ValueError("Map Layer Dimensionen stimmen nicht.")
        # Fenster / UI anpassen
        new_win_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        screen = pygame.display.set_mode(new_win_size); background_surface = pygame.Surface(new_win_size).convert(); ui_manager.set_window_resolution(new_win_size)
        if toolbar_panel: toolbar_panel.set_dimensions((SCREEN_WIDTH, TOOLBAR_HEIGHT))
        if palette_container: palette_container.set_dimensions((PALETTE_AREA_WIDTH, MAP_AREA_HEIGHT)); palette_container.set_relative_position((MAP_AREA_WIDTH, TOOLBAR_HEIGHT))
        if palette_scrollbar: palette_scrollbar.set_dimensions((20, MAP_AREA_HEIGHT)); palette_scrollbar.set_relative_position((SCREEN_WIDTH - 20, TOOLBAR_HEIGHT))
        palette_data_needs_rebuild = True # Wichtig für Scrollbar etc.
        pygame.display.set_caption(f"Map Editor - {os.path.basename(filepath)}")
        print(f"Karte geladen: {filepath}")
    except Exception as e:
        print(f"Fehler Verarbeiten Kartendaten: {e}"); traceback.print_exc()
        print("Setze Editor zurück."); clear_all_tilesets(); initialize_map_data()
        try:
            update_layout_dimensions(); new_win_size = (SCREEN_WIDTH, SCREEN_HEIGHT); screen = pygame.display.set_mode(new_win_size); background_surface = pygame.Surface(new_win_size).convert(); ui_manager.set_window_resolution(new_win_size); palette_data_needs_rebuild = True
            pygame.display.set_caption(f"Map Editor - Fehler Laden")
        except pygame.error as display_error: print(f"Display Reset Fehler: {display_error}")

# --- UI Hilfsfunktionen ---

def create_ui_elements():
    """Erstellt die initialen UI Elemente."""
    # (Unverändert zu V10)
    global ui_manager, toolbar_panel, mode_button, palette_container, palette_scrollbar, palette_data_needs_rebuild
    toolbar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, TOOLBAR_HEIGHT)
    toolbar_panel = pygame_gui.elements.UIPanel(relative_rect=toolbar_rect, manager=ui_manager, anchors={'left': 'left', 'right': 'right', 'top': 'top'})
    button_width = 100; button_height = 40; button_margin = 10; current_x = button_margin
    pygame_gui.elements.UIButton(relative_rect=pygame.Rect((current_x, (TOOLBAR_HEIGHT - button_height)//2), (button_width, button_height)), text='Load Map', manager=ui_manager, container=toolbar_panel, object_id='#load_map_button'); current_x += button_width + button_margin
    pygame_gui.elements.UIButton(relative_rect=pygame.Rect((current_x, (TOOLBAR_HEIGHT - button_height)//2), (button_width, button_height)), text='Save Map', manager=ui_manager, container=toolbar_panel, object_id='#save_map_button'); current_x += button_width + button_margin
    mode_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((current_x, (TOOLBAR_HEIGHT - button_height)//2), (button_width+20, button_height)), text=f"Mode: {edit_mode.capitalize()}", manager=ui_manager, container=toolbar_panel, object_id='#mode_button'); current_x += button_width + 20 + button_margin
    pygame_gui.elements.UIButton(relative_rect=pygame.Rect((current_x, (TOOLBAR_HEIGHT - button_height)//2), (button_width+10, button_height)), text='Load Tileset(s)', manager=ui_manager, container=toolbar_panel, object_id='#load_ts_button'); current_x += button_width + 10 + button_margin
    pygame_gui.elements.UIButton(relative_rect=pygame.Rect((current_x, (TOOLBAR_HEIGHT - button_height)//2), (button_width+10, button_height)), text='Clear Tilesets', manager=ui_manager, container=toolbar_panel, object_id='#clear_ts_button'); current_x += button_width + 10 + button_margin
    pygame_gui.elements.UIButton(relative_rect=pygame.Rect((current_x, (TOOLBAR_HEIGHT - button_height)//2), (button_width, button_height)), text='Resize Map', manager=ui_manager, container=toolbar_panel, object_id='#resize_map_button')
    container_rect = pygame.Rect(MAP_AREA_WIDTH, TOOLBAR_HEIGHT, PALETTE_AREA_WIDTH, MAP_AREA_HEIGHT)
    palette_container = pygame_gui.elements.UIScrollingContainer(relative_rect=container_rect, manager=ui_manager)
    scrollbar_rect = pygame.Rect(0, 0, 20, MAP_AREA_HEIGHT); scrollbar_rect.topleft = (MAP_AREA_WIDTH + PALETTE_AREA_WIDTH - 20, TOOLBAR_HEIGHT)
    palette_scrollbar = pygame_gui.elements.UIVerticalScrollBar(relative_rect=scrollbar_rect, visible_percentage=1.0, manager=ui_manager)
    palette_data_needs_rebuild = True

def update_palette_ui():
    """Aktualisiert Scroll-Offset, zeichnet Tiles und aktualisiert Scrollbar."""
    # --- KORRIGIERT: Robusterer Check am Anfang ---
    global palette_container, palette_scrollbar, palette_scroll_offset_y, palette_data_needs_rebuild
    if not ui_manager or not palette_container or not palette_scrollbar:
        # UI Elemente noch nicht bereit, nichts tun
        return

    # --- 1. Scroll-Offset aus Scrollbar lesen ---
    scroll_pos_norm = palette_scrollbar.scroll_position
    view_height = MAP_AREA_HEIGHT
    content_height = MAP_AREA_HEIGHT # Standardwert
    # Prüfe ob scrollable_container existiert
    if palette_container.scrollable_container:
         content_height = max(palette_container.scrollable_container.rect.height, view_height)
    max_scroll = max(0, content_height - view_height)
    palette_scroll_offset_y = round(scroll_pos_norm * max_scroll)

    # --- 2. Tiles in Container zeichnen (mit Offset) ---
    try:
        # Prüfe, ob der Container und seine Surface gültig sind
        container = palette_container.get_container()
        if container and hasattr(container, 'surface') and container.surface:
            container_surface = container.surface
            container_surface.fill(LIGHT_GRAY) # Hintergrund löschen
        else:
            # Container (noch) nicht bereit zum Zeichnen
            return

        num_cols = PALETTE_WIDTH_TILES; current_x = 0; current_y = 0; max_y = 0
        for flat_idx, img in enumerate(all_tile_images_flat):
            draw_pos_x = current_x; draw_pos_y = current_y - palette_scroll_offset_y
            if draw_pos_y + TILE_HEIGHT > 0 and draw_pos_y < MAP_AREA_HEIGHT:
                 container_surface.blit(img, (draw_pos_x, draw_pos_y))
                 if flat_idx == current_flat_palette_index: pygame.draw.rect(container_surface, RED, (draw_pos_x, draw_pos_y, TILE_WIDTH, TILE_HEIGHT), 2)
            current_x += TILE_WIDTH
            if current_x >= PALETTE_AREA_WIDTH: current_x = 0; current_y += TILE_HEIGHT
            if current_x == 0 and current_y > 0: max_y = current_y

    except AttributeError as e:
        # Fängt Fehler ab, wenn z.B. get_container() fehlschlägt
        print(f"Warnung: Zugriff auf palette_container fehlgeschlagen: {e}")
        return

    # --- 3. Scrollbar aktualisieren (nur wenn Daten neu sind) ---
    if palette_data_needs_rebuild:
        new_content_height = max(max_y + TILE_HEIGHT, MAP_AREA_HEIGHT)
        try:
            palette_container.set_scrollable_area_dimensions((PALETTE_AREA_WIDTH, new_content_height))
            if new_content_height > view_height:
                visible_perc = max(0.01, min(1.0, view_height / new_content_height))
                palette_scrollbar.set_visible_percentage(visible_perc)
                # Setze Scrollposition neu basierend auf aktuellem Offset und neuer Höhe
                if not palette_scrollbar.is_focused: # Nur wenn Nutzer nicht gerade scrollt
                    new_max_scroll = max(0, new_content_height - view_height)
                    if new_max_scroll > 0: current_scroll_pos_norm = max(0.0, min(1.0, palette_scroll_offset_y / new_max_scroll)); palette_scrollbar.set_scroll_position(current_scroll_pos_norm)
                    else: palette_scrollbar.set_scroll_position(0.0)
                palette_scrollbar.show()
            else: palette_scrollbar.set_visible_percentage(1.0); palette_scrollbar.hide(); palette_scroll_offset_y = 0
        except Exception as e: print(f"Fehler Scrollbar Update: {e}")
        palette_data_needs_rebuild = False # Daten-Update abgeschlossen

def handle_palette_click(mouse_pos):
     """Verarbeitet Klicks innerhalb des Paletten-Containers."""
     # (Unverändert zu V10)
     global current_flat_palette_index, current_tileset_index, current_tile_index_in_tileset, palette_data_needs_rebuild
     if not palette_container or not PALETTE_AREA_RECT.collidepoint(mouse_pos): return
     relative_pos = (mouse_pos[0] - PALETTE_AREA_RECT.left, mouse_pos[1] - PALETTE_AREA_RECT.top)
     virtual_x = relative_pos[0]; virtual_y = relative_pos[1] + palette_scroll_offset_y
     col = virtual_x // TILE_WIDTH; row = virtual_y // TILE_HEIGHT
     num_cols = PALETTE_WIDTH_TILES; clicked_flat_index = row * num_cols + col
     if 0 <= clicked_flat_index < len(all_tile_images_flat):
          if current_flat_palette_index != clicked_flat_index:
            current_flat_palette_index = clicked_flat_index
            if current_flat_palette_index < len(all_tile_mapping):
                current_tileset_index, current_tile_index_in_tileset = all_tile_mapping[current_flat_palette_index]
                print(f"Palette: Flat={current_flat_palette_index}, TS={current_tileset_index}, Idx={current_tile_index_in_tileset}")
                palette_data_needs_rebuild = True # Trigger redraw of highlight
            else: print(f"Fehler: Mapping ungültig für Index {current_flat_palette_index}."); current_flat_palette_index = -1; current_tileset_index = -1; current_tile_index_in_tileset = -1
     else: pass

def open_resize_map_window():
     """Öffnet ein Fenster zur Eingabe der neuen Kartengrösse."""
     # (Unverändert zu V10)
     global resize_map_window, ui_manager
     if resize_map_window is not None and resize_map_window.alive(): resize_map_window.focus(); return
     window_rect = pygame.Rect(0, 0, 300, 200); window_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
     resize_map_window = pygame_gui.windows.UIWindow(rect=window_rect, manager=ui_manager, window_display_title="Resize Map")
     pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 10, 100, 30), text="New Width:", manager=ui_manager, container=resize_map_window)
     entry_w = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(120, 10, 150, 30), manager=ui_manager, container=resize_map_window, object_id="#resize_width_entry"); entry_w.set_text(str(MAP_WIDTH_TILES)); entry_w.set_allowed_characters('numbers')
     pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 50, 100, 30), text="New Height:", manager=ui_manager, container=resize_map_window)
     entry_h = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(120, 50, 150, 30), manager=ui_manager, container=resize_map_window, object_id="#resize_height_entry"); entry_h.set_text(str(MAP_HEIGHT_TILES)); entry_h.set_allowed_characters('numbers')
     pygame_gui.elements.UIButton(relative_rect=pygame.Rect(-190, -50, 80, 30), text="OK", manager=ui_manager, container=resize_map_window, object_id="#resize_ok_button", anchors={'left': 'right', 'right': 'right', 'top':'bottom', 'bottom':'bottom'})
     pygame_gui.elements.UIButton(relative_rect=pygame.Rect(-100, -50, 80, 30), text="Cancel", manager=ui_manager, container=resize_map_window, object_id="#resize_cancel_button", anchors={'left': 'right', 'right': 'right', 'top':'bottom', 'bottom':'bottom'})

def handle_map_interaction(mouse_pos, button_left_pressed, button_right_pressed):
    """Verarbeitet Klicks und Malen auf der Karte."""
    # (Unverändert zu V10)
    global last_painted_tile_coords, map_tileset_indices, map_tile_indices, map_collision_data
    map_coords = get_map_coords_from_pos(mouse_pos[0], mouse_pos[1])
    if not map_coords: last_painted_tile_coords = None; return
    row, col = map_coords
    if map_coords == last_painted_tile_coords and (is_mouse_down_left or is_mouse_down_right): return
    if button_left_pressed:
        if edit_mode == 'tile':
            if current_tileset_index != -1 and current_tile_index_in_tileset != -1: map_tileset_indices[row][col] = current_tileset_index; map_tile_indices[row][col] = current_tile_index_in_tileset
        elif edit_mode == 'collision': map_collision_data[row][col] = not map_collision_data[row][col]
        last_painted_tile_coords = map_coords
    elif button_right_pressed:
        if edit_mode == 'tile': map_tileset_indices[row][col] = -1; map_tile_indices[row][col] = -1
        elif edit_mode == 'collision': map_collision_data[row][col] = False
        last_painted_tile_coords = map_coords

# --- Zeichenfunktionen ---

def draw_grid(surface, start_x, start_y, width, height, tile_w, tile_h, color):
    # (Unverändert zu V10)
    for x in range(start_x, start_x + width + 1, tile_w): pygame.draw.line(surface, color, (x, start_y), (x, start_y + height))
    for y in range(start_y, start_y + height + 1, tile_h): pygame.draw.line(surface, color, (start_x, y), (start_x + width, y))

def draw_map_area(target_surface):
    """Zeichnet den Kartenbereich auf die HINTERGRUND-Surface."""
    # (Unverändert zu V10)
    try:
        map_draw_area = target_surface.subsurface(MAP_AREA_RECT); map_draw_area.fill(BLACK)
        for r in range(MAP_HEIGHT_TILES):
            for c in range(MAP_WIDTH_TILES):
                ts_idx = map_tileset_indices[r][c]; tile_idx = map_tile_indices[r][c]
                if ts_idx != -1 and tile_idx != -1 and ts_idx < len(loaded_tilesets):
                    tileset = loaded_tilesets[ts_idx]
                    if isinstance(tileset.get('images'), list) and tile_idx < len(tileset['images']): img = tileset['images'][tile_idx]; map_draw_area.blit(img, (c*TILE_WIDTH, r*TILE_HEIGHT))
                if map_collision_data[r][c]: collision_surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA); collision_surface.fill(TRANSPARENT_RED); map_draw_area.blit(collision_surface, (c*TILE_WIDTH, r*TILE_HEIGHT))
        draw_grid(map_draw_area, 0, 0, MAP_AREA_WIDTH, MAP_AREA_HEIGHT, TILE_WIDTH, TILE_HEIGHT, GRAY)
    except ValueError as e: print(f"Fehler Map-Subsurface: {e}"); pygame.draw.rect(target_surface, RED, MAP_AREA_RECT, 2)


# --- KORRIGIERT: draw_ui_info Signatur und Verwendung ---
def draw_ui_info(surface, medium_font, small_font):
     """Zeichnet UI-Texte (Statusanzeige)."""
     y_offset = 10 ; x_pos = MAP_AREA_WIDTH + 10 # Im Palettenbereich starten
     sel_text = "Ausgewählt: Nichts"
     if current_flat_palette_index != -1 and current_flat_palette_index < len(all_tile_mapping):
          ts_idx, t_idx = all_tile_mapping[current_flat_palette_index]
          if ts_idx < len(loaded_tilesets):
              ts_name = os.path.basename(loaded_tilesets[ts_idx].get('path', '?'))
              sel_text = f"Ausgew.: {ts_name} ({t_idx})"
          else: sel_text = "Ausgew.: Fehler (TS Index!)"
     elif current_flat_palette_index != -1: sel_text = "Ausgew.: Fehler (Mapping!)"

     # Prüfe, ob Font-Objekt existiert, bevor es verwendet wird
     if medium_font: # <-- Parameter Name hier verwenden
        try:
             # Verwende Parameter medium_font
             sel_surf = medium_font.render(sel_text, True, BLACK)
             # Zeichne auf Hauptscreen, Position unter Toolbar im Palettenbereich
             surface.blit(sel_surf, (x_pos, TOOLBAR_HEIGHT + y_offset))
             y_offset += 30
        except Exception as e:
             print(f"Fehler beim Rendern mit medium_font: {e}")

     # Anleitung auskommentiert
     # if small_font: # <-- Parameter Name hier verwenden
     #    ... instr = ...
     #    for line in instr: line_surf = small_font.render(...) ...

# --- Hauptfunktion ---

def main():
    # --- KORRIGIERT: Font Variablen sind lokal zu main ---
    global screen, clock, ui_manager, background_surface
    global is_mouse_down_left, is_mouse_down_right, last_painted_tile_coords
    global edit_mode, current_flat_palette_index, current_tileset_index, current_tile_index_in_tileset
    global palette_data_needs_rebuild, palette_scroll_offset_y
    global resize_map_window
    global MAP_WIDTH_TILES, MAP_HEIGHT_TILES, TILE_WIDTH, TILE_HEIGHT
    global MAP_AREA_WIDTH, MAP_AREA_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, PALETTE_AREA_WIDTH
    global MAP_AREA_RECT, PALETTE_AREA_RECT, toolbar_panel, mode_button, palette_container, palette_scrollbar

    # 1. Pygame und Fonts
    pygame.init(); pygame.font.init()
    # --- KORRIGIERT: Fonts als lokale Variablen ---
    font_small = None; font_medium = None
    try:
        font_small = pygame.font.SysFont(None, 24)
        font_medium = pygame.font.SysFont(None, 30)
    except Exception as e:
        print(f"Fehler SysFont: {e}")
        try: font_small = pygame.font.Font(None, 24); font_medium = pygame.font.Font(None, 30)
        except Exception as e2: print(f"Fehler Fallback Font: {e2}"); pygame.quit(); sys.exit()

    # 2. Layout & Fenster
    update_layout_dimensions()
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)); pygame.display.set_caption("Map Editor"); clock = pygame.time.Clock()
        background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
    except pygame.error as e: print(f"Fehler Fenster: {e}"); pygame.quit(); sys.exit()

    # 3. Pygame GUI Manager
    try: ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e: print(f"Fehler pygame_gui: {e}"); pygame.quit(); sys.exit()

    # 4. UI Elemente erstellen
    create_ui_elements()

    # 5. Map Daten initialisieren
    initialize_map_data()

    # 6. Haupt-Schleife
    running = True
    while running:
        time_delta = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        # --- Event-Verarbeitung ---
        for event in pygame.event.get():
            # --- A: Pygame GUI Events verarbeiten (zuerst) ---
            consumed_by_gui = ui_manager.process_events(event)

            # --- B: Globale Events (Quit, Tastatur-Shortcuts) ---
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif not ui_manager.get_focus_set() or not isinstance(ui_manager.get_focus_set(), pygame_gui.elements.UITextEntryLine):
                    if event.key == pygame.K_c:
                         edit_mode = 'collision' if edit_mode == 'tile' else 'tile'
                         if mode_button: mode_button.set_text(f"Mode: {edit_mode.capitalize()}")
                         print(f"Wechsle zu Modus: {edit_mode}")
                    elif event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META): save_map()
                    elif event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META): load_map()

            # --- C: Spezifische UI Events behandeln (Button Klicks etc.) ---
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                obj_id = getattr(event.ui_element, 'object_ids', [None])[-1]
                if obj_id == '#load_map_button': load_map()
                elif obj_id == '#save_map_button': save_map()
                elif obj_id == '#mode_button':
                    edit_mode = 'collision' if edit_mode == 'tile' else 'tile'
                    if mode_button: mode_button.set_text(f"Mode: {edit_mode.capitalize()}")
                    print(f"Wechsle zu Modus: {edit_mode}")
                elif obj_id == '#load_ts_button': select_tilesets_and_load()
                elif obj_id == '#clear_ts_button': clear_all_tilesets()
                elif obj_id == '#resize_map_button': open_resize_map_window()
                elif obj_id == '#resize_ok_button' and resize_map_window:
                     width_entry = ui_manager.find_element_by_object_id(container=resize_map_window, object_id='#resize_width_entry')
                     height_entry = ui_manager.find_element_by_object_id(container=resize_map_window, object_id='#resize_height_entry')
                     if width_entry and height_entry:
                          try:
                               new_w = int(width_entry.get_text()); new_h = int(height_entry.get_text())
                               if new_w > 0 and new_h > 0:
                                    resize_map_data(new_w, new_h) # Passt globale Grössen an
                                    new_win_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
                                    screen = pygame.display.set_mode(new_win_size); background_surface = pygame.Surface(new_win_size).convert(); ui_manager.set_window_resolution(new_win_size)
                                    if toolbar_panel: toolbar_panel.set_dimensions((SCREEN_WIDTH, TOOLBAR_HEIGHT))
                                    container_rect_new = pygame.Rect(MAP_AREA_WIDTH, TOOLBAR_HEIGHT, PALETTE_AREA_WIDTH, MAP_AREA_HEIGHT)
                                    if palette_container: palette_container.set_relative_rect(container_rect_new); palette_container.set_dimensions((PALETTE_AREA_WIDTH, MAP_AREA_HEIGHT))
                                    scrollbar_rect_new = pygame.Rect(container_rect_new.right - 20, container_rect_new.top, 20, container_rect_new.height)
                                    if palette_scrollbar: palette_scrollbar.set_relative_rect(scrollbar_rect_new); palette_scrollbar.set_dimensions((20, MAP_AREA_HEIGHT))
                                    palette_data_needs_rebuild = True
                                    print("Resize abgeschlossen.")
                               else: print("Bitte positive Zahlen > 0 eingeben.")
                          except ValueError: print("Ungültige Zahleneingabe.")
                          except Exception as e: print(f"Fehler bei Resize: {e}"); traceback.print_exc()
                     resize_map_window.kill(); resize_map_window = None
                elif obj_id == '#resize_cancel_button' and resize_map_window:
                     resize_map_window.kill(); resize_map_window = None

            # --- Scrollbar Event Logik entfernt ---

            elif event.type == pygame_gui.UI_WINDOW_CLOSE:
                 if event.ui_element == resize_map_window: resize_map_window = None

            # --- D: Maus Events für Map/Palette (nur wenn NICHT vom GUI verarbeitet) ---
            if not consumed_by_gui:
                # --- Prüfung auf 'active_window' entfernt ---
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Links
                        is_mouse_down_left = True
                        if PALETTE_AREA_RECT.collidepoint(mouse_pos): handle_palette_click(mouse_pos)
                        elif MAP_AREA_RECT.collidepoint(mouse_pos): handle_map_interaction(mouse_pos, True, False)
                    elif event.button == 3: # Rechts
                        is_mouse_down_right = True
                        # Rechtsklick nur auf Map, nicht Palette
                        if MAP_AREA_RECT.collidepoint(mouse_pos): handle_map_interaction(mouse_pos, False, True)
                elif event.type == pygame.MOUSEBUTTONUP:
                     if event.button == 1: is_mouse_down_left = False; last_painted_tile_coords = None
                     elif event.button == 3: is_mouse_down_right = False; last_painted_tile_coords = None
                elif event.type == pygame.MOUSEMOTION:
                     # Malen nur auf Map
                     if is_mouse_down_left and MAP_AREA_RECT.collidepoint(mouse_pos): handle_map_interaction(mouse_pos, True, False)
                     elif is_mouse_down_right and MAP_AREA_RECT.collidepoint(mouse_pos): handle_map_interaction(mouse_pos, False, True)


        # --- Update ---
        ui_manager.update(time_delta)
        # Palette immer updaten
        update_palette_ui()

        # --- Zeichnen ---
        if screen:
            background_surface.fill(GRAY); draw_map_area(background_surface)
            screen.blit(background_surface, (0, 0))
            ui_manager.draw_ui(screen)
            # --- KORRIGIERT: Fonts an draw_ui_info übergeben ---
            draw_ui_info(screen, font_medium, font_small) # Übergabe der lokalen Font-Variablen
            pygame.display.flip()
        else: pygame.time.wait(100)

    # --- Ende ---
    pygame.quit()
    sys.exit()

# --- Skript starten ---
if __name__ == "__main__":
    main()