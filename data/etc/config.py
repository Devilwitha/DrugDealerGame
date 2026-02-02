# data/etc/config.py
# Stand: 2025-04-15 (Neu erstellt für Refactoring)
# Formatiert für maximale Lesbarkeit

import pygame # Nur für pygame.Color benötigt, kann entfernt werden, wenn Farben als Tupel reichen
import os # <-- HINZUGEFÜGT für os.path.join


# ========= FARBEN (RGB-Tupel) =========
# Es ist üblich, Farbkonstanten in einer Konfigurationsdatei zu haben.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 255) # Oft für Debugging/Fehleranzeige
GREY = (100, 100, 100)
LIGHT_GREY = (180, 180, 180)
DARK_BLUE = (0, 0, 100)
YELLOW = (255, 255, 0)

# Alternativ mit pygame.Color (benötigt pygame Import):
# WHITE = pygame.Color('white')
# BLACK = pygame.Color('black')
# ... etc.


# ========= SPIELWELT & PHYSIK =========
TILE_SIZE = 32  # Grundgröße für Gitter etc.
FPS = 60        # Ziel-Bildrate
INTERACTION_RADIUS = TILE_SIZE * 1.5  # Radius um Spieler für Interaktion
LONG_PRESS_THRESHOLD = 1.0         # Sekunden für langes Drücken (Aufheben)


# ========= GAMEPLAY =========
WEED_SELL_PRICE = 15.0 # Verkaufspreis pro Einheit Weed
PACKED_WEED_SELL_PRICE = 25.0 # Verkaufspreis pro Einheit VerpacktesWeed (höher als normales Weed)


# ========= UI LAYOUT (Basiswerte & Standard-Konfiguration) =========
# --- Fonts ---
# Referenzhöhe für Font-Skalierung (wird in game.py/setup.py verwendet)
FONT_SIZE_REF_H = 600.0
# Basis-Schriftgrößen (werden zur Laufzeit basierend auf Bildschirmhöhe skaliert)
BASE_UI_FONT_SIZE = 28
BASE_BUTTON_FONT_SIZE = 18
BASE_INV_QTY_FONT_SIZE = 16 # Wird jetzt in inventory.py verwendet? Ggf. dorthin verschieben?
BASE_DIALOG_FONT_SIZE = 24
BASE_SHOP_FONT_SIZE = 18

# --- Android Interaktionsbutton ---
BUTTON_DEFAULT_WIDTH_PERCENT = 0.08  # Breite als % der Bildschirmbreite
BUTTON_DEFAULT_HEIGHT_PERCENT = 0.13 # Höhe als % der Bildschirmhöhe
BUTTON_PADDING = 15                 # Abstand des Buttons von Rändern/anderen Elementen
BUTTON_X = BUTTON_PADDING           # Standard X-Position des Buttons (linker Rand)
BUTTON_COLOR_NORMAL = (80, 80, 80)  # Fallback-Farbe, wenn kein Bild geladen
BUTTON_BORDER_COLOR = WHITE         # Randfarbe für Fallback-Button


# ========= SPIELZUSTÄNDE =========
# Konstanten für verschiedene UI- oder Spielmodi
GAME_STATE_PLAY = "play"
GAME_STATE_DIALOG = "dialog"
GAME_STATE_SHOP = "shop"
GAME_STATE_SELL = "sell"
# Evtl. weitere hinzufügen: GAME_STATE_MENU, GAME_STATE_MINIGAME, etc.


# ========= DATEI- & ORDNERNAMEN (Relativ zum Projekt- oder Datenverzeichnis) =========
# --- Verzeichnisnamen (relativ zum Projekt-Root) ---
# Diese werden im Hauptskript mit os.path.join(PROJECT_ROOT, ...) verwendet
DATA_DIR_NAME = "data"
IMAGE_DIR_NAME = os.path.join(DATA_DIR_NAME, "bilder") # Beispiel: data/bilder
SOUND_DIR_NAME = os.path.join(DATA_DIR_NAME, "sounds") # Beispiel: data/sounds
SAVE_DATA_DIR_NAME = os.path.join(DATA_DIR_NAME, "savedata") # Beispiel: data/savedata
SETTINGS_DIR_NAME = os.path.join(DATA_DIR_NAME, "settings") # Beispiel: data/settings
LOG_DIR_NAME = os.path.join(DATA_DIR_NAME, "logs")       # Beispiel: data/logs
MINIGAME_DIR_NAME = os.path.join(DATA_DIR_NAME, "miniGame") # Beispiel: data/miniGame
GROWING_SUBDIR_NAME = "Growing" # Relativ zu MINIGAME_DIR_NAME
ZIPWEED_SUBDIR_NAME = "zipWeed" # Relativ zu MINIGAME_DIR_NAME

# --- Dateinamen (nur der Name, ohne Pfad) ---
# Haupt-Assets
BACKGROUND_FILENAME = "background.png"
BUTTON_FILENAME = "interact_button.png" # Bild für Android-Button
# Icons (MONEY_ICON_FILENAME ist in inventory.py)
GRIPS_ICON_FILENAME = "grips_icon.png"
PACKED_WEED_ICON_FILENAME = "packed_weed_icon.png"
# Sounds
NO_RESOURCE_SOUND_FILENAME = "error.wav" # Sound für fehlende Ressourcen

# Konfigurations- & Speicherdateien
SETTINGS_FILENAME = "settings.json"
INVENTORY_SAVE_FILENAME = "inventar.json"
PLAYER_POS_SAVE_FILENAME = "player_position.json"
PLACED_ITEMS_SAVE_FILENAME = "placed_items.json"

# Minispiel-Skripte (nur Dateinamen)
MINIGAME1_FILENAME = "plant_grow1.py" # Erde füllen
MINIGAME2_FILENAME = "grow_plant2.py" # Samen/Gießen
MINIGAME3_FILENAME = "earn_buds.py" # Ernten
MINIGAME_ZIPWEED_FILENAME = "zipWeed.py" # Verpacken

# Hauptskript (relativ zum Projekt-Root) - nützlich für Neustart
MAIN_SCRIPT_NAME = "main.py"

# ========= LOGGING (Basiskonfiguration) =========
# Könnte auch direkt in game.py bleiben, aber hier als Option
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"
# Standard-Level für Entwicklung, kann zur Laufzeit angepasst werden
DEFAULT_LOG_LEVEL = LOG_LEVEL_DEBUG
DATE_FMT = '%Y-%m-%d %H:%M:%S'

# ========= SONSTIGES =========
# Hier könnten weitere globale Einstellungen platziert werden,
# z.B. Standard-Sprache, Debug-Flags etc.
DEBUG_MODE = False # Beispiel für ein Debug-Flag