# dialog.py
import logging

logger = logging.getLogger(__name__)

# Struktur:
# DIALOGS = {
#    "dialog_knoten_id": {
#        "npc_text": "Was der NPC sagt.",
#        "responses": [
#            {"text": "Antwort 1 des Spielers", "action": "aktion_code", "next_node": "ziel_knoten_id_1"},
#            {"text": "Antwort 2 des Spielers", "action": None, "next_node": "ziel_knoten_id_2"},
#            ...
#        ]
#    }, ...
# }
# Mögliche Aktions-Codes: "open_shop", "end_dialog", "quest_start_xy", None

DIALOGS = {
    "händler_start": {
        "npc_text": "Sei gegrüßt, Reisender! Interessiert an feinen Waren?",
        "responses": [
            {"text": "Zeig mir, was du hast!", "action": "open_shop", "next_node": None},
            {"text": "Wie läuft das Geschäft?", "action": None, "next_node": "händler_geschäft"},
            {"text": "Nur mal umgesehen.", "action": "end_dialog", "next_node": None},
            {"text": "Auf Wiedersehen.", "action": "end_dialog", "next_node": None}
        ]
    },
    "händler_geschäft": {
        "npc_text": "Ach, man schlägt sich durch. Die Zeiten sind hart, aber gute Ware findet immer einen Käufer.",
        "responses": [
            {"text": "Verstehe. Zeig mal deine Waren.", "action": "open_shop", "next_node": None},
            {"text": "Interessant. Lebewohl.", "action": "end_dialog", "next_node": None}
        ]
    },
    "generic_hallo": {
         "npc_text": "Hallo.",
         "responses": [
             {"text": "[Gehen]", "action": "end_dialog", "next_node": None}
         ]
    }
    # Füge hier weitere Dialoge oder Knoten hinzu
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