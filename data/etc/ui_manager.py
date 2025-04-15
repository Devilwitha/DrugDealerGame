# data/etc/ui_manager.py
# Stand: 2025-04-15 (Neu erstellt für Refactoring)
# Formatiert für maximale Lesbarkeit

import pygame
import logging
import locale # Für Währungsformatierung

# Eigene Module importieren (Passe ggf. Pfade/Import-Syntax an deine Struktur an)
try:
    from . import config  # Konfiguration für Farben, Zustände etc.
    # Zugriff auf die Item-Daten für Shop und Icons
    from . import items
    # Zugriff auf die Dialogstruktur
    from . import dialog
    # Zugriff auf das Shop-Angebot
    from . import shop_items
except ImportError:
    # Fallback für den Fall, dass das Skript direkt ausgeführt wird o.ä.
    import config
    import items
    import dialog
    import shop_items


# Logging für dieses Modul
logger = logging.getLogger(__name__)

# ========= HILFSFUNKTION: TEXTUMBRUCH (aus game.py verschoben) =========
def wrap_text(surface, text, font, color, rect, aa=True):
    """Zeichnet Text mit Zeilenumbruch innerhalb eines Rechtecks."""
    if not font:
        logger.error("wrap_text: Font ist None!")
        return
    if not text: # Leeren Text nicht verarbeiten
        return

    lines = []
    words = str(text).split(' ') # Sicherstellen, dass es ein String ist
    current_line_words = []

    while words:
        word = words.pop(0)
        current_line_words.append(word)
        try:
            line_width, _ = font.size(' '.join(current_line_words))
            if line_width > rect.width:
                if len(current_line_words) > 1:
                    last_word = current_line_words.pop()
                    words.insert(0, last_word)
                    lines.append(' '.join(current_line_words))
                    current_line_words = [last_word]
                else: # Wort selbst ist schon zu lang
                    lines.append(current_line_words[0]) # Füge das zu lange Wort hinzu (wird abgeschnitten)
                    logger.warning(f"wrap_text: Wort '{current_line_words[0]}' ist breiter als das Rechteck ({rect.width}).")
                    current_line_words = [] # Beginne nächste Zeile leer

        except pygame.error as e:
            logger.exception(f"Fehler bei font.size() in wrap_text: {e}")
            return

    if current_line_words:
        lines.append(' '.join(current_line_words))

    y = rect.top
    line_spacing = font.get_linesize() * 0.9
    line_height = font.get_height()

    for line in lines:
        if y + line_height > rect.bottom:
            logger.warning("Textumbruch: Nicht alle Zeilen passen ins Rechteck.")
            break
        try:
            img = font.render(line, aa, color)
            # Links ausrichten innerhalb des Text-Rects
            surface.blit(img, (rect.left, y))
            y += int(line_spacing)
        except pygame.error as e:
            logger.exception(f"Fehler bei font.render() für Zeile: '{line}': {e}")
            break
        except Exception as e:
             logger.exception(f"Allg. Fehler beim Rendern der Zeile '{line}': {e}")
             break

# ========= UI ZEICHENFUNKTIONEN =========

