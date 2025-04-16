import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog, simpledialog # simpledialog für Grössenabfrage
import json
import traceback # Für detailliertere Fehlermeldungen

# --- Konstanten und Konfiguration ---

# Dies ist die ZIEL-Grösse für alle Tiles im Editor (Pixel)
TILE_WIDTH = 32
TILE_HEIGHT = 32
# Standard-Annahme für Quell-Tilesets, falls Dimensionen passen (Pixel)
DEFAULT_SOURCE_TILE_W = 32
DEFAULT_SOURCE_TILE_H = 32

# Standard-Kartengrösse (in Tiles)
DEFAULT_MAP_WIDTH_TILES = 25
DEFAULT_MAP_HEIGHT_TILES = 20
# Breite der Tile-Palette (in Tiles)
PALETTE_WIDTH_TILES = 6

# Aktuelle Kartengrösse (wird ggf. beim Laden angepasst)
MAP_WIDTH_TILES = DEFAULT_MAP_WIDTH_TILES
MAP_HEIGHT_TILES = DEFAULT_MAP_HEIGHT_TILES

# Berechnete Dimensionen (werden ggf. beim Laden angepasst)
MAP_AREA_WIDTH = MAP_WIDTH_TILES * TILE_WIDTH
MAP_AREA_HEIGHT = MAP_HEIGHT_TILES * TILE_HEIGHT
PALETTE_AREA_WIDTH = PALETTE_WIDTH_TILES * TILE_WIDTH
SCREEN_WIDTH = MAP_AREA_WIDTH + PALETTE_AREA_WIDTH
SCREEN_HEIGHT = MAP_AREA_HEIGHT

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
TRANSPARENT_RED = (255, 0, 0, 128) # Für Kollisionsanzeige

# Frames pro Sekunde
FPS = 60

# --- Globale Variablen ---
screen = None
clock = None
font_small = None
font_medium = None

# Editor-Status
# loaded_tilesets speichert jetzt auch source_w/h
loaded_tilesets = [] # List[Dict{'path':str, 'images':[Surf], 'tile_count':int, 'cols':int, 'source_w':int, 'source_h':int}]
all_tile_images_flat = [] # Alle Tile-Bilder (skaliert auf Editor-Grösse) in einer flachen Liste für die Palette
all_tile_mapping = [] # Mapping von flachem Index zu (tileset_idx, tile_idx_in_tileset)

# Map-Daten (mehrere Layer)
map_tileset_indices = []
map_tile_indices = []
map_collision_data = [] # True = Kollision, False = keine Kollision

# Aktuell ausgewählte Elemente
current_tileset_index = -1
current_tile_index_in_tileset = -1
current_flat_palette_index = -1 # Index in all_tile_images_flat

# Maus-Status für Malen
is_mouse_down_left = False
is_mouse_down_right = False
last_painted_tile_coords = None

# Editier-Modus ('tile' oder 'collision')
edit_mode = 'tile'

# --- Hilfsfunktionen ---

def initialize_map_data(width=DEFAULT_MAP_WIDTH_TILES, height=DEFAULT_MAP_HEIGHT_TILES):
    """Initialisiert oder setzt Map-Daten zurück, optional mit neuen Dimensionen."""
    global map_tileset_indices, map_tile_indices, map_collision_data
    global MAP_WIDTH_TILES, MAP_HEIGHT_TILES
    # Setze die globalen Variablen für die aktuelle Map-Grösse
    MAP_WIDTH_TILES = width
    MAP_HEIGHT_TILES = height
    # Erstelle die leeren Datenstrukturen basierend auf der Grösse
    map_tileset_indices = [[-1 for _ in range(width)] for _ in range(height)]
    map_tile_indices = [[-1 for _ in range(width)] for _ in range(height)]
    map_collision_data = [[False for _ in range(width)] for _ in range(height)]
    print(f"Map Daten initialisiert ({width}x{height} Tiles)")

