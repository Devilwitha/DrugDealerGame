# data/etc/items.py
# Stand: 2025-04-15 (Refaktorierte Version)
# Formatiert für maximale Lesbarkeit

import pygame
import logging
import time
import os
import sys
import subprocess # Für Minispiel-Start

# Logging für dieses Modul
logger = logging.getLogger(__name__)

# ========= KONSTANTEN (aus game.py hierher verschoben) =========
# Standard-Wachstumszeit für Pflanzen (kann pro Item überschrieben werden)
DEFAULT_GROW_TIME_SECONDS = 10
# Größe, mit der platzierte Items in der Welt dargestellt werden
PLACED_ITEM_SIZE = 32

# Pfade zu den Minispielen (relative Pfade vom Projekt-Root)
# WICHTIG: Diese Pfade müssen korrekt sein!
try:
    # Direkter Pfad, wenn __file__ bekannt ist
    script_dir_items = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback, falls __file__ nicht verfügbar (z.B. interaktive Konsole)
    script_dir_items = os.path.abspath(".")

# Annahme: items.py liegt in data/etc/, Projekt-Root ist 2 Ebenen höher
project_root_dir_items = os.path.abspath(os.path.join(script_dir_items, "..", ".."))

# Minispiel Pfade (als absolute Pfade konstruieren)
MINIGAME_FOLDER_GROWING = os.path.join(project_root_dir_items, "data", "miniGame", "Growing")
MINIGAME_FOLDER_ZIPWEED = os.path.join(project_root_dir_items, "data", "miniGame", "zipWeed")

MINIGAME_GROW1_PATH = os.path.join(MINIGAME_FOLDER_GROWING, "plant_grow1.py")     # Erde füllen
MINIGAME_GROW2_PATH = os.path.join(MINIGAME_FOLDER_GROWING, "grow_plant2.py")     # Samen/Gießen
MINIGAME_EARN_WEED_PATH = os.path.join(MINIGAME_FOLDER_GROWING, "earn_buds.py")   # Ernten
ZIPWEED_SCRIPT_PATH = os.path.join(MINIGAME_FOLDER_ZIPWEED, "zipWeed.py")        # Verpacken

# --- Verwendete Item-Namen (als Konstanten definieren für Typsicherheit) ---
ITEM_BLUMENTOPF = "Blumentopf"
ITEM_SACK_ERDE = "Sack Erde"
ITEM_WEED_SEEDS = "Weed Seeds"
ITEM_VERPACKSTATION = "Verpackstation"
ITEM_WEED = "Weed"
ITEM_GRIPS = "Grips"
ITEM_VERPACKTES_WEED = "VerpacktesWeed"

# Liste der Items, die platziert werden können (wird von game.py zum Starten des Drag&Drop genutzt)
PLACEABLE_ITEMS = [ITEM_BLUMENTOPF, ITEM_VERPACKSTATION]

# Zustände für den Blumentopf
STATE_OHNE_ERDE = 'ohneErde'
STATE_OHNE_SEED = 'ohneSeed'
STATE_GIESSEN = 'giessen'       # Zustand nach dem Pflanzen, bereit zum Gießen/Wachstum starten
STATE_GROWING = 'growing'
STATE_READY_TO_EARN = 'readyToEarn'

# Zustände für die Verpackstation (falls benötigt, aktuell 'default')
STATE_DEFAULT = 'default'