def draw_dialog_ui(surface, screen_width, screen_height, dialog_node_id, fonts):
    """
    Zeichnet das Dialogfenster.

    Args:
        surface (pygame.Surface): Die Oberfläche zum Zeichnen.
        screen_width (int): Breite des Bildschirms.
        screen_height (int): Höhe des Bildschirms.
        dialog_node_id (str): Die ID des aktuellen Dialogknotens.
        fonts (dict): Ein Dictionary mit den benötigten Fonts {'dialog': Font, ...}.

    Returns:
        list: Eine Liste von Tupeln (pygame.Rect, response_data) für klickbare Antworten.
              response_data ist das Dictionary der Antwort aus der Dialogstruktur.
              Gibt leere Liste zurück bei Fehlern oder wenn keine Antworten vorhanden sind.
    """
    clickable_elements = []
    dialog_font = fonts.get('dialog')
    node = dialog.get_dialog_node(dialog_node_id) # Holt Knoten aus dialog.py

    if not node:
        logger.error(f"Ungültiger Dialog-Knoten ID '{dialog_node_id}' in draw_dialog_ui.")
        if dialog_font: # Fehlermeldung anzeigen
             err_surf = dialog_font.render(f"Dialog Error: Node '{dialog_node_id}' not found!", True, config.RED)
             err_rect = err_surf.get_rect(center=(screen_width // 2, screen_height // 2))
             surface.blit(err_surf, err_rect)
        return clickable_elements # Leere Liste zurückgeben

    if not dialog_font:
        logger.error("Dialog-Font fehlt in draw_dialog_ui.")
        # Optional: Fallback-Text ohne Font zeichnen?
        return clickable_elements # Leere Liste zurückgeben

    # Dimensionen und Position des Dialogfensters (z.B. unteres Drittel)
    dlg_h = screen_height // 3
    dlg_y = screen_height - dlg_h
    dlg_rect = pygame.Rect(0, dlg_y, screen_width, dlg_h)

    # Hintergrund und Rand
    pygame.draw.rect(surface, config.DARK_BLUE, dlg_rect)
    pygame.draw.rect(surface, config.WHITE, dlg_rect, 3)

    # NPC Text anzeigen (mit Zeilenumbruch)
    npc_text_rect = pygame.Rect(
        dlg_rect.left + 20, dlg_rect.top + 15,
        dlg_rect.width - 40, dlg_rect.height // 2 - 30
    )
    wrap_text(surface, node.get("npc_text", "Dialogfehler..."), dialog_font, config.WHITE, npc_text_rect)

    # Spieler-Antworten als Buttons zeichnen
    resp_y = npc_text_rect.bottom + 15
    resp_h = 35
    resp_sp = 10
    # Breite könnte dynamischer sein, hier fix als Beispiel
    btn_w = min(dlg_rect.width - 40, max(200, dlg_rect.width // 2 - 30))

    mouse_pos = pygame.mouse.get_pos() # Für Hover-Effekt

    for i, response in enumerate(node.get("responses", [])):
        btn_x = dlg_rect.left + 20
        # Optional: Mehrere Spalten, wenn viele Antworten? Hier nur eine Spalte.
        btn_y = resp_y + i * (resp_h + resp_sp)

        if btn_y + resp_h > dlg_rect.bottom - 10:
            logger.warning("Nicht genug Platz für alle Dialogantworten.")
            break

        resp_rect = pygame.Rect(btn_x, btn_y, btn_w, resp_h)
        # Füge Rect und die dazugehörigen Antwortdaten zur Liste hinzu
        clickable_elements.append((resp_rect, response))

        # Hover-Effekt
        hover = resp_rect.collidepoint(mouse_pos)
        btn_col = config.LIGHT_GREY if hover else config.GREY

        pygame.draw.rect(surface, btn_col, resp_rect)
        pygame.draw.rect(surface, config.WHITE, resp_rect, 1) # Rand

        # Text der Antwort zentriert im Button
        resp_text = response.get("text", "?")
        try:
            resp_surf = dialog_font.render(resp_text, True, config.BLACK)
            resp_text_rect = resp_surf.get_rect(center=resp_rect.center)
            # Ggf. Text abschneiden, wenn zu lang für Button
            if resp_text_rect.width > resp_rect.width - 10:
                resp_surf = dialog_font.render(resp_text[:len(resp_text)//2] + "...", True, config.BLACK) # Simples abschneiden
                resp_text_rect = resp_surf.get_rect(center=resp_rect.center)
            surface.blit(resp_surf, resp_text_rect)
        except pygame.error as e:
             logger.error(f"Fehler beim Rendern des Dialog-Antwort-Textes '{resp_text}': {e}")
        except Exception as e:
             logger.exception(f"Allg. Fehler beim Rendern der Dialog-Antwort '{resp_text}': {e}")


    return clickable_elements


def draw_shop_ui(surface, screen_width, screen_height, player_money, locale_set, item_icons, fonts):
    """
    Zeichnet das Shop-Fenster.

    Args:
        surface (pygame.Surface): Die Oberfläche zum Zeichnen.
        screen_width (int): Breite des Bildschirms.
        screen_height (int): Höhe des Bildschirms.
        player_money (float): Aktuelles Geld des Spielers.
        locale_set (bool): Info für Währungsformatierung.
        item_icons (dict): Dictionary mit Item-Icons {item_name: Surface}.
        fonts (dict): Dictionary mit benötigten Fonts {'ui': Font, 'shop': Font, 'button': Font, 'inventory': Font}.

    Returns:
        tuple: (list_of_item_elements, exit_button_rect)
               list_of_item_elements: Liste von Tupeln [(pygame.Rect, item_data), ...] für klickbare Items.
               exit_button_rect: pygame.Rect für den Verlassen-Button oder None.
    """
    clickable_item_elements = []
    shop_exit_button_rect = None # Initialisieren

    ui_font = fonts.get('ui')
    shop_font = fonts.get('shop')
    button_font = fonts.get('button')
    inventory_font = fonts.get('inventory') # Für Geldanzeige

    margin = 50
    shop_rect = pygame.Rect(margin, margin, screen_width - 2 * margin, screen_height - 2 * margin)

    # Hintergrund und Rand
    pygame.draw.rect(surface, config.DARK_BLUE, shop_rect)
    pygame.draw.rect(surface, config.WHITE, shop_rect, 3)

    # Titel
    if ui_font:
        title_surf = ui_font.render("Shop", True, config.YELLOW)
        title_rect = title_surf.get_rect(centerx=shop_rect.centerx, top=shop_rect.top + 15)
        surface.blit(title_surf, title_rect)

    # Geld anzeigen
    if inventory_font:
        try:
            money_txt_shop = locale.currency(player_money, grouping=True) if locale_set else f"{player_money:.2f} $"
        except Exception:
            money_txt_shop = f"{player_money:.2f}" # Fallback
        money_surf_shop = inventory_font.render(f"Dein Geld: {money_txt_shop}", True, config.GREEN)
        money_rect_shop = money_surf_shop.get_rect(right=shop_rect.right - 20, top=shop_rect.top + 20)
        surface.blit(money_surf_shop, money_rect_shop)

    # Grid für Shop-Items
    cols = 4
    rows = 4 # Anpassen nach Bedarf
    available_items_list = shop_items.get_available_items() # Holt Liste aus shop_items.py

    grid_x = shop_rect.left + 30
    grid_y = shop_rect.top + 70
    grid_area_height = shop_rect.height - 120 # Platz für Grid (ohne Titel, Geld, Exit)
    cell_w = (shop_rect.width - 60) // cols
    cell_h = max(50, grid_area_height // rows) # Mindesthöhe sicherstellen
    icon_display_size = min(cell_w // 2, cell_h // 2, 64) # Angepasste Icon-Größe für Shop

    mouse_pos = pygame.mouse.get_pos()

    for i, item_data in enumerate(available_items_list):
        if i >= cols * rows:
            logger.warning("Mehr Shop-Items verfügbar als angezeigt werden können.")
            break

        row = i // cols
        col = i % cols
        cell_x = grid_x + col * cell_w
        cell_y = grid_y + row * cell_h

        # Prüfen, ob Zelle noch ins Fenster passt
        if cell_y + cell_h > shop_rect.bottom - 60: # Platz für Exit Button lassen
             break

        cell_rect = pygame.Rect(cell_x, cell_y, cell_w - 10, cell_h - 10)
        clickable_item_elements.append((cell_rect, item_data)) # Rect und Item-Daten speichern

        # Hover-Effekt
        hover = cell_rect.collidepoint(mouse_pos)
        can_afford = player_money >= item_data.get("price", float('inf'))
        cell_col = config.LIGHT_GREY if hover else config.GREY
        border_col = config.YELLOW if (hover and can_afford) else config.RED if (hover and not can_afford) else config.WHITE

        pygame.draw.rect(surface, cell_col, cell_rect)
        pygame.draw.rect(surface, border_col, cell_rect, 1 if not hover else 2) # Dickerer Rand bei Hover

        # Item-Icon, Name und Preis
        name = item_data.get("name", "Unbekannt")
        price = item_data.get("price", 0.0)
        icon_surf_shop = item_icons.get(name)

        text_y_start = cell_rect.top + 5
        if icon_surf_shop:
            # Icon skalieren und zeichnen
            try:
                shop_icon_scaled = pygame.transform.smoothscale(icon_surf_shop, (icon_display_size, icon_display_size))
                icon_rect_shop = shop_icon_scaled.get_rect(centerx=cell_rect.centerx, top=cell_rect.top + 5)
                surface.blit(shop_icon_scaled, icon_rect_shop)
                text_y_start = icon_rect_shop.bottom + 3
            except Exception as e_scale:
                 logger.error(f"Fehler Skalieren Shop-Icon für {name}: {e_scale}")
                 # Fallback: Namen zeichnen
                 if shop_font:
                    name_surf = shop_font.render(name, True, config.WHITE)
                    name_rect = name_surf.get_rect(centerx=cell_rect.centerx, top=text_y_start)
                    surface.blit(name_surf, name_rect)
                    text_y_start = name_rect.bottom + 3
        elif shop_font: # Nur Namen, wenn kein Icon
            name_surf = shop_font.render(name, True, config.WHITE)
            name_rect = name_surf.get_rect(centerx=cell_rect.centerx, top=text_y_start)
            surface.blit(name_surf, name_rect)
            text_y_start = name_rect.bottom + 3

        # Preis anzeigen
        if shop_font:
            try:
                price_txt = locale.currency(price, grouping=True, symbol=False) + " €" if locale_set else f"{price:.2f} $"
            except:
                price_txt = f"{price:.2f}"
            price_color = config.YELLOW if can_afford else config.RED # Preis rot färben, wenn nicht leistbar
            price_surf_shop = shop_font.render(price_txt, True, price_color)
            price_rect_shop = price_surf_shop.get_rect(centerx=cell_rect.centerx, bottom=cell_rect.bottom - 5)
            surface.blit(price_surf_shop, price_rect_shop)

    # Verlassen-Button
    exit_w = 100
    exit_h = 40
    exit_x = shop_rect.centerx - exit_w // 2
    exit_y = shop_rect.bottom - exit_h - 15
    shop_exit_button_rect = pygame.Rect(exit_x, exit_y, exit_w, exit_h)
    hover = shop_exit_button_rect.collidepoint(mouse_pos)
    exit_col = config.RED if hover else config.DARK_BLUE
    pygame.draw.rect(surface, exit_col, shop_exit_button_rect)
    pygame.draw.rect(surface, config.WHITE, shop_exit_button_rect, 2)
    if button_font:
        exit_surf = button_font.render("Verlassen", True, config.WHITE)
        exit_rect = exit_surf.get_rect(center=shop_exit_button_rect.center)
        surface.blit(exit_surf, exit_rect)

    return clickable_item_elements, shop_exit_button_rect


def draw_sell_ui(surface, screen_width, screen_height, player_money, locale_set, inventory, item_icons, fonts):
    """
    Zeichnet das Verkaufsfenster (aktuell nur für Weed).

    Args:
        surface (pygame.Surface): Die Oberfläche zum Zeichnen.
        screen_width (int): Breite des Bildschirms.
        screen_height (int): Höhe des Bildschirms.
        player_money (float): Aktuelles Geld des Spielers.
        locale_set (bool): Info für Währungsformatierung.
        inventory (Inventory): Das Spieler-Inventar.
        item_icons (dict): Dictionary mit Item-Icons {item_name: Surface}.
        fonts (dict): Dictionary mit benötigten Fonts {'ui', 'shop', 'button', 'inventory'}.

    Returns:
        tuple: (sell_button_rect, exit_button_rect)
               sell_button_rect: pygame.Rect für den Verkaufen-Button oder None (wenn nichts zu verkaufen).
               exit_button_rect: pygame.Rect für den Verlassen-Button oder None.
    """
    sell_button_rect = None # Initialisieren
    sell_exit_button_rect = None # Initialisieren

    ui_font = fonts.get('ui')
    shop_font = fonts.get('shop') # Nutzen Shop-Font für Item-Text
    button_font = fonts.get('button')
    inventory_font = fonts.get('inventory') # Für Geldanzeige

    margin = 50
    sell_ui_rect = pygame.Rect(margin, margin, screen_width - 2 * margin, screen_height - 2 * margin)

    # Hintergrund und Rand
    pygame.draw.rect(surface, config.DARK_GREEN, sell_ui_rect)
    pygame.draw.rect(surface, config.WHITE, sell_ui_rect, 3)

    # Titel
    if ui_font:
        title_surf = ui_font.render("Weed Verkaufen", True, config.YELLOW)
        title_rect = title_surf.get_rect(centerx=sell_ui_rect.centerx, top=sell_ui_rect.top + 15)
        surface.blit(title_surf, title_rect)

    # Aktuelles Geld anzeigen
    if inventory_font:
        try:
            money_txt_sell = locale.currency(player_money, grouping=True) if locale_set else f"{player_money:.2f} $"
        except Exception:
            money_txt_sell = f"{player_money:.2f}" # Fallback
        money_surf = inventory_font.render(f"Dein Geld: {money_txt_sell}", True, config.GREEN)
        money_rect = money_surf.get_rect(right=sell_ui_rect.right - 20, top=sell_ui_rect.top + 20)
        surface.blit(money_surf, money_rect)

    # Bereich für das zu verkaufende Item (Weed)
    item_name_to_sell = items.ITEM_WEED # Nutze Konstante aus items.py
    item_price = config.WEED_SELL_PRICE # Nutze Konstante aus config.py
    item_icon = item_icons.get(item_name_to_sell)
    item_qty = 0
    if inventory:
        item_qty = inventory.get_item_count(item_name_to_sell)
    else:
        logger.error("draw_sell_ui: Inventar ist None!")

    item_area_x = sell_ui_rect.left + 30
    item_area_y = sell_ui_rect.top + 70
    item_area_w = sell_ui_rect.width - 60
    item_area_h = 100
    item_display_rect = pygame.Rect(item_area_x, item_area_y, item_area_w, item_area_h)
    pygame.draw.rect(surface, config.GREY, item_display_rect)
    pygame.draw.rect(surface, config.WHITE, item_display_rect, 1)

    # Item-Icon und Text
    text_start_x = item_display_rect.left + 15
    if item_icon:
        # Icon skalieren für Anzeige (Beispielgröße)
        try:
             icon_scaled = pygame.transform.smoothscale(item_icon, (item_area_h - 20, item_area_h - 20))
             icon_rect = icon_scaled.get_rect(centery=item_display_rect.centery, left=item_display_rect.left + 15)
             surface.blit(icon_scaled, icon_rect)
             text_start_x = icon_rect.right + 20
        except Exception as e:
            logger.error(f"Fehler beim Skalieren des Sell-Icons für {item_name_to_sell}: {e}")
    else:
        logger.warning(f"Kein Icon für '{item_name_to_sell}' im Verkaufs-UI gefunden.")

    if shop_font:
        name_surf = shop_font.render(f"{item_name_to_sell} (Du hast: {item_qty})", True, config.WHITE)
        name_rect = name_surf.get_rect(left=text_start_x, top=item_display_rect.top + 15)
        surface.blit(name_surf, name_rect)

        try:
            price_txt_sell = locale.currency(item_price, grouping=True) if locale_set else f"{item_price:.2f} $"
        except Exception:
            price_txt_sell = f"{item_price:.2f}"
        price_surf = shop_font.render(f"Preis pro Stück: {price_txt_sell}", True, config.YELLOW)
        price_rect = price_surf.get_rect(left=text_start_x, top=name_rect.bottom + 10)
        surface.blit(price_surf, price_rect)

    # Verkaufen-Button
    mouse_pos = pygame.mouse.get_pos()
    button_w = 150
    button_h = 40
    button_y = item_display_rect.bottom + 20
    button_x = sell_ui_rect.centerx - button_w // 2
    temp_sell_button_rect = pygame.Rect(button_x, button_y, button_w, button_h)

    if item_qty > 0: # Button nur aktiv, wenn man etwas hat
        sell_button_rect = temp_sell_button_rect # Rect für Klick-Erkennung speichern
        hover = sell_button_rect.collidepoint(mouse_pos)
        btn_col = config.LIGHT_GREY if hover else config.GREY
        pygame.draw.rect(surface, btn_col, sell_button_rect)
        pygame.draw.rect(surface, config.WHITE, sell_button_rect, 1)
        if button_font:
            sell_text_surf = button_font.render("1 Verkaufen", True, config.BLACK)
            sell_text_rect = sell_text_surf.get_rect(center=sell_button_rect.center)
            surface.blit(sell_text_surf, sell_text_rect)
    else: # Button inaktiv
        pygame.draw.rect(surface, (50, 50, 50), temp_sell_button_rect) # Dunkler
        pygame.draw.rect(surface, config.GREY, temp_sell_button_rect, 1)
        if button_font:
            sell_text_surf = button_font.render("Nichts da", True, config.LIGHT_GREY)
            sell_text_rect = sell_text_surf.get_rect(center=temp_sell_button_rect.center)
            surface.blit(sell_text_surf, sell_text_rect)
        # sell_button_rect bleibt None

    # Verlassen-Button
    exit_w = 100
    exit_h = 40
    exit_x = sell_ui_rect.centerx - exit_w // 2
    exit_y = sell_ui_rect.bottom - exit_h - 15
    sell_exit_button_rect = pygame.Rect(exit_x, exit_y, exit_w, exit_h) # Immer klickbar
    hover = sell_exit_button_rect.collidepoint(mouse_pos)
    exit_col = config.RED if hover else config.DARK_BLUE
    pygame.draw.rect(surface, exit_col, sell_exit_button_rect)
    pygame.draw.rect(surface, config.WHITE, sell_exit_button_rect, 2)
    if button_font:
        exit_surf = button_font.render("Verlassen", True, config.WHITE)
        exit_rect = exit_surf.get_rect(center=sell_exit_button_rect.center)
        surface.blit(exit_surf, exit_rect)

    return sell_button_rect, sell_exit_button_rect


# ========= UI EVENT HANDLER =========

def handle_dialog_click(mouse_pos, clickable_dialog_elements, inventory):
    """
    Verarbeitet einen Mausklick im Dialog-Zustand.

    Args:
        mouse_pos (tuple): Die (x, y) Position des Mausklicks.
        clickable_dialog_elements (list): Liste von (Rect, response_data) aus draw_dialog_ui.
        inventory (Inventory): Das Spieler-Inventar (für Zustandsprüfungen benötigt).

    Returns:
        dict | None: Ein Dictionary mit dem Ergebnis der Aktion, z.B.
                     {'next_state': config.GAME_STATE_SHOP},
                     {'next_state': config.GAME_STATE_PLAY},
                     {'next_dialog_node': 'node_id'},
                     oder None, wenn kein klickbares Element getroffen wurde.
    """
    for rect, response_data in clickable_dialog_elements:
        if rect.collidepoint(mouse_pos):
            action = response_data.get("action")
            next_node = response_data.get("next_node")
            logger.debug(f"Dialog Antwort '{response_data.get('text', '?')}' geklickt. Aktion: {action}, Nächster Knoten: {next_node}")

            if action == "open_shop":
                return {'next_state': config.GAME_STATE_SHOP}
            elif action == "open_sell_menu":
                # Prüfe, ob der Spieler überhaupt etwas zu verkaufen hat (Weed)
                if inventory and inventory.has_item(items.ITEM_WEED, 1):
                    return {'next_state': config.GAME_STATE_SELL}
                else:
                    # Spieler hat nichts, zeige anderen Dialogknoten statt Verkaufsmenü
                    logger.info("Verkaufen-Aktion, aber kein Weed im Inventar. Suche 'nichts_da'-Knoten.")
                    # Versuche, zu einem spezifischen "nichts da"-Knoten zu springen
                    # (Hier Annahme: Händler hat "händler_nichts_da", Kunde hat "client_nichts_da")
                    # Dies könnte flexibler gestaltet werden, z.B. durch ein Feld in der response_data
                    if next_node and "client" in next_node: # Heuristik
                         alternative_node = "client_nichts_da"
                    else:
                         alternative_node = "händler_nichts_da" # Fallback oder Standard für Händler

                    # Prüfe, ob der alternative Knoten existiert
                    if dialog.get_dialog_node(alternative_node):
                         return {'next_dialog_node': alternative_node}
                    else:
                         logger.warning(f"Konnte alternativen Dialogknoten '{alternative_node}' nicht finden.")
                         # Fallback: Dialog beenden, wenn kein passender Knoten gefunden wird
                         return {'next_state': config.GAME_STATE_PLAY}

            elif action == "end_dialog":
                return {'next_state': config.GAME_STATE_PLAY}
            elif next_node:
                # Stelle sicher, dass der nächste Knoten existiert
                if dialog.get_dialog_node(next_node):
                     return {'next_dialog_node': next_node}
                else:
                     logger.error(f"Dialog-Antwort verweist auf ungültigen nächsten Knoten: '{next_node}'. Beende Dialog.")
                     return {'next_state': config.GAME_STATE_PLAY}
            else:
                # Keine Aktion und kein nächster Knoten -> Dialog beenden
                logger.debug("Dialog-Antwort ohne Aktion/NextNode -> Beende Dialog.")
                return {'next_state': config.GAME_STATE_PLAY}
            # break # Eigentlich nicht nötig, da wir returnen

    return None # Nichts geklickt

def handle_shop_click(mouse_pos, clickable_shop_items, exit_button_rect, inventory, current_money, play_sound_func):
    """
    Verarbeitet einen Mausklick im Shop-Zustand.

    Args:
        mouse_pos (tuple): Die (x, y) Position des Mausklicks.
        clickable_shop_items (list): Liste von (Rect, item_data) aus draw_shop_ui.
        exit_button_rect (pygame.Rect | None): Rect des Verlassen-Buttons.
        inventory (Inventory): Das Spieler-Inventar.
        current_money (float): Das aktuelle Geld des Spielers.
        play_sound_func (callable): Funktion zum Abspielen von Sounds (z.B. "error").

    Returns:
        dict | None: Ein Dictionary mit dem Ergebnis der Aktion, z.B.
                     {'next_state': config.GAME_STATE_PLAY},
                     {'money_change': -preis, 'item_added': ('ItemName', 1)},
                     oder None, wenn kein klickbares Element getroffen wurde.
    """
    # Prüfe Klick auf Items zuerst
    for rect, item_data in clickable_shop_items:
        if rect.collidepoint(mouse_pos):
            name = item_data.get("name")
            price = item_data.get("price")

            if name and price is not None:
                logger.debug(f"Shop: Klick auf '{name}' (Preis: {price:.2f}). Geld: {current_money:.2f}")
                if current_money >= price:
                    # Versuch, Item zum Inventar hinzuzufügen (könnte fehlschlagen, wenn voll)
                    if inventory and inventory.add_item(name, 1):
                        logger.info(f"Erfolgreich gekauft: {name}.")
                        # Gib die Änderung zurück, game.py führt sie aus
                        return {'money_change': -price, 'item_added': (name, 1)}
                    else:
                        logger.warning(f"Kauf von '{name}' fehlgeschlagen: Inventar voll oder Inventar-Objekt fehlt.")
                        play_sound_func("error") # Sound für Inventar voll
                        return None # Keine Zustandsänderung
                else:
                    logger.info(f"Kauf von '{name}' fehlgeschlagen: Nicht genug Geld.")
                    play_sound_func("error") # Sound für nicht genug Geld
                    return None # Keine Zustandsänderung
            else:
                logger.error(f"Ungültige Item-Daten im Shop geklickt: {item_data}")
                return None # Fehler, keine Aktion

    # Prüfe Klick auf Verlassen-Button, wenn kein Item geklickt wurde
    if exit_button_rect and exit_button_rect.collidepoint(mouse_pos):
        logger.debug("Shop: Klick auf Verlassen-Button.")
        return {'next_state': config.GAME_STATE_PLAY}

    return None # Nichts Relevantes geklickt


def handle_sell_click(mouse_pos, sell_button_rect, exit_button_rect, inventory, play_sound_func):
    """
    Verarbeitet einen Mausklick im Verkaufs-Zustand.

    Args:
        mouse_pos (tuple): Die (x, y) Position des Mausklicks.
        sell_button_rect (pygame.Rect | None): Rect des Verkaufen-Buttons (ist None, wenn nichts da ist).
        exit_button_rect (pygame.Rect | None): Rect des Verlassen-Buttons.
        inventory (Inventory): Das Spieler-Inventar.
        play_sound_func (callable): Funktion zum Abspielen von Sounds (z.B. "error", "sell_success").

    Returns:
        dict | None: Ein Dictionary mit dem Ergebnis der Aktion, z.B.
                     {'next_state': config.GAME_STATE_PLAY},
                     {'money_change': preis, 'item_removed': ('Weed', 1)},
                     oder None, wenn kein klickbares Element getroffen wurde.
    """
    item_name_to_sell = items.ITEM_WEED
    item_price = config.WEED_SELL_PRICE

    # Prüfe Klick auf Verkaufen-Button
    if sell_button_rect and sell_button_rect.collidepoint(mouse_pos):
        logger.debug(f"Verkaufen: Klick auf Verkaufen-Button.")
        if inventory and inventory.has_item(item_name_to_sell, 1):
            # Versuche Item zu entfernen
            if inventory.remove_item(item_name_to_sell, 1):
                logger.info(f"1 {item_name_to_sell} verkauft.")
                play_sound_func("sell_success") # Optional: Eigener Sound für Verkauf
                # Gib Änderung zurück
                return {'money_change': item_price, 'item_removed': (item_name_to_sell, 1)}
            else:
                # Sollte nicht passieren, wenn has_item True war
                logger.error("Konnte Weed nicht entfernen, obwohl has_item True war?")
                play_sound_func("error")
                return None # Keine Änderung
        else:
            # Sollte nicht passieren, da Button dann None sein sollte
            logger.warning("Klick auf Verkaufen, obwohl kein Weed (mehr) da ist.")
            play_sound_func("error")
            return None # Keine Änderung

    # Prüfe Klick auf Verlassen-Button
    if exit_button_rect and exit_button_rect.collidepoint(mouse_pos):
        logger.debug("Verkaufen: Klick auf Verlassen-Button.")
        return {'next_state': config.GAME_STATE_PLAY}

    return None # Nichts Relevantes geklickt