def load_tileset_images(filepath, source_tile_width, source_tile_height, target_tile_width, target_tile_height):
    """
    Lädt Tileset, extrahiert Tiles basierend auf der *Source*-Grösse
    und skaliert sie auf die *Target*-Grösse.
    Gibt zurück: (Liste der skalierten Tile-Surfaces, Anzahl Tiles, Spaltenanzahl basierend auf Source-Grösse)
    """
    if not os.path.exists(filepath):
        print(f"Fehler: Tileset-Datei nicht gefunden: {filepath}")
        return None, 0, 0

    print(f"Lade '{os.path.basename(filepath)}': Erwartete Quell-Tilegrösse {source_tile_width}x{source_tile_height}, Zielgrösse {target_tile_width}x{target_tile_height}")

    try:
        # Bild laden (ohne convert/convert_alpha hier, da Pygame display evtl. noch nicht existiert)
        tileset_image = pygame.image.load(filepath)
    except pygame.error as e:
        print(f"Fehler beim Laden von Bilddatei '{filepath}': {e}")
        return None, 0, 0

    img_w, img_h = tileset_image.get_size()
    tile_images = [] # Hier sammeln wir die skalierten Tile-Surfaces
    any_scaled = False # Merker, ob Skalierung stattfand

    # Prüfe auf gültige Source-Tilegrösse
    if source_tile_width <= 0 or source_tile_height <= 0:
         print(f"Fehler: Ungültige Quell-Tilegrösse ({source_tile_width}x{source_tile_height}) für {os.path.basename(filepath)}")
         return None, 0, 0

    # Berechne Raster basierend auf der *Source*-Tilegrösse
    cols = img_w // source_tile_width
    rows = img_h // source_tile_height

    # Warnung, wenn Dimensionen nicht exakt passen
    if img_w % source_tile_width != 0 or img_h % source_tile_height != 0:
         print(f"Warnung: Bilddimensionen ({img_w}x{img_h}) von '{os.path.basename(filepath)}' "
               f"sind nicht exakt durch Quell-Tilegrösse ({source_tile_width}x{source_tile_height}) teilbar. "
               f"Einige Pixel am Rand werden ignoriert.")

    # Iteriere durch das Raster (basierend auf Source-Grösse)
    for row in range(rows):
        for col in range(cols):
            # Extrahiere das Tile mit *Source*-Grösse
            tile_rect = pygame.Rect(col * source_tile_width, row * source_tile_height,
                                     source_tile_width, source_tile_height)
            try:
                tile_surface = tileset_image.subsurface(tile_rect)

                # Skaliere auf *Target*-Grösse (Editor-Grösse), falls nötig
                # Mache dies immer, um sicherzustellen, dass alle Tiles im Editor die Zielgrösse haben
                if source_tile_width != target_tile_width or source_tile_height != target_tile_height:
                    any_scaled = True # Merken, dass skaliert wurde
                    try:
                        # smoothscale für bessere Qualität
                        scaled_tile = pygame.transform.smoothscale(tile_surface, (target_tile_width, target_tile_height))
                    except ValueError:
                         # Fallback, falls smoothscale Probleme macht
                         print(f"Warnung: smoothscale fehlgeschlagen für Tile ({row},{col}) in {os.path.basename(filepath)}. Verwende scale.")
                         scaled_tile = pygame.transform.scale(tile_surface, (target_tile_width, target_tile_height))
                    tile_images.append(scaled_tile) # Füge das *skalierte* Bild hinzu
                else:
                    # Grösse passt bereits, direkt hinzufügen
                    # Optional: Hier konvertieren, falls Pygame Display schon initialisiert wäre
                    tile_images.append(tile_surface)

            except ValueError as e:
                 # Fehler bei subsurface (z.B. Rect ungültig)
                 print(f"Fehler beim Extrahieren von Subsurface bei ({row},{col}) in {os.path.basename(filepath)}: {e}")
                 continue # Nächstes Tile versuchen

    if any_scaled:
        print(f"Hinweis: Tiles aus '{os.path.basename(filepath)}' wurden auf "
              f"{target_tile_width}x{target_tile_height} skaliert.")

    print(f"{len(tile_images)} Tiles aus '{os.path.basename(filepath)}' erfolgreich extrahiert/skaliert.")
    # Wichtig: 'cols' gibt die Anzahl der Spalten basierend auf der *Source*-Grösse zurück
    return tile_images, len(tile_images), cols

def rebuild_palette_data():
    """Erstellt die flache Liste aller Tiles und das Mapping neu."""
    global all_tile_images_flat, all_tile_mapping
    all_tile_images_flat = []
    all_tile_mapping = []
    for ts_idx, tileset in enumerate(loaded_tilesets):
        # Stelle sicher, dass 'images' existiert und eine Liste ist
        if isinstance(tileset.get('images'), list):
            for tile_idx, img in enumerate(tileset['images']):
                all_tile_images_flat.append(img)
                all_tile_mapping.append((ts_idx, tile_idx))
        else:
            print(f"Warnung: Fehlende oder ungültige 'images' für Tileset Index {ts_idx} ({tileset.get('path')})")
    print(f"Palette neu aufgebaut mit {len(all_tile_images_flat)} Tiles.")

def ask_source_tile_size(parent_tk_window, filepath):
     """Fragt den Benutzer nach der originalen Tile-Grösse für eine Datei."""
     title = f"Original Tile-Grösse für: {os.path.basename(filepath)}"
     # Frage nach Breite
     w = simpledialog.askinteger("Original Breite",
                                 f"Breite der Tiles in\n'{os.path.basename(filepath)}'?\n(Pixel)",
                                 parent=parent_tk_window,
                                 initialvalue=DEFAULT_SOURCE_TILE_W, # Standardwert anbieten
                                 minvalue=1) # Mindestens 1 Pixel
     if w is None: # Benutzer hat abgebrochen
         return None, None
     # Frage nach Höhe
     h = simpledialog.askinteger("Original Höhe",
                                 f"Höhe der Tiles in\n'{os.path.basename(filepath)}'?\n(Pixel)",
                                 parent=parent_tk_window,
                                 initialvalue=DEFAULT_SOURCE_TILE_H, # Standardwert anbieten
                                 minvalue=1) # Mindestens 1 Pixel
     if h is None: # Benutzer hat abgebrochen
         return None, None
     return w, h