# ========= PLACED ITEM KLASSE =========
class PlacedItem(pygame.sprite.Sprite):
    """Repräsentiert ein in der Spielwelt platziertes Item."""

    def __init__(self, x, y, item_type, images_dict, fallback_image,
                 grow_time=0, initial_state=None, timer_end=None):
        """
        Initialisiert ein platziertes Item.

        Args:
            x (int): Welt-X-Koordinate (Mittelpunkt).
            y (int): Welt-Y-Koordinate (Mittelpunkt).
            item_type (str): Der Typ des Items (z.B. "Blumentopf").
            images_dict (dict): Dictionary mit Bildern für verschiedene Zustände
                                {state_name: pygame.Surface}.
            fallback_image (pygame.Surface | None): Bild, das verwendet wird, wenn
                                                 kein passendes Zustandsbild gefunden wird.
            grow_time (int): Zeit in Sekunden für Wachstum (relevant für Blumentopf).
            initial_state (str | None): Der Startzustand des Items. Wenn None,
                                       wird ein Standardzustand basierend auf item_type gewählt.
            timer_end (float | None): Timestamp, wann ein laufender Timer endet (z.B. Wachstum).
                                    Wird aus Speicherstand geladen.
        """
        super().__init__()
        self.item_type = item_type
        self.images = images_dict if isinstance(images_dict, dict) else {}
        self.fallback_image = fallback_image
        self.grow_time_seconds = grow_time if grow_time > 0 else (DEFAULT_GROW_TIME_SECONDS if item_type == ITEM_BLUMENTOPF else 0)

        # Zustand festlegen
        if initial_state:
            self.state = initial_state
        elif item_type == ITEM_BLUMENTOPF:
            self.state = STATE_OHNE_ERDE
        elif item_type == ITEM_VERPACKSTATION:
             self.state = STATE_DEFAULT
        else:
            self.state = STATE_DEFAULT # Fallback
            logger.warning(f"Kein expliziter Startzustand für Item-Typ '{item_type}' definiert. Nutze '{self.state}'.")

        self.timer_end_timestamp = timer_end # Wird aus Speicherstand geladen
        self.is_timer_active = self.timer_end_timestamp is not None and self.timer_end_timestamp > time.time()

        # Bild und Rect initialisieren
        self.image = None # Wird in update_appearance gesetzt
        self.rect = None  # Wird in update_appearance gesetzt
        self.update_appearance() # Setzt das initiale Bild basierend auf dem Zustand

        if not self.image:
             logger.error(f"Konnte kein initiales Bild für Item '{self.item_type}' (Zustand: {self.state}) finden!")
             # Fallback: Erzeuge ein kleines farbiges Rechteck, um Fehler anzuzeigen
             self.image = pygame.Surface((PLACED_ITEM_SIZE // 2, PLACED_ITEM_SIZE // 2))
             self.image.fill((255, 0, 255)) # Magenta als Fehlerfarbe

        # self.rect muss nach dem Setzen von self.image gesetzt werden
        if self.image:
            self.rect = self.image.get_rect(center=(x, y))
        else:
             # Sollte nicht passieren, aber als Sicherheit
            self.rect = pygame.Rect(x - PLACED_ITEM_SIZE//4, y - PLACED_ITEM_SIZE//4, PLACED_ITEM_SIZE//2, PLACED_ITEM_SIZE//2)
            logger.error(f"Konnte kein Rect für Item '{self.item_type}' erstellen, da kein Bild vorhanden war.")

        logger.debug(f"PlacedItem erstellt: Typ='{self.item_type}', Pos={self.rect.center if self.rect else (x,y)}, "
                     f"Zustand='{self.state}', GrowTime={self.grow_time_seconds}s, "
                     f"TimerEnd={self.timer_end_timestamp}, TimerActive={self.is_timer_active}")

    def update_appearance(self):
        """Aktualisiert das Bild des Items basierend auf dem aktuellen Zustand."""
        original_center = self.rect.center if self.rect else None # Position speichern
        self.image = self.images.get(self.state) # Versuche Bild für aktuellen Zustand zu holen

        if not self.image:
            self.image = self.fallback_image # Nutze Fallback-Bild, falls Zustand unbekannt
            logger.warning(f"Kein spezifisches Bild für Zustand '{self.state}' von Item '{self.item_type}' gefunden. Nutze Fallback.")

        # Stelle sicher, dass das Bild die korrekte Größe hat
        if self.image and self.image.get_size() != (PLACED_ITEM_SIZE, PLACED_ITEM_SIZE):
            try:
                self.image = pygame.transform.smoothscale(self.image, (PLACED_ITEM_SIZE, PLACED_ITEM_SIZE))
            except Exception as e_scale:
                logger.error(f"Fehler beim Skalieren des Zustandsbildes '{self.state}' für '{self.item_type}': {e_scale}")
                # Behalte unskaliertes Bild oder nutze Fallback erneut? Hier behalten wir es erstmal.
                if not self.image: self.image = self.fallback_image # Erneuter Fallback-Versuch

        # Rect neu setzen, falls sich Bild geändert hat oder noch nicht existierte
        if self.image:
             # Nur Rect neu erstellen, wenn nötig (Bild anders oder Rect fehlt)
            if not self.rect or self.rect.size != self.image.get_size():
                if original_center:
                    self.rect = self.image.get_rect(center=original_center)
                else:
                    # Sollte nicht passieren, wenn Initialisierung korrekt war
                    self.rect = self.image.get_rect()
                    logger.error(f"Rect für '{self.item_type}' musste ohne Center-Info neu erstellt werden.")
        elif self.fallback_image:
             # Fallback, wenn auch das Zustandsbild nicht geladen werden konnte
             self.image = self.fallback_image
             if self.image: # Prüfen ob Fallback Bild existiert
                 if not self.rect or self.rect.size != self.image.get_size():
                    if original_center:
                        self.rect = self.image.get_rect(center=original_center)
                    else:
                        self.rect = self.image.get_rect()


    def update(self, dt):
        """
        Wird in jedem Frame aufgerufen. Prüft z.B. abgelaufene Timer.

        Args:
            dt (float): Delta Time - Zeit seit dem letzten Frame in Sekunden.
        """
        if self.is_timer_active and self.timer_end_timestamp:
            current_time = time.time()
            if current_time >= self.timer_end_timestamp:
                self.is_timer_active = False
                self.timer_end_timestamp = None
                # Zustandswechsel, wenn Timer abgelaufen ist (z.B. Wachstum abgeschlossen)
                if self.state == STATE_GROWING and self.item_type == ITEM_BLUMENTOPF:
                    self.state = STATE_READY_TO_EARN
                    self.update_appearance()
                    logger.info(f"Blumentopf ({self.rect.center}) ist fertig gewachsen -> Zustand: {self.state}")
                else:
                     logger.warning(f"Timer für Item '{self.item_type}' (Zustand: {self.state}) abgelaufen, aber keine Zustandsänderung definiert.")

    def _run_minigame(self, script_path):
        """Führt ein externes Python-Skript als Minispiel aus und gibt Erfolg zurück."""
        logger.info(f"Starte externes Minispiel: {script_path}")
        # WICHTIG: Spielstand vorher in game.py speichern!
        success = False
        stdout_msg = ""
        stderr_msg = ""
        try:
            # Stelle sicher, dass das Arbeitsverzeichnis das Projekt-Root ist
            # Damit relative Pfade innerhalb des Minispiels funktionieren
            result = subprocess.run(
                [sys.executable, script_path], # Führe das Skript mit dem aktuellen Python-Interpreter aus
                capture_output=True, text=True, check=False, # Gib keinen Fehler bei Return Code != 0
                encoding='utf-8', errors='ignore', # Versuche, Output zu dekodieren
                cwd=project_root_dir_items # Arbeitsverzeichnis setzen!
            )
            success = (result.returncode == 0)
            stdout_msg = result.stdout.strip() if result.stdout else ""
            stderr_msg = result.stderr.strip() if result.stderr else ""
            logger.info(f"Minispiel '{os.path.basename(script_path)}' beendet. RC={result.returncode}. Success={success}")
            if not success:
                logger.warning(f"Minispiel Output: STDOUT='{stdout_msg}' STDERR:'{stderr_msg}'")
            else:
                 # Bei Erfolg kann der STDOUT relevant sein (z.B. Ernte-Menge)
                 logger.debug(f"Minispiel STDOUT: '{stdout_msg}'")

        except FileNotFoundError:
             logger.error(f"Minispiel-Skript nicht gefunden: '{script_path}'")
             success = False
        except Exception as e:
            logger.exception(f"Fehler bei der Ausführung von Minispiel '{script_path}':")
            success = False
        return success, stdout_msg # Gebe auch STDOUT zurück für Ernte etc.

    def interact(self, inventory, play_sound_func):
        """
        Verarbeitet eine kurze Interaktion mit diesem Item.
        Ändert den Zustand, startet Minispiele, verbraucht/gibt Items.

        Args:
            inventory (Inventory): Das Spieler-Inventar zum Prüfen/Ändern von Items.
            play_sound_func (callable): Eine Funktion, die einen Soundnamen (str)
                                        als Argument nimmt und den Sound abspielt
                                        (z.B. für "error.wav").
        Returns:
            bool: True, wenn die Interaktion erfolgreich war und eine Zustandsänderung
                  oder eine Aktion (wie Minispielstart) ausgelöst hat, sonst False.
            dict: Ein optionales Dictionary mit Ergebnissen (z.B. {'earned_weed': 5})
                  oder None.
        """
        action_taken = False
        result_data = None

        if self.item_type == ITEM_BLUMENTOPF:
            logger.debug(f"Interaktion mit Blumentopf im Zustand: {self.state}")

            if self.state == STATE_OHNE_ERDE:
                if inventory.has_item(ITEM_SACK_ERDE, 1):
                    if inventory.remove_item(ITEM_SACK_ERDE, 1):
                        success, _ = self._run_minigame(MINIGAME_GROW1_PATH)
                        if success:
                            self.state = STATE_OHNE_SEED
                            self.update_appearance()
                            logger.info(f"Blumentopf ({self.rect.center}): Erde hinzugefügt -> Zustand: {self.state}")
                            action_taken = True
                        else:
                            inventory.add_item(ITEM_SACK_ERDE, 1) # Item zurückgeben
                            logger.info(f"Blumentopf ({self.rect.center}): Minispiel (Erde) fehlgeschlagen. Item zurückgegeben.")
                            play_sound_func("error") # Oder spezifischer Sound
                    else:
                        logger.error("Konnte Sack Erde nicht entfernen, obwohl has_item True war?")
                        play_sound_func("error")
                else:
                    logger.info(f"Blumentopf ({self.rect.center}): Interaktion fehlgeschlagen - Kein Sack Erde.")
                    play_sound_func("error") # Standard "geht nicht" Sound

            elif self.state == STATE_OHNE_SEED:
                if inventory.has_item(ITEM_WEED_SEEDS, 1):
                    if inventory.remove_item(ITEM_WEED_SEEDS, 1):
                        success, _ = self._run_minigame(MINIGAME_GROW2_PATH)
                        if success:
                            self.state = STATE_GIESSEN # Zustand nach erfolgreichem Pflanzen
                            self.update_appearance()
                            logger.info(f"Blumentopf ({self.rect.center}): Samen gepflanzt -> Zustand: {self.state}")
                            action_taken = True
                        else:
                            inventory.add_item(ITEM_WEED_SEEDS, 1) # Item zurückgeben
                            logger.info(f"Blumentopf ({self.rect.center}): Minispiel (Samen) fehlgeschlagen. Item zurückgegeben.")
                            play_sound_func("error")
                    else:
                        logger.error("Konnte Weed Seeds nicht entfernen, obwohl has_item True war?")
                        play_sound_func("error")
                else:
                    logger.info(f"Blumentopf ({self.rect.center}): Interaktion fehlgeschlagen - Keine Weed Seeds.")
                    play_sound_func("error")

            elif self.state == STATE_GIESSEN:
                # Starte den Wachstumstimer
                self.state = STATE_GROWING
                self.timer_end_timestamp = time.time() + self.grow_time_seconds
                self.is_timer_active = True
                self.update_appearance()
                logger.info(f"Blumentopf ({self.rect.center}): Wachstum gestartet ({self.grow_time_seconds}s) -> Zustand: {self.state}")
                action_taken = True

            elif self.state == STATE_GROWING:
                # Zeige verbleibende Zeit an (nur Log-Info)
                if self.timer_end_timestamp:
                    remaining = self.timer_end_timestamp - time.time()
                    logger.info(f"Blumentopf ({self.rect.center}) wächst noch. Verbleibend: {remaining:.1f}s")
                else:
                    logger.warning(f"Blumentopf ({self.rect.center}) ist im Status 'growing', aber kein Timer gesetzt?")

            elif self.state == STATE_READY_TO_EARN:
                success, stdout_msg = self._run_minigame(MINIGAME_EARN_WEED_PATH)
                if success:
                    earned_amount = 0
                    try:
                        # Versuche, die letzte Zeile des Outputs als Zahl zu interpretieren
                        earned_amount = int(stdout_msg.splitlines()[-1])
                        logger.info(f"Blumentopf ({self.rect.center}): Erfolgreich geerntet ({earned_amount} {ITEM_WEED}).")
                    except (ValueError, IndexError, TypeError):
                        logger.error(f"Konnte Ernte-Menge nicht aus Minispiel-Output lesen: '{stdout_msg}'")
                        earned_amount = 0 # Sicherheitshalber 0 annehmen

                    if earned_amount > 0:
                        if inventory.add_item(ITEM_WEED, earned_amount):
                             result_data = {'earned_weed': earned_amount}
                             logger.info(f"{earned_amount} {ITEM_WEED} zum Inventar hinzugefügt.")
                        else:
                            logger.warning(f"Konnte geernteten {ITEM_WEED} nicht hinzufügen (Inventar voll?). Ernte geht verloren!")
                            play_sound_func("error") # Inventar voll Sound?

                    # Zustand zurücksetzen nach erfolgreicher Ernte
                    self.state = STATE_OHNE_ERDE
                    self.update_appearance()
                    action_taken = True

                else:
                    logger.info(f"Blumentopf ({self.rect.center}): Minispiel (Ernten) fehlgeschlagen.")
                    play_sound_func("error") # Oder spezifischer Sound

            else:
                logger.warning(f"Unbehandelter Zustand '{self.state}' für Blumentopf-Interaktion.")

        elif self.item_type == ITEM_VERPACKSTATION:
             logger.debug(f"Interaktion mit Verpackstation im Zustand: {self.state}")
             # Prüfe Ressourcen
             weed_count = inventory.get_item_count(ITEM_WEED)
             grips_count = inventory.get_item_count(ITEM_GRIPS)

             if weed_count > 0 and grips_count > 0:
                 logger.info(f"Starte ZipWeed Minispiel von Item {self.item_type} aus.")
                 # Hier starten wir das Minispiel nicht direkt mit subprocess,
                 # da es Pygame-Elemente benötigt (screen, settings).
                 # Stattdessen geben wir ein Signal zurück, dass das Spiel gestartet werden soll.
                 action_taken = True # Signalisiert, dass eine Aktion ausgelöst wurde
                 result_data = {'action': 'start_zipweed', 'initial_weed': weed_count, 'initial_grips': grips_count}

             else:
                 logger.info("Nicht genug Weed oder Grips für Verpackstation.")
                 play_sound_func("error")


        else:
            logger.warning(f"Keine Interaktionslogik für Item-Typ '{self.item_type}' definiert.")

        return action_taken, result_data


# ========= ASSET LADEFUNKTION (Beispielstruktur, übernimm deine Logik) =========
def load_image_asset(filename, alpha=True, scale_to=None):
    """
    Dummy-Funktion zum Laden von Bildern.
    Ersetze dies durch deine tatsächliche Ladefunktion oder importiere sie.
    Diese Funktion wird von load_item_assets benötigt.
    """
    # Implementiere hier deine Logik zum Laden von Bildern aus dem IMAGE_FOLDER
    # Beispiel:
    # path = os.path.join(IMAGE_FOLDER, filename)
    # try:
    #     image = pygame.image.load(path)
    #     # ... Konvertierung, Skalierung ...
    #     return image
    # except Exception as e:
    #     logger.error(f"Fehler Laden Bild '{filename}': {e}")
    #     return None
    logger.debug(f"load_image_asset aufgerufen für: {filename} (Scale: {scale_to}) - Implementierung fehlt!")
    # Erstelle ein Dummy-Bild, damit das Spiel nicht abstürzt
    dummy_surf = pygame.Surface(scale_to if scale_to else (32, 32), pygame.SRCALPHA)
    dummy_surf.fill((random.randint(50, 200), random.randint(50, 200), random.randint(50, 200), 150))
    pygame.draw.rect(dummy_surf, (255,255,255), dummy_surf.get_rect(), 1)
    return dummy_surf

# Beispiel für load_item_assets (übernimm deine Version)
import random # Nur für Dummy-Bilder

def load_item_assets(image_folder, placed_size, icon_size, image_loader_func):
    """
    Lädt die Bilder für Inventar-Icons und platzierte Items.

    Args:
        image_folder (str): Pfad zum Ordner mit den Bildern.
        placed_size (int): Zielgröße für Bilder platzierter Items.
        icon_size (tuple): Zielgröße (width, height) für Inventar-Icons.
        image_loader_func (callable): Die Funktion zum Laden einzelner Bilder
                                      (z.B. die load_image_asset oben).

    Returns:
        tuple: (item_icons, placed_item_images, fallback_placed_image)
            item_icons (dict): {item_name: icon_surface}
            placed_item_images (dict): {item_type: {state: surface}}
            fallback_placed_image (Surface): Ein Fallback-Bild für platzierte Items.
    """
    item_icons = {}
    placed_item_images = {}

    # --- Fallback-Bild erstellen ---
    fallback_surf = pygame.Surface((placed_size, placed_size), pygame.SRCALPHA)
    fallback_surf.fill((128, 128, 128, 180)) # Halbtransparent Grau
    pygame.draw.rect(fallback_surf, (255, 255, 255), fallback_surf.get_rect(), 1)
    pygame.draw.line(fallback_surf, (255, 0, 0), (0, 0), (placed_size - 1, placed_size - 1), 2)
    pygame.draw.line(fallback_surf, (255, 0, 0), (0, placed_size - 1), (placed_size - 1, 0), 2)
    fallback_placed_image = fallback_surf
    logger.debug(f"Fallback-Bild erstellt ({placed_size}x{placed_size}).")

    # --- Item-Definitionen (Beispiel) ---
    # Du solltest deine echten Dateinamen und Zustände hier verwenden!
    item_definitions = {
        ITEM_BLUMENTOPF: {
            "icon": "blumentopf_icon.png", # Icon fürs Inventar
            "placed_images": { # Bilder für die Welt
                STATE_OHNE_ERDE: "blumentopf_leer.png",
                STATE_OHNE_SEED: "blumentopf_erde.png",
                STATE_GIESSEN: "blumentopf_samen.png", # Zustand direkt nach Pflanzen
                STATE_GROWING: "blumentopf_waechst.png",
                STATE_READY_TO_EARN: "blumentopf_fertig.png"
            }
        },
        ITEM_SACK_ERDE: {
            "icon": "sack_erde_icon.png",
            "placed_images": {} # Nicht platzierbar
        },
        ITEM_WEED_SEEDS: {
            "icon": "weed_seeds_icon.png",
            "placed_images": {} # Nicht platzierbar
        },
         ITEM_WEED: {
            "icon": "weed_normal.png", # Icon für geerntetes Weed
             "placed_images": {} # Nicht platzierbar
        },
        ITEM_VERPACKSTATION: {
             "icon": "verpackstation_icon.png",
             "placed_images": {
                 STATE_DEFAULT: "verpackstation.png" # Nur ein Zustand bisher
            }
        },
        ITEM_GRIPS: { # Verbrauchsmaterial für Verpackstation
            "icon": "grips_icon.png",
            "placed_images": {} # Nicht platzierbar
        },
        ITEM_VERPACKTES_WEED: { # Ergebnis der Verpackstation
            "icon": "packed_weed_icon.png",
            "placed_images": {} # Nicht platzierbar
        }
        # ... füge hier alle deine Items hinzu ...
    }

    # --- Laden der Assets ---
    logger.info("Lade Item-Assets...")
    for item_name, data in item_definitions.items():
        # Icon laden
        icon_filename = data.get("icon")
        if icon_filename:
            icon_surf = image_loader_func(icon_filename, alpha=True, scale_to=icon_size)
            if icon_surf:
                item_icons[item_name] = icon_surf
                # logger.debug(f"  Icon für '{item_name}' geladen.")
            else:
                logger.warning(f"  Icon für '{item_name}' ('{icon_filename}') konnte nicht geladen werden!")
                # Optional: Dummy-Icon erstellen
                item_icons[item_name] = image_loader_func(None, scale_to=icon_size) # Nutzt Dummy aus loader func

        # Platzierte Bilder laden (nur für platzierbare Items relevant)
        if item_name in PLACEABLE_ITEMS:
            placed_images_for_item = {}
            placed_data = data.get("placed_images", {})
            if not placed_data:
                 logger.warning(f"Item '{item_name}' ist in PLACEABLE_ITEMS, hat aber keine 'placed_images' definiert!")

            for state, filename in placed_data.items():
                placed_surf = image_loader_func(filename, alpha=True, scale_to=(placed_size, placed_size))
                if placed_surf:
                    placed_images_for_item[state] = placed_surf
                    # logger.debug(f"    Placed Image für '{item_name}' Zustand '{state}' geladen.")
                else:
                    logger.warning(f"    Placed Image für '{item_name}' Zustand '{state}' ('{filename}') konnte nicht geladen werden!")
                    # Hier wird später das fallback_image verwendet, wenn PlacedItem erstellt wird

            if placed_images_for_item: # Nur hinzufügen, wenn Bilder geladen wurden
                placed_item_images[item_name] = placed_images_for_item
            elif item_name in PLACEABLE_ITEMS:
                 # Wenn keine Bilder geladen wurden, aber das Item platzierbar ist,
                 # füge einen leeren Eintrag hinzu, damit das Spiel weiß, dass es theoretisch
                 # platzierbar ist, aber das Fallback-Bild verwenden muss.
                 placed_item_images[item_name] = {}
                 logger.warning(f"Keine platzierten Bilder für '{item_name}' geladen, wird Fallback nutzen.")


    logger.info(f"Item-Asset-Laden abgeschlossen. {len(item_icons)} Icons, {len(placed_item_images)} platzierbare Item-Typen mit Bildern.")
    return item_icons, placed_item_images, fallback_placed_image

# ========= HILFSFUNKTIONEN (zum Laden/Speichern von platzierten Items) =========

def load_placed_items(filepath, placed_item_images_assets, fallback_image_asset):
    """
    Lädt platzierte Items aus einer JSON-Datei.

    Args:
        filepath (str): Der Pfad zur Speicherdatei.
        placed_item_images_assets (dict): Das geladene Dictionary mit Bildern für platzierbare Items.
                                          Format: {item_type: {state: surface}}
        fallback_image_asset (Surface): Das Fallback-Bild für platzierte Items.

    Returns:
        list: Eine Liste von PlacedItem-Instanzen.
    """
    from .persistence import load_data # Lokaler Import, um Zirkelbezüge zu vermeiden? Oder global?

    logger.debug(f"Lade platzierte Items aus: {filepath}")
    loaded_items_list_data = load_data(filepath, default_data=[])
    placed_item_objects = []
    loaded_count = 0

    if isinstance(loaded_items_list_data, list):
        for item_data in loaded_items_list_data:
            if isinstance(item_data, dict):
                try:
                    item_type = item_data.get('type')
                    item_x = item_data.get('x')
                    item_y = item_data.get('y')

                    if not item_type or item_x is None or item_y is None:
                        logger.warning(f"Unvollständiger Item-Eintrag übersprungen: {item_data}")
                        continue

                    item_x = int(item_x)
                    item_y = int(item_y)
                    item_state = item_data.get('state')
                    item_timer = item_data.get('timer_end') # Timestamp
                    item_grow_time = item_data.get('grow_time')

                    # Standard-Wachstumszeit setzen, falls nicht im Savegame (für alte Saves)
                    if item_grow_time is None and item_type == ITEM_BLUMENTOPF:
                         item_grow_time = DEFAULT_GROW_TIME_SECONDS

                    # Bilder für das Item holen (oder leeres Dict, wenn Typ unbekannt)
                    images_for_this_item = placed_item_images_assets.get(item_type, {})
                    if not images_for_this_item and item_type in PLACEABLE_ITEMS:
                         logger.warning(f"Keine Bilder für geladenes Item '{item_type}' gefunden, obwohl platzierbar. Nutze Fallback.")


                    # Neues PlacedItem Objekt erstellen
                    new_item = PlacedItem(
                        item_x, item_y, item_type, images_for_this_item, fallback_image_asset,
                        item_grow_time, item_state, item_timer
                    )

                    # Prüfen ob Erstellung erfolgreich war (hat Bild und Rect?)
                    if new_item and new_item.image and new_item.rect:
                        placed_item_objects.append(new_item)
                        loaded_count += 1
                        # logger.debug(f"  -> Geladenes Item '{item_type}' hinzugefügt bei ({item_x},{item_y}).")
                    else:
                        logger.error(f"  -> FEHLER: Geladenes PlacedItem '{item_type}' konnte nicht korrekt initialisiert werden. Daten: {item_data}")

                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Fehler beim Verarbeiten des gespeicherten Items '{item_data}': {e}", exc_info=False)
                except Exception as e_load:
                    logger.error(f"Allgemeiner Fehler beim Laden eines Items: {item_data}", exc_info=True)
            else:
                logger.warning(f"Ungültiger Typ in Speicherdatei für platzierte Items gefunden: {type(item_data)}")
        logger.info(f"{loaded_count} platzierte Items erfolgreich aus '{os.path.basename(filepath)}' geladen.")
    elif loaded_items_list_data is not None:
        logger.warning(f"Inhalt der Speicherdatei '{os.path.basename(filepath)}' war keine Liste: {type(loaded_items_list_data)}.")
    else: # Falls load_data None zurückgibt (Datei nicht gefunden)
        logger.info(f"Keine Speicherdatei '{os.path.basename(filepath)}' gefunden oder Datei war leer. Keine Items geladen.")

    return placed_item_objects


def save_placed_items(items_group, filepath):
    """
    Speichert die Daten der platzierten Items in eine JSON-Datei.

    Args:
        items_group (pygame.sprite.Group): Die Gruppe mit den PlacedItem-Instanzen.
        filepath (str): Der Pfad zur Speicherdatei.

    Returns:
        bool: True bei Erfolg, False bei Fehler.
    """
    from .persistence import save_data # Lokaler Import

    logger.debug(f"Speichere platzierte Items nach: {filepath}")
    items_to_save = []
    saved_count = 0
    skipped_count = 0

    if items_group is None:
         logger.warning("Placed_items Gruppe ist None, kann nicht gespeichert werden.")
         return False

    for item in items_group:
        # Stelle sicher, dass es ein PlacedItem ist und die nötigen Attribute hat
        if isinstance(item, PlacedItem) and hasattr(item, 'rect') and item.rect and hasattr(item, 'item_type'):
            items_to_save.append({
                'type': item.item_type,
                'x': item.rect.centerx, # Center speichern ist oft robuster
                'y': item.rect.centery,
                'state': getattr(item, 'state', STATE_DEFAULT), # Sicherer Zugriff
                'timer_end': getattr(item, 'timer_end_timestamp', None), # Sicherer Zugriff
                'grow_time': getattr(item, 'grow_time_seconds', 0) # Sicherer Zugriff
            })
            saved_count += 1
        else:
            logger.warning(f"Überspringe Speichern von Sprite {item} (Typ: {getattr(item, 'item_type', '?')}), da es kein gültiges PlacedItem mit Rect/Typ ist.")
            skipped_count += 1

    success = save_data(items_to_save, filepath)
    if success:
        logger.info(f"{saved_count} platzierte Items erfolgreich in '{os.path.basename(filepath)}' gespeichert.")
        if skipped_count > 0:
             logger.warning(f"{skipped_count} Sprites in der Gruppe wurden beim Speichern übersprungen.")
    else:
        logger.error(f"Fehler beim Speichern der platzierten Items in '{os.path.basename(filepath)}' (laut save_data).")

    return success