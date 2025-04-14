# persistence.py
import json
import os
import logging

# Hole einen Logger für dieses Modul
logger = logging.getLogger(__name__) # Name ist 'persistence'

def ensure_directory_exists(filepath):
    """Stellt sicher, dass das Verzeichnis für den gegebenen Dateipfad existiert."""
    dir_path = os.path.dirname(filepath)
    if dir_path: # Nur wenn ein Verzeichnis im Pfad angegeben ist
        try:
            os.makedirs(dir_path, exist_ok=True) # exist_ok=True: Kein Fehler, wenn schon vorhanden
            return True
        except OSError as e:
            logger.error(f"Fehler beim Erstellen/Prüfen von Verzeichnis '{dir_path}': {e}")
            return False
    return True # Kein Verzeichnis angegeben, also erfolgreich

def save_data(data, filepath):
    """
    Speichert Python-Daten (müssen JSON-serialisierbar sein) in eine JSON-Datei.

    Args:
        data: Die zu speichernden Python-Daten (z.B. dict, list).
        filepath (str): Der vollständige Pfad zur Zieldatei.

    Returns:
        bool: True bei Erfolg, False bei einem Fehler.
    """
    # Stelle sicher, dass das Zielverzeichnis existiert
    if not ensure_directory_exists(filepath):
        logger.error(f"Speichern fehlgeschlagen: Verzeichnis für '{filepath}' konnte nicht sichergestellt werden.")
        return False

    # Versuche, die Daten als JSON zu speichern
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # logger.info(f"Daten erfolgreich in '{filepath}' gespeichert.") # War vorher auskommentiert
        return True
    except TypeError as e:
        logger.error(f"Fehler beim Konvertieren der Daten nach JSON für '{filepath}': {e}. Daten NICHT gespeichert.")
        return False
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Daten in '{filepath}': {e}")
        return False

def load_data(filepath, default_data=None):
    """
    Lädt Daten aus einer JSON-Datei.

    Args:
        filepath (str): Der vollständige Pfad zur Quelldatei.
        default_data: Der Wert, der zurückgegeben wird, wenn die Datei nicht
                      gefunden wird oder ein Fehler auftritt (Standard: None).

    Returns:
        Die geladenen Python-Daten oder default_data bei Fehlern.
    """
    if not ensure_directory_exists(filepath):
         logger.warning(f"Laden fehlgeschlagen: Verzeichnis für '{filepath}' nicht sichergestellt.")
         return default_data
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # logger.info(f"Daten erfolgreich aus '{filepath}' geladen.") # War vorher auskommentiert
        return data
    except FileNotFoundError:
        logger.info(f"Datei '{filepath}' nicht gefunden. Gebe Standardwert zurück.")
        return default_data
    except json.JSONDecodeError:
        logger.error(f"Fehler Lesen '{filepath}': Ungültiges JSON. Gebe Standardwert zurück.")
        return default_data
    except Exception as e:
        logger.error(f"Unerwarteter Fehler Laden '{filepath}': {e}", exc_info=True)
        return default_data