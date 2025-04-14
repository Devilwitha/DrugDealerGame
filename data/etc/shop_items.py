# shop_items.py

# Struktur: Liste von Dictionaries
# Jedes Dictionary repräsentiert ein kaufbares Item.
# Der 'name' sollte mit den Namen in items.ICON_FILES übereinstimmen,
# damit das richtige Icon in game.py geladen werden kann.

SHOP_ITEMS = [
    {"name": "Sack Erde", "price": 5.00, "description": "Ein Sack voll fruchtbarer Erde."},
    {"name": "Weed Seeds", "price": 10.00, "description": "Samen für Standard-Gras."},
    {"name": "Blumentopf", "price": 25.00, "description": "Ein einfacher Topf zum Anpflanzen."},
    # --- Füge hier bis zu 32 Items hinzu ---
    {"name": "Sack Erde", "price": 5.00, "description": "Ein Sack voll fruchtbarer Erde."},
    {"name": "Weed Seeds", "price": 10.00, "description": "Samen für Standard-Gras."},
    {"name": "Blumentopf", "price": 25.00, "description": "Ein einfacher Topf zum Anpflanzen."},
    {"name": "Sack Erde", "price": 5.00, "description": "Ein Sack voll fruchtbarer Erde."},
    {"name": "Weed Seeds", "price": 10.00, "description": "Samen für Standard-Gras."},
    # Beispiel für ein Item ohne Icon (zeigt dann Text im Inventar/Shop)
    # {"name": "Gießkanne", "price": 50.00, "description": "Zum Bewässern deiner Pflanzen."},

]

# Optional: Funktion, um Items zu holen (falls später komplexere Logik nötig)
def get_available_items():
    """Gibt die Liste der aktuell verfügbaren Shop-Items zurück."""
    # Momentan nur die statische Liste
    # Später könnte hier Logik rein (z.B. abhängig vom Spielfortschritt)
    return SHOP_ITEMS