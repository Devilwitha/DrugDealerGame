# data/etc/settings_utils.py
import os
import json
import traceback

# --- Standardeinstellungen ---
DEFAULT_SETTINGS = {
    "music_volume": 0.7,  # Standard Musiklautstärke (0.0 bis 1.0)
    "sfx_volume": 0.8,    # Standard Soundeffekt-Lautstärke (Platzhalter)
    "master_volume": 1.0  # Standard Gesamtlautstärke (Platzhalter)
}

# --- Funktion zum Laden der Einstellungen ---
def load_settings(filepath):
    """
    Lädt Einstellungen aus einer JSON-Datei.
    Gibt ein Dictionary mit den Einstellungen zurück.
    Verwendet Standardwerte, wenn die Datei nicht existiert oder ungültig ist.
    """
    current_settings = DEFAULT_SETTINGS.copy() # Start mit Defaults
    try:
        # Sicherstellen, dass der Ordner existiert (nur für den Leseversuch, nicht kritisch)
        # os.makedirs(os.path.dirname(filepath), exist_ok=True) # Nicht unbedingt nötig für reines Laden
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                loaded_data = json.load(f)
                # Überprüfe, ob geladene Daten gültige Keys haben und aktualisiere
                valid_settings = {}
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key in loaded_data and isinstance(loaded_data[key], (int, float)):
                        # Clamping: Stelle sicher, dass Werte im gültigen Bereich sind
                        valid_settings[key] = max(0.0, min(1.0, float(loaded_data[key])))
                    else:
                        print(f"WARNUNG: Ungültiger oder fehlender Wert für '{key}' in {filepath}. Nutze Standardwert {default_value}.")
                        valid_settings[key] = default_value
                current_settings = valid_settings
                print(f"INFO: Einstellungen geladen aus {filepath}: {current_settings}")
        else:
            print(f"INFO: Einstellungsdatei {filepath} nicht gefunden. Nutze Standardeinstellungen.")
            # Datei wird erst beim Speichern erstellt.
            # current_settings bleibt DEFAULT_SETTINGS.copy()
    except json.JSONDecodeError:
        print(f"FEHLER: Einstellungsdatei {filepath} ist korrupt (ungültiges JSON). Nutze Standardeinstellungen.")
        current_settings = DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"FEHLER beim Laden der Einstellungen aus {filepath}: {e}")
        traceback.print_exc()
        current_settings = DEFAULT_SETTINGS.copy() # Fallback zu Defaults
    return current_settings # Gib die geladenen oder Standardeinstellungen zurück

# --- Funktion zum Speichern der Einstellungen ---
def save_settings(filepath, settings_dict):
    """Speichert das übergebene Einstellungs-Dictionary in eine JSON-Datei."""
    try:
        # Sicherstellen, dass der Ordner existiert, bevor geschrieben wird
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(settings_dict, f, indent=4) # indent=4 für Lesbarkeit
        print(f"INFO: Einstellungen gespeichert in {filepath}: {settings_dict}")
        return True # Erfolg signalisieren
    except Exception as e:
        print(f"FEHLER beim Speichern der Einstellungen in {filepath}: {e}")
        traceback.print_exc()
        return False # Fehler signalisieren