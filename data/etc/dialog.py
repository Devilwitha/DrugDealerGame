# dialog.py
# Formatierung optimiert für Lesbarkeit
# Stand: 2025-04-15

import logging

logger = logging.getLogger(__name__)

# Struktur:
# DIALOGS = {
#     "dialog_knoten_id": {
#         "npc_text": "Was der NPC sagt.",
#         "responses": [
#             {"text": "Antwort 1", "action": "code", "next_node": "ziel_id_1"},
#             ...
#         ]
#     }, ...
# }
# Mögliche Aktions-Codes: "open_shop", "open_sell_menu", "end_dialog", None

DIALOGS = {
    # --- Händler Dialoge ---
    "händler_start": {
        "npc_text": "Sei gegrüßt, Reisender! Interessiert an feinen Waren?",
        "responses": [
            {"text": "Zeig mir, was du hast!", "action": "open_shop", "next_node": None},
            {"text": "Wie läuft das Geschäft?", "action": None, "next_node": "händler_geschäft"},
            {"text": "Nur mal umgesehen.", "action": "end_dialog", "next_node": None},
        ]
    },
    "händler_geschäft": {
        "npc_text": "Ach, man schlägt sich durch. Die Zeiten sind hart, aber gute Ware findet immer einen Käufer.",
        "responses": [
            {"text": "Verstehe. Zeig mal deine Waren.", "action": "open_shop", "next_node": None},
            {"text": "Interessant. Lebewohl.", "action": "end_dialog", "next_node": None}
        ]
    },

    # --- Client/Kunden Dialoge (NEU) ---
    "client_start": {
        "npc_text": "Psst... hast du was für mich? Ich zahle gut.",
        "responses": [
            {"text": "[Weed verkaufen]", "action": "open_sell_menu", "next_node": None}, # Aktion zum Öffnen des Verkaufs-UI
            {"text": "Was suchst du denn?", "action": None, "next_node": "client_sucht"},
            {"text": "Kein Interesse.", "action": "end_dialog", "next_node": None},
        ]
    },
    "client_sucht": {
        "npc_text": "Du weißt schon... das gute Zeug. Wenn du was hast, sag Bescheid.",
        "responses": [
            {"text": "[Weed verkaufen]", "action": "open_sell_menu", "next_node": None},
            {"text": "Verstanden.", "action": "end_dialog", "next_node": None},
        ]
    },
     "client_danke": { # Optional: Nach erfolgreichem Verkauf (könnte in game.py gesetzt werden)
        "npc_text": "Gutes Geschäft. Meld dich wieder.",
        "responses": [
            {"text": "[Gehen]", "action": "end_dialog", "next_node": None}
        ]
    },
     "client_zu_wenig": { # Optional: Wenn Spieler nicht genug hat (könnte in game.py gesetzt werden)
        "npc_text": "Das ist nicht genug. Komm wieder, wenn du mehr hast.",
        "responses": [
            {"text": "[Okay]", "action": "end_dialog", "next_node": None}
        ]
    },
    "client_nichts_da": { # Wenn Spieler gar kein Weed hat
        "npc_text": "Schade, ich hätte was gebraucht. Sag Bescheid, wenn du fündig wirst.",
         "responses": [
            {"text": "[Okay]", "action": "end_dialog", "next_node": None}
        ]
    },


    # --- Generischer Dialog ---
    "generic_hallo": {
        "npc_text": "Hallo.",
        "responses": [
            {"text": "[Gehen]", "action": "end_dialog", "next_node": None}
        ]
    }
}

def get_dialog_node(node_id):
    """Holt einen Dialogknoten anhand seiner ID."""
    if not node_id:
        logger.warning("Versuch, Dialogknoten mit leerer ID abzurufen.")
        return None
    node = DIALOGS.get(node_id)
    if node:
        logger.debug(f"Dialogknoten '{node_id}' gefunden.")
        return node
    else:
        logger.error(f"Dialogknoten mit ID '{node_id}' nicht gefunden!")
        # Fallback auf einen Standard-Knoten oder None
        return DIALOGS.get("generic_hallo") # Beispiel-Fallback