def select_tilesets_and_load():
    """Öffnet Dialog, fragt ggf. nach Tile-Grössen und lädt Tilesets."""
    global loaded_tilesets
    # Temporäres Tkinter-Fenster für Dialoge
    root = tk.Tk()
    root.withdraw() # Hauptfenster verstecken
    print("Öffne Dialog zur Auswahl von Tileset-Dateien...")
    # Erlaube Auswahl mehrerer Dateien
    filepaths = filedialog.askopenfilenames(
        title="Wähle ein oder mehrere Tilesets",
        initialdir=os.path.dirname(__file__) if "__file__" in locals() else ".", # Start im Skript-Verzeichnis
        filetypes=[("Bilddateien", "*.png *.jpg *.jpeg"), ("Alle Dateien", "*.*")]
    )
    # root wird erst später zerstört, falls Dialoge (ask_source_tile_size) benötigt werden

    if not filepaths:
        print("Keine Dateien ausgewählt.")
        root.destroy() # Tkinter-Fenster schliessen
        return False # Signalisiert: Nichts geladen

    new_tilesets = [] # Sammle hier gültige, neu geladene Tilesets
    # Gehe jede ausgewählte Datei durch
    for fp in filepaths:
        print(f"Verarbeite: {fp}")
        source_w, source_h = DEFAULT_SOURCE_TILE_W, DEFAULT_SOURCE_TILE_H # Standardannahme

        try:
            # Lade Bild nur für Dimensionsprüfung (benötigt pygame.init())
            img = pygame.image.load(fp)
            img_w, img_h = img.get_size()
            del img # Bild wieder aus Speicher entfernen

            # Prüfen, ob Dimensionen durch Editor-Standard-TILEGRÖSSE teilbar sind
            if img_w % TILE_WIDTH != 0 or img_h % TILE_HEIGHT != 0:
                 print(f"Bilddimensionen ({img_w}x{img_h}) nicht durch Editor-Zielgrösse ({TILE_WIDTH}x{TILE_HEIGHT}) teilbar.")
                 # Frage Benutzer nach der tatsächlichen *Original*-Grösse dieses Tilesets
                 source_w, source_h = ask_source_tile_size(root, fp)
                 if source_w is None or source_h is None:
                      print(f"Auswahl der Grösse für '{os.path.basename(fp)}' abgebrochen. Überspringe Datei.")
                      continue # Überspringe diese Datei und mache mit der nächsten weiter
            else:
                 # Annahme: Die Standardgrösse passt auch für die Quelle
                 source_w, source_h = TILE_WIDTH, TILE_HEIGHT
                 print(f"Bilddimensionen ({img_w}x{img_h}) passen zur Editor-Zielgrösse ({source_w}x{source_h}). Nehme diese als Quellgrösse an.")

            # Lade nun die Tiles mit der ermittelten Source-Grösse
            # und skaliere sie auf die Target-Grösse (Editor-Konstanten)
            images, count, cols = load_tileset_images(fp, source_w, source_h, TILE_WIDTH, TILE_HEIGHT)

            # Wenn erfolgreich geladen, zum Ergebnis hinzufügen
            if images:
                new_tilesets.append({
                    'path': fp,           # Pfad zur Originaldatei
                    'images': images,     # Liste der skalierten Tile-Surfaces
                    'tile_count': count,  # Anzahl der Tiles
                    'cols': cols,         # Spalten im Original-Raster
                    'source_w': source_w, # Originalbreite (gespeichert für save/load)
                    'source_h': source_h  # Originalhöhe (gespeichert für save/load)
                })
            else:
                # Fehler beim Laden, auch nach Grössenangabe
                print(f"Konnte Tileset '{os.path.basename(fp)}' trotz Grössenangabe nicht verarbeiten.")

        except pygame.error as e:
            # Fehler beim Lesen der Bilddatei (z.B. Format nicht unterstützt)
            print(f"Fehler beim Lesen der Dimensionen oder Laden von '{os.path.basename(fp)}': {e}")
        except Exception as e:
             # Andere unerwartete Fehler
             print(f"Allgemeiner Fehler bei Verarbeitung von '{os.path.basename(fp)}': {e}")
             traceback.print_exc() # Zeige detaillierten Traceback

    # Tkinter-Fenster jetzt sicher schliessen
    root.destroy()

    # Prüfen, ob überhaupt Tilesets erfolgreich geladen wurden
    if not new_tilesets:
        print("Konnte keine gültigen Tilesets laden.")
        return False # Signalisiert: Ladevorgang fehlgeschlagen

    # Ersetze die alte Liste der Tilesets komplett durch die neu geladenen
    loaded_tilesets = new_tilesets
    # Baue die Palette mit den neuen Daten auf
    rebuild_palette_data()
    return True # Signalisiert: Erfolgreich geladen

def get_palette_tile_from_pos(mouse_x, mouse_y):
    """Gibt den flachen Index des Tiles in der Palette unter der Mausposition zurück, oder -1."""
    # Prüfen, ob Maus im Palettenbereich (rechts vom Map-Bereich) ist
    if mouse_x < MAP_AREA_WIDTH:
        return -1 # Klick war nicht in der Palette

    # Berechne Koordinaten relativ zur oberen linken Ecke der Palette
    palette_x = mouse_x - MAP_AREA_WIDTH
    palette_y = mouse_y

    # Berechne Spalte und Zeile innerhalb des Paletten-Gitters
    col = palette_x // TILE_WIDTH
    row = palette_y // TILE_HEIGHT

    # Berechne den flachen Index in der `all_tile_images_flat` Liste
    # Basierend auf der Breite der Palette in Tiles (PALETTE_WIDTH_TILES)
    flat_index = row * PALETTE_WIDTH_TILES + col

    # Prüfen, ob der berechnete Index gültig ist (innerhalb der Liste)
    if 0 <= flat_index < len(all_tile_images_flat):
        return flat_index
    else:
        return -1 # Kein gültiges Tile an dieser Position

def get_map_coords_from_pos(mouse_x, mouse_y):
    """Gibt die Karten-Koordinaten (row, col) unter der Mausposition zurück, oder None."""
    # Prüfen, ob Maus ausserhalb des Kartenbereichs (links oben) ist
    if mouse_x >= MAP_AREA_WIDTH or mouse_y >= MAP_AREA_HEIGHT or mouse_x < 0 or mouse_y < 0:
        return None

    # Berechne Spalte und Zeile im Karten-Gitter
    map_col = mouse_x // TILE_WIDTH
    map_row = mouse_y // TILE_HEIGHT

    # Zusätzliche Sicherheitsprüfung (sollte durch obige Prüfung abgedeckt sein)
    if 0 <= map_row < MAP_HEIGHT_TILES and 0 <= map_col < MAP_WIDTH_TILES:
        return map_row, map_col
    else:
        # Sollte eigentlich nicht vorkommen
        return None

def handle_map_interaction(mouse_pos, button_left_pressed, button_right_pressed):
    """Verarbeitet Klicks und Malen auf der Karte, basierend auf dem Modus."""
    global last_painted_tile_coords, map_tileset_indices, map_tile_indices, map_collision_data

    # Ermittle die Kartenkoordinaten unter der Maus
    map_coords = get_map_coords_from_pos(mouse_pos[0], mouse_pos[1])

    # Wenn Maus nicht über der Karte ist, Aktion beenden und Mal-Status zurücksetzen
    if not map_coords:
        last_painted_tile_coords = None
        return

    row, col = map_coords

    # Beim "Malen" (Taste gedrückt halten): Nur Aktion ausführen,
    # wenn die Maus sich auf eine *neue* Kachel bewegt hat.
    if map_coords == last_painted_tile_coords and (is_mouse_down_left or is_mouse_down_right):
         return # Keine Aktion auf derselben Kachel ohne Bewegung

    # --- Aktionen basierend auf gedrückter Taste und Modus ---
    if button_left_pressed: # Linksklick / Linke Taste gehalten
        if edit_mode == 'tile':
            # Modus 'tile': Platziere das aktuell ausgewählte Tile
            if current_tileset_index != -1 and current_tile_index_in_tileset != -1:
                map_tileset_indices[row][col] = current_tileset_index
                map_tile_indices[row][col] = current_tile_index_in_tileset
                # Optional: print für Debugging
                # print(f"Setze Tile (TS: {current_tileset_index}, Idx: {current_tile_index_in_tileset}) auf ({row}, {col})")
            # else: print("Kein Tile zum Platzieren ausgewählt.")
        elif edit_mode == 'collision':
            # Modus 'collision': Schalte Kollision für die Kachel um
            map_collision_data[row][col] = not map_collision_data[row][col]
            # Optional: print für Debugging
            # print(f"Setze Kollision auf {map_collision_data[row][col]} bei ({row}, {col})")

        # Merke die zuletzt bemalte Koordinate für die "Malen"-Logik
        last_painted_tile_coords = map_coords

    elif button_right_pressed: # Rechtsklick / Rechte Taste gehalten
        if edit_mode == 'tile':
            # Modus 'tile': Lösche das Tile an dieser Position
            map_tileset_indices[row][col] = -1 # Kein Tileset Index
            map_tile_indices[row][col] = -1    # Kein Tile Index
            # Optional: print für Debugging
            # print(f"Lösche Tile bei ({row}, {col})")
        elif edit_mode == 'collision':
             # Modus 'collision': Setze Kollision sicher auf False (entfernen)
             map_collision_data[row][col] = False
             # Optional: print für Debugging
             # print(f"Entferne Kollision bei ({row}, {col})")

        # Merke die zuletzt bemalte Koordinate für die "Malen"-Logik
        last_painted_tile_coords = map_coords

def save_map():
    """Speichert die aktuelle Karte inkl. Original-Tilegrössen in einer JSON-Datei."""
    # Tkinter-Wurzelfenster für Dialog erstellen und verstecken
    root = tk.Tk(); root.withdraw()
    # Dialog zum Speichern anzeigen
    filepath = filedialog.asksaveasfilename(
        title="Karte speichern unter...",
        initialdir=os.path.dirname(__file__) if "__file__" in locals() else ".", # Start im Skript-Ordner
        defaultextension=".json", # Standard-Dateiendung
        filetypes=[("Karten-Dateien", "*.json"), ("Alle Dateien", "*.*")] # Dateifilter
    )
    root.destroy() # Tkinter-Fenster schliessen

    # Wenn kein Pfad ausgewählt wurde (Abbruch), Funktion beenden
    if not filepath:
        print("Speichern abgebrochen.")
        return

    # Ermittle relative Pfade der Tilesets (falls möglich) und deren Originalgrössen
    script_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
    relative_tileset_paths = []
    source_tileset_sizes = [] # Liste für [breite, höhe] Paare
    for ts in loaded_tilesets:
        try:
            # Versuche relativen Pfad zu erstellen
            rel_path = os.path.relpath(ts['path'], script_dir)
            relative_tileset_paths.append(rel_path.replace("\\", "/")) # Slashes vereinheitlichen
        except ValueError:
             # Wenn auf anderem Laufwerk o.ä., speichere den vollen Pfad
             print(f"Warnung: Tileset {ts['path']} ist nicht relativ zum Skript-Ordner. Speichere vollen Pfad.")
             relative_tileset_paths.append(ts['path'].replace("\\", "/")) # Slashes vereinheitlichen

        # Füge die Source-Grösse hinzu (mit Fallback auf Editor-Zielgrösse)
        source_tileset_sizes.append([
            ts.get('source_w', TILE_WIDTH),
            ts.get('source_h', TILE_HEIGHT)
        ])

    # Datenstruktur für die JSON-Datei erstellen
    map_save_data = {
        "tile_width": TILE_WIDTH, # Die Zielgrösse, die der Editor verwendet
        "tile_height": TILE_HEIGHT,
        "map_width_tiles": MAP_WIDTH_TILES, # Aktuelle Kartendimensionen
        "map_height_tiles": MAP_HEIGHT_TILES,
        "tileset_paths": relative_tileset_paths, # Liste der (relativen) Pfade
        "source_tileset_sizes": source_tileset_sizes, # NEU: Liste der Originalgrössen
        "map_tileset_indices": map_tileset_indices, # Layer 1: Welches Tileset?
        "map_tile_indices": map_tile_indices,       # Layer 2: Welches Tile im Tileset?
        "map_collision_data": map_collision_data,   # Layer 3: Kollision?
    }

    # Versuche, die Daten als JSON zu speichern
    try:
        with open(filepath, 'w') as f:
            json.dump(map_save_data, f, indent=4) # `indent=4` für Lesbarkeit
        print(f"Karte erfolgreich gespeichert: {filepath}")
    except Exception as e:
        print(f"Fehler beim Speichern der Karte in '{filepath}': {e}")
        traceback.print_exc()

def load_map():
    """Lädt eine Karte aus einer JSON-Datei und berücksichtigt gespeicherte Original-Tilegrössen."""
    # Globale Variablen, die potenziell geändert werden
    global map_tileset_indices, map_tile_indices, map_collision_data, loaded_tilesets
    global MAP_WIDTH_TILES, MAP_HEIGHT_TILES, TILE_WIDTH, TILE_HEIGHT, screen # Editor-Zielgrösse bleibt konstant
    global MAP_AREA_WIDTH, MAP_AREA_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT

    # Tkinter-Dialog zum Laden öffnen
    root = tk.Tk(); root.withdraw()
    filepath = filedialog.askopenfilename(
        title="Karte laden",
        initialdir=os.path.dirname(__file__) if "__file__" in locals() else ".",
        filetypes=[("Karten-Dateien", "*.json"), ("Alle Dateien", "*.*")]
    )
    root.destroy()

    if not filepath:
        print("Laden abgebrochen.")
        return

    # JSON-Datei einlesen
    try:
        with open(filepath, 'r') as f:
            map_load_data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Lesen der Kartendatei '{filepath}': {e}")
        traceback.print_exc()
        return

    # Versuche, die Daten zu verarbeiten
    try:
        # Ziel-Tilegrösse aus Datei lesen (nur zur Info, Editor behält seine Zielgrösse bei)
        loaded_target_tw = map_load_data.get('tile_width', TILE_WIDTH)
        loaded_target_th = map_load_data.get('tile_height', TILE_HEIGHT)
        if loaded_target_tw != TILE_WIDTH or loaded_target_th != TILE_HEIGHT:
            print(f"Info: Geladene Karte wurde mit Ziel-Tilegrösse {loaded_target_tw}x{loaded_target_th} erstellt. "
                  f"Editor verwendet {TILE_WIDTH}x{TILE_HEIGHT} und skaliert Tiles entsprechend beim Laden.")

        # Map-Dimensionen aus Datei lesen
        new_map_w = map_load_data['map_width_tiles']
        new_map_h = map_load_data['map_height_tiles']

        # Map-Layer-Daten laden
        loaded_map_tileset_indices = map_load_data['map_tileset_indices']
        loaded_map_tile_indices = map_load_data['map_tile_indices']
        loaded_map_collision_data = map_load_data['map_collision_data']

        # Dimensionen der geladenen Layer prüfen
        if len(loaded_map_tile_indices) != new_map_h or \
           any(len(row) != new_map_w for row in loaded_map_tile_indices) or \
           len(loaded_map_tileset_indices) != new_map_h or \
           any(len(row) != new_map_w for row in loaded_map_tileset_indices) or \
           len(loaded_map_collision_data) != new_map_h or \
           any(len(row) != new_map_w for row in loaded_map_collision_data):
            raise ValueError("Dimensionen der geladenen Map-Layer stimmen nicht mit den Header-Infos überein.")

        # Benötigte Tileset-Pfade und deren Original-Grössen laden
        required_paths = map_load_data['tileset_paths']
        # Lade Originalgrössen, mit Fallback für alte Dateien ohne diese Info
        source_tileset_sizes = map_load_data.get('source_tileset_sizes', [])

        # Baue die `loaded_tilesets` Liste neu auf
        temp_loaded_tilesets = []
        script_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
        print("Lade und verarbeite Tilesets für die Karte...")

        for i, rel_path in enumerate(required_paths):
            # Versuche den Pfad zu finden (relativ zum Skript oder absolut)
            abs_path = os.path.normpath(os.path.join(script_dir, rel_path))
            if not os.path.exists(abs_path):
                abs_path = os.path.normpath(rel_path) # Versuch mit dem Pfad wie er ist (absolut?)
                if not os.path.exists(abs_path):
                    print(f"FEHLER: Benötigtes Tileset '{rel_path}' (gesucht als '{abs_path}') nicht gefunden! Ersetze durch Platzhalter.")
                    # Füge einen Platzhalter hinzu, damit Indizes nicht komplett verschoben werden
                    temp_loaded_tilesets.append({'path': rel_path, 'images': [], 'tile_count': 0, 'cols': 0, 'source_w': TILE_WIDTH, 'source_h': TILE_HEIGHT})
                    continue # Nächstes Tileset

            # Ermittle die zu verwendende Original-Grösse aus den geladenen Daten
            source_w, source_h = TILE_WIDTH, TILE_HEIGHT # Fallback-Standard
            if i < len(source_tileset_sizes) and isinstance(source_tileset_sizes[i], list) and len(source_tileset_sizes[i]) == 2:
                source_w, source_h = source_tileset_sizes[i]
            else:
                 # Keine (gültige) Grösse in Datei gefunden -> Fallback oder Raten
                 print(f"Warnung: Keine gültige Originalgrösse für Tileset #{i} ('{os.path.basename(abs_path)}') in Kartendatei gefunden. "
                       f"Verwende Fallback ({source_w}x{source_h}) zum Extrahieren.")
                 # Optional: Hier könnte man erneut versuchen, die Grösse zu erraten/abzufragen

            # Lade das Tileset mit korrekter Source-Grösse und skaliere auf Editor-Target-Grösse
            images, count, cols = load_tileset_images(abs_path, source_w, source_h, TILE_WIDTH, TILE_HEIGHT)

            # Füge das Ergebnis zur temporären Liste hinzu
            if images:
                 temp_loaded_tilesets.append({
                    'path': abs_path, 'images': images, 'tile_count': count, 'cols': cols,
                    'source_w': source_w, 'source_h': source_h
                 })
            else:
                 # Fehler beim Laden, füge Platzhalter hinzu
                 print(f"Fehler beim Laden von Tileset '{os.path.basename(abs_path)}'. Ersetze durch Platzhalter.")
                 temp_loaded_tilesets.append({'path': abs_path, 'images': [], 'tile_count': 0, 'cols': 0, 'source_w': source_w, 'source_h': source_h})

        # --- Nach dem Laden aller Tilesets: Wende die Änderungen an ---
        loaded_tilesets = temp_loaded_tilesets # Überschreibe die globale Liste
        rebuild_palette_data() # Baue die Palette neu auf

        # Initialisiere Map-Daten mit neuen Dimensionen (setzt globale Grössenvariablen)
        initialize_map_data(new_map_w, new_map_h)
        # Überschreibe die gerade initialisierten leeren Daten mit den geladenen Daten
        map_tileset_indices = loaded_map_tileset_indices
        map_tile_indices = loaded_map_tile_indices
        map_collision_data = loaded_map_collision_data

        # Berechne neue Fenster-/Bereichsgrössen basierend auf geladener Map
        MAP_AREA_WIDTH = MAP_WIDTH_TILES * TILE_WIDTH
        MAP_AREA_HEIGHT = MAP_HEIGHT_TILES * TILE_HEIGHT
        SCREEN_WIDTH = MAP_AREA_WIDTH + PALETTE_AREA_WIDTH
        # Höhe nur anpassen, wenn sie die minimale Palettenhöhe unterschreitet? Vorerst Map-Höhe.
        SCREEN_HEIGHT = MAP_AREA_HEIGHT
        # Erstelle das Pygame-Fenster neu mit den potenziell geänderten Dimensionen
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"Map Editor - {os.path.basename(filepath)}") # Update Fenstertitel

        print(f"Karte erfolgreich geladen und Editor angepasst: {filepath}")

    except Exception as e:
        # Fange alle anderen möglichen Fehler ab (z.B. KeyError, ValueError)
        print(f"Unerwarteter Fehler beim Verarbeiten der geladenen Kartendaten: {e}")
        traceback.print_exc()
        # Setze Editor auf einen sicheren, leeren Zustand zurück
        print("Setze Editor auf leeren Standardzustand zurück.")
        initialize_map_data() # Standardgrösse
        # Alte Tilesets entfernen? Oder behalten? Hier: Entfernen.
        loaded_tilesets = []
        rebuild_palette_data()
        # Fenster auch zurücksetzen
        MAP_AREA_WIDTH = MAP_WIDTH_TILES * TILE_WIDTH
        MAP_AREA_HEIGHT = MAP_HEIGHT_TILES * TILE_HEIGHT
        SCREEN_WIDTH = MAP_AREA_WIDTH + PALETTE_AREA_WIDTH
        SCREEN_HEIGHT = MAP_AREA_HEIGHT
        try:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption(f"Map Editor - Fehler beim Laden")
        except pygame.error as display_error:
             print(f"Konnte Pygame-Display nach Ladefehler nicht zurücksetzen: {display_error}")

# --- Zeichenfunktionen ---

def draw_grid(surface, start_x, start_y, width, height, tile_w, tile_h, color):
    """Zeichnet ein Gitter auf die Surface."""
    for x in range(start_x, start_x + width + 1, tile_w):
        pygame.draw.line(surface, color, (x, start_y), (x, start_y + height))
    for y in range(start_y, start_y + height + 1, tile_h):
        pygame.draw.line(surface, color, (start_x, y), (start_x + width, y))

def draw_map_area(surface):
    """Zeichnet den Kartenbereich mit Tiles und Kollisions-Overlay."""
    map_rect = pygame.Rect(0, 0, MAP_AREA_WIDTH, MAP_AREA_HEIGHT)
    surface.fill(BLACK, map_rect) # Hintergrund des Kartenbereichs

    # Gehe durch jede Zelle der Karte
    for r in range(MAP_HEIGHT_TILES):
        for c in range(MAP_WIDTH_TILES):
            # Hole Indizes für diese Zelle
            ts_idx = map_tileset_indices[r][c]
            tile_idx = map_tile_indices[r][c]

            # Prüfe, ob gültige Indizes vorhanden sind
            if ts_idx != -1 and tile_idx != -1 and ts_idx < len(loaded_tilesets):
                tileset = loaded_tilesets[ts_idx]
                # Prüfe, ob das Tileset Bilder hat und der Index gültig ist
                if isinstance(tileset.get('images'), list) and tile_idx < len(tileset['images']):
                    img = tileset['images'][tile_idx] # Hole das (skalierte) Tile-Bild
                    # Berechne Zielposition auf dem Bildschirm
                    dest_x = c * TILE_WIDTH
                    dest_y = r * TILE_HEIGHT
                    # Zeichne das Bild
                    surface.blit(img, (dest_x, dest_y))
                # else: print(f"Debug: Ungültiger Tile-Index {tile_idx} für Tileset {ts_idx} bei ({r},{c})")

            # Zeichne Kollisions-Overlay, falls Kollision aktiv ist
            if map_collision_data[r][c]:
                 # Erstelle eine halbtransparente rote Fläche
                 collision_surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA) # SRCALPHA für Transparenz
                 collision_surface.fill(TRANSPARENT_RED)
                 # Berechne Zielposition
                 dest_x = c * TILE_WIDTH
                 dest_y = r * TILE_HEIGHT
                 # Zeichne die transparente Fläche über das Tile
                 surface.blit(collision_surface, (dest_x, dest_y))

    # Zeichne das Gitter über die Karte
    draw_grid(surface, 0, 0, MAP_AREA_WIDTH, MAP_AREA_HEIGHT, TILE_WIDTH, TILE_HEIGHT, GRAY)

def draw_palette_area(surface):
    """Zeichnet den Palettenbereich mit den verfügbaren Tiles."""
    palette_rect = pygame.Rect(MAP_AREA_WIDTH, 0, PALETTE_AREA_WIDTH, SCREEN_HEIGHT)
    surface.fill(LIGHT_GRAY, palette_rect) # Hintergrund der Palette

    # Berechne, wie viele Spalten die Palette hat
    num_cols = PALETTE_WIDTH_TILES
    # Gehe durch alle verfügbaren (skalierten) Tile-Bilder
    for flat_idx, img in enumerate(all_tile_images_flat):
        # Berechne Zeile und Spalte in der Palette
        col = flat_idx % num_cols
        row = flat_idx // num_cols

        # Berechne die Bildschirmkoordinaten für dieses Paletten-Tile
        dest_x = MAP_AREA_WIDTH + col * TILE_WIDTH
        dest_y = row * TILE_HEIGHT

        # Nur zeichnen, wenn das Tile noch in den sichtbaren Bereich der Palette passt
        if dest_y + TILE_HEIGHT <= SCREEN_HEIGHT:
            surface.blit(img, (dest_x, dest_y))

            # Wenn dieses Tile aktuell ausgewählt ist, zeichne einen roten Rahmen
            if flat_idx == current_flat_palette_index:
                pygame.draw.rect(surface, RED, (dest_x, dest_y, TILE_WIDTH, TILE_HEIGHT), 3) # Rahmenstärke 3
        else:
            # Wenn Tiles nicht mehr passen, höre auf zu zeichnen (kein Scrolling implementiert)
            break

    # Zeichne ein Gitter über die Palette zur besseren Übersicht
    draw_grid(surface, MAP_AREA_WIDTH, 0, PALETTE_AREA_WIDTH, SCREEN_HEIGHT, TILE_WIDTH, TILE_HEIGHT, GRAY)

def draw_ui_info(surface):
     """Zeichnet UI-Texte und Informationen (Modus, Auswahl, Anleitung)."""
     y_offset = 10 # Startposition für den Text (vertikal)
     x_pos = MAP_AREA_WIDTH + 10 # Startposition horizontal (im Palettenbereich)

     # Zeige aktuellen Modus an
     mode_text = f"Modus: {'Tiles malen' if edit_mode == 'tile' else 'Kollision setzen'} (C)"
     mode_surf = font_medium.render(mode_text, True, BLACK) # Schwarzer Text auf hellem Grund
     surface.blit(mode_surf, (x_pos, y_offset))
     y_offset += 30 # Nächste Zeile

     # Zeige aktuell ausgewähltes Tile an
     sel_text = "Ausgewählt: Nichts"
     # Prüfe, ob ein gültiger Index ausgewählt ist
     if current_flat_palette_index != -1 and current_flat_palette_index < len(all_tile_mapping):
          ts_idx, t_idx = all_tile_mapping[current_flat_palette_index]
          # Prüfe, ob der Tileset-Index noch gültig ist
          if ts_idx < len(loaded_tilesets):
            # Hole den Dateinamen des Tilesets
            ts_name = os.path.basename(loaded_tilesets[ts_idx].get('path', 'Unbekannt'))
            sel_text = f"Ausgew.: {ts_name} ({t_idx})"
          else:
            # Sollte nicht passieren, aber als Absicherung
            sel_text = "Ausgew.: Fehler (TS Index ungültig)!"
     elif current_flat_palette_index != -1:
         # Index ausgewählt, aber Mapping-Problem?
         sel_text = "Ausgew.: Fehler (Mapping ungültig)!"

     sel_surf = font_medium.render(sel_text, True, BLACK)
     surface.blit(sel_surf, (x_pos, y_offset))
     y_offset += 30 # Nächste Zeile

     # Zeige Kurzanleitung an
     instructions = [
         "L-Klick: Malen/Aktion",
         "R-Klick: Löschen/Entfernen",
         "C: Modus wechseln",
         "STRG+S: Speichern",
         "STRG+L: Laden",
         "ESC: Beenden"
     ]
     for line in instructions:
         line_surf = font_small.render(line, True, BLACK)
         surface.blit(line_surf, (x_pos, y_offset))
         y_offset += 20 # Nächste Zeile

# --- Hauptfunktion ---

def main():
    # Globale Variablen deklarieren, die in main() verwendet oder geändert werden
    global screen, clock, font_small, font_medium, loaded_tilesets, edit_mode
    global is_mouse_down_left, is_mouse_down_right, last_painted_tile_coords
    global current_flat_palette_index, current_tileset_index, current_tile_index_in_tileset
    # Globale Grössenvariablen, die von load_map geändert werden können
    global MAP_WIDTH_TILES, MAP_HEIGHT_TILES, TILE_WIDTH, TILE_HEIGHT
    global MAP_AREA_WIDTH, MAP_AREA_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT

    # 1. Pygame initialisieren (wichtig *vor* Bildoperationen)
    pygame.init()
    # Auch das Font-Modul explizit initialisieren
    pygame.font.init()

    # 2. Fonts erstellen (nach pygame.font.init())
    try:
        font_small = pygame.font.SysFont(None, 24)
        font_medium = pygame.font.SysFont(None, 30)
    except Exception as e:
        print(f"Fehler beim Initialisieren der Schriftarten: {e}")
        # Fallback auf Standardfont, falls SysFont nicht geht
        font_small = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 30)


    # 3. Tilesets auswählen und laden (fragt ggf. nach Grössen)
    if not select_tilesets_and_load():
         print("Keine Tilesets geladen. Editor wird beendet.")
         pygame.quit() # Pygame sauber beenden
         sys.exit()   # Skript beenden

    # 4. Pygame-Fenster erstellen (Grösse basiert jetzt auf initialen Konstanten)
    #    Die Grösse wird ggf. in load_map() angepasst.
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Map Editor")
        clock = pygame.time.Clock()
    except pygame.error as e:
        print(f"Fehler beim Erstellen des Pygame-Fensters: {e}")
        pygame.quit()
        sys.exit()

    # 5. Initialisiere die Map-Daten mit der Standardgrösse
    initialize_map_data()

    # 6. Haupt-Schleife des Editors
    running = True
    while running:
        # --- Event-Verarbeitung ---
        mouse_pos = pygame.mouse.get_pos()
        # Klick-Status pro Frame zurücksetzen (wird nur bei MOUSEBUTTONDOWN gesetzt)
        left_click_this_frame = False
        right_click_this_frame = False

        for event in pygame.event.get():
            # Fenster schliessen
            if event.type == pygame.QUIT:
                running = False

            # Tastatureingaben
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: # ESC -> Beenden
                    running = False
                elif event.key == pygame.K_c: # C -> Modus wechseln
                    edit_mode = 'collision' if edit_mode == 'tile' else 'tile'
                    print(f"Wechsle zu Modus: {edit_mode}")
                # STRG + S -> Speichern
                elif event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META): # META für MacOS Command
                     save_map()
                # STRG + L -> Laden
                elif event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META): # META für MacOS Command
                     load_map() # Diese Funktion passt ggf. globale Variablen wie screen, Map-Grösse etc. an

            # Mausklicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Linksklick
                    is_mouse_down_left = True   # Merken, dass Taste gedrückt ist
                    left_click_this_frame = True # Merken für diesen Frame
                    # Prüfe, ob Klick in der Palette war
                    clicked_palette_idx = get_palette_tile_from_pos(mouse_pos[0], mouse_pos[1])
                    if clicked_palette_idx != -1:
                         # Klick war in Palette -> Tile auswählen
                         current_flat_palette_index = clicked_palette_idx
                         # Mapping von flachem Index zu Tileset/Tile-im-Tileset holen
                         if current_flat_palette_index < len(all_tile_mapping):
                            current_tileset_index, current_tile_index_in_tileset = all_tile_mapping[current_flat_palette_index]
                         else:
                            # Sollte nicht passieren, wenn Palette korrekt aufgebaut wurde
                            print(f"Fehler: Ungültiger Palettenindex {current_flat_palette_index} nach Klick.")
                            current_flat_palette_index = -1; current_tileset_index = -1; current_tile_index_in_tileset = -1
                    else:
                         # Klick war nicht in Palette -> Aktion auf Karte ausführen
                         handle_map_interaction(mouse_pos, True, False)

                elif event.button == 3: # Rechtsklick
                    is_mouse_down_right = True  # Merken, dass Taste gedrückt ist
                    right_click_this_frame = True # Merken für diesen Frame
                    # Aktion auf Karte ausführen (Löschen / Kollision entfernen)
                    handle_map_interaction(mouse_pos, False, True)

            # Maustaste losgelassen
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: # Linke Taste
                    is_mouse_down_left = False
                    last_painted_tile_coords = None # Mal-Status zurücksetzen
                elif event.button == 3: # Rechte Taste
                    is_mouse_down_right = False
                    last_painted_tile_coords = None # Mal-Status zurücksetzen

            # Mausbewegung
            if event.type == pygame.MOUSEMOTION:
                 # Wenn eine Maustaste gehalten wird -> "Malen"-Aktion ausführen
                 if is_mouse_down_left:
                      handle_map_interaction(mouse_pos, True, False)
                 elif is_mouse_down_right:
                      handle_map_interaction(mouse_pos, False, True)

        # --- Spiellogik Update ---
        # (Hier nicht relevant, da Editor)

        # --- Zeichnen (Rendern) ---
        if screen: # Nur zeichnen, wenn Screen korrekt initialisiert wurde
            screen.fill(BLACK) # Gesamten Hintergrund löschen

            # Einzelne Bereiche zeichnen
            draw_map_area(screen)       # Kartenkacheln + Kollision + Gitter
            draw_palette_area(screen)   # Tileset-Kacheln + Auswahl + Gitter
            draw_ui_info(screen)        # Text-Infos (Modus, Auswahl, Hilfe)

            # Alles auf dem Bildschirm anzeigen
            pygame.display.flip()
        else:
             # Fange den Fall ab, dass screen None ist (z.B. nach Ladefehler)
             print("Warte auf Screen-Initialisierung oder Fehler...")
             pygame.time.wait(100) # Kurze Pause, um CPU zu schonen


        # --- Framerate begrenzen ---
        if clock:
            clock.tick(FPS)

    # --- Spiel beenden ---
    pygame.quit()
    sys.exit()

# --- Skript starten ---
if __name__ == "__main__":
    # Führe die Hauptfunktion aus
    main()