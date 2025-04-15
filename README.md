DrugDealerGame

Das Projekt "DrugDealerGame" ist ein Spiel, das mit Python entwickelt wurde, höchstwahrscheinlich unter Verwendung der Pygame-Bibliothek (typisch für solche Dateistrukturen und Dateinamen wie player.py, npc.py, camera.py).

Spielkonzept:
Der Spieler schlüpft in die Rolle eines Drogendealers. Das Gameplay scheint sich um folgende Aspekte zu drehen:

Item-Management: Sammeln, Verwalten und möglicherweise Herstellen von verschiedenen Gegenständen (Drogen, Werkzeuge etc.) über ein Inventarsystem (inventory.py, items.py, inventar.json).
Interaktion: Interaktion mit Nicht-Spieler-Charakteren (NPCs) (npc.py), möglicherweise für Handel, Quests oder Dialoge (dialog.py).
Platzierung: Platzieren von Gegenständen in der Spielwelt (placed_items.json, devtool_plazierenvonKästchen.py).
Minispiele: Teilnahme an themenbezogenen Minispielen zur Herstellung oder Verarbeitung von Drogen, wie z.B. das Anbauen von Pflanzen (Growing/), das Verpacken von "Weed" (zipWeed/) und das Kochen von "Crack" (cockCrack/).
Fortschritt speichern: Das Spiel speichert den Fortschritt des Spielers, einschliesslich Inventar, Spielerposition und platzierter Gegenstände (persistence.py, data/savedata/).
Konfiguration: Anpassbare Einstellungen (settings.json, options_menu.py, settings_utils.py).
Technologie:
Es verwendet Python und wahrscheinlich Pygame für die Grafik, die Ereignisbehandlung und die Spielschleife. Die Daten (Spielstände, Einstellungen) werden im JSON-Format gespeichert. Es gibt Hinweise auf plattformspezifische Überlegungen (platform_utils.py, androiderkennung.txt), was auf Versuche hindeuten könnte, das Spiel auch auf anderen Plattformen (evtl. Android) lauffähig zu machen.

Funktion der Python-Dateien (.py)

Hier ist eine Beschreibung der wahrscheinlichen Funktion jeder Python-Datei im Projekt:

main.py (im Hauptverzeichnis):

Dies ist der Haupteinstiegspunkt des Spiels.
Initialisiert Pygame (falls verwendet), erstellt das Hauptspielfenster.
Erstellt eine Instanz der Hauptspielklasse (wahrscheinlich aus data/etc/game.py).
Startet die Hauptspielschleife (Game Loop).
Kümmert sich um das grundlegende Setup und den Start des Spiels.
data/miniGame/Template.py:

Eine Vorlagendatei oder Basisklasse für Minispiele.
Definiert wahrscheinlich eine gemeinsame Struktur oder Schnittstelle (Methoden, Attribute), die alle spezifischen Minispiele implementieren müssen.
data/miniGame/zipWeed/zipWeed.py:

Implementiert das Minispiel "zipWeed".
Enthält die Logik und die grafische Darstellung für das Verpacken von "Weed".
Nutzt vermutlich Pygame für Interaktion und Anzeige.
data/miniGame/Growing/earn_buds.py:

Teil des "Growing"-Minispielkomplexes.
Verantwortlich für die Logik, wie "Buds" (Knospen) verdient werden, möglicherweise basierend auf Zeit, Spieleraktionen oder dem Zustand der Pflanzen aus anderen Growing-Skripten.
data/miniGame/Growing/grow_plant2.py:

Eine weitere Stufe oder Variante des Pflanzenanbau-Minispiels.
Könnte ein fortgeschrittenes Wachstumsstadium, eine andere Pflanze oder eine alternative Mechanik darstellen.
Nutzt Pygame für die Visualisierung.
data/miniGame/Growing/plant_grow1.py:

Implementiert den ersten oder grundlegenden Teil des Pflanzenanbau-Minispiels.
Verwaltet die Logik und Darstellung des Pflanzenwachstums und die Interaktion des Spielers damit.
Nutzt Pygame.
data/miniGame/cockCrack/cockCrack.py:

Startet und verwaltet das "cockCrack" (wahrscheinlich cook Crack) Minispiel.
Initialisiert die verschiedenen Teile dieses Minispiels.
Nutzt Pygame.
data/miniGame/cockCrack/cockCrackpart2.py, ...part3.py, ...part4.py:

Sequentielle Teile oder Phasen des "cookCrack"-Minispiels.
Jede Datei implementiert einen bestimmten Schritt im Kochprozess (z.B. Zutaten mischen, erhitzen, abkühlen).
Nutzt Pygame.
data/etc/camera.py:

Verwaltet die Spielkamera oder den sichtbaren Ausschnitt der Spielwelt.
Sorgt dafür, dass die Ansicht dem Spieler folgt, wenn die Spielwelt grösser ist als der Bildschirm.
Berechnet, welche Teile der Welt gezeichnet werden müssen.
data/etc/config.py:

Enthält globale Konfigurationseinstellungen und Konstanten für das Spiel.
Beispiele: Bildschirmauflösung, Framerate (FPS), Kachelgrössen, Farbdefinitionen, eventuell Dateipfade.
data/etc/devtool_plazierenvonKästchen.py:

Ein Entwicklerwerkzeug (Dev-Tool), nicht für den Endspieler gedacht.
Wurde wahrscheinlich während der Entwicklung verwendet, um Kollisionsboxen, Triggerbereiche oder andere rechteckige Elemente ("Kästchen") visuell auf der Karte zu platzieren und deren Positionen zu speichern (möglicherweise in box_positions.txt).
data/etc/dialog.py:

Verwaltet das Dialogsystem des Spiels.
Zeigt Textboxen an, wenn der Spieler mit NPCs spricht.
Könnte Logik für Dialogbäume oder Antwortmöglichkeiten enthalten.
data/etc/game.py:

Enthält die Hauptspielklasse (z.B. Game).
Organisiert den Hauptablauf des Spiels: Event-Handling (Tastatur, Maus), Update der Spiellogik (Spielerbewegung, NPC-Verhalten), Rendern der Grafik.
Verwaltet verschiedene Spielzustände (Menü, Spielen, Minispiel, Pause).
Integriert und koordiniert die anderen Module (player.py, npc.py, camera.py, etc.).
data/etc/inventory.py:

Implementiert das Inventarsystem des Spielers.
Verwaltet das Hinzufügen, Entfernen und Stapeln von Gegenständen.
Ist verantwortlich für das Laden und Speichern des Inventarstatus (aus/in data/savedata/inventar.json).
Stellt möglicherweise auch die Inventar-UI (Benutzeroberfläche) dar oder stellt Daten dafür bereit.
data/etc/items.py:

Definiert die verschiedenen Arten von Gegenständen (Items), die im Spiel existieren.
Enthält Klassen oder Datenstrukturen für Items mit ihren Eigenschaften (Name, Beschreibung, Wert, Stapelbarkeit, Effekte).
Verwaltet auch Gegenstände, die in der Spielwelt platziert sind (Laden/Speichern aus data/savedata/placed_items.json).
data/etc/npc.py:

Definiert die Klasse(n) für Nicht-Spieler-Charaktere (NPCs).
Beinhaltet deren Verhalten (Bewegungsmuster, KI), Aussehen (Sprites) und Interaktionslogik (Starten von Dialogen, Anbieten von Shops).
data/etc/options_menu.py:

Implementiert das Options- oder Einstellungsmenü des Spiels.
Ermöglicht dem Spieler das Ändern von Spieleinstellungen (z.B. Lautstärke, Steuerung).
Interagiert wahrscheinlich mit settings_utils.py zum Laden und Speichern der Einstellungen.
data/etc/persistence.py:

Verantwortlich für das Speichern und Laden des gesamten Spielzustands.
Koordiniert das Speichern/Laden von Daten aus verschiedenen Modulen (Spielerposition, Inventar, platzierte Items) in die entsprechenden JSON-Dateien im data/savedata/ Ordner.
data/etc/platform_utils.py:

Enthält Hilfsfunktionen, um Unterschiede zwischen verschiedenen Betriebssystemen oder Plattformen zu behandeln.
Könnte z.B. Pfadtrennzeichen anpassen oder plattformspezifische Funktionen bereitstellen (im Zusammenhang mit androiderkennung.txt).
data/etc/player.py:

Definiert die Klasse für den Spielercharakter.
Verwaltet den Zustand des Spielers (Position, Geld, Inventar-Referenz?).
Beinhaltet die Logik für Spielerbewegung, Kollisionserkennung und Interaktion mit der Spielwelt (Items aufheben, NPCs ansprechen).
Lädt und speichert die Spielerposition (data/savedata/player_position.json).
data/etc/settings_utils.py:

Stellt Hilfsfunktionen speziell für das Laden und Speichern von Spieleinstellungen aus/in die Datei data/settings/settings.json bereit.
Wird vom options_menu.py und beim Spielstart verwendet.
data/etc/setup.py:

Könnte ein Skript sein, das einmalige Setup-Aufgaben durchführt (z.B. Erstellen von Verzeichnissen, Initialisieren von Speicherdateien, wenn sie nicht existieren).
Alternativ (weniger wahrscheinlich wegen des Speicherorts) könnte es eine setuptools-Datei für die Paketierung des Spiels sein, aber das ist in Pygame-Projekten oft nicht in einem etc-Ordner. Wahrscheinlich eher für die Spielinitialisierung.
data/etc/shop_items.py:

Definiert, welche Gegenstände in Shops gekauft oder verkauft werden können.
Legt Preise, verfügbare Mengen und möglicherweise fest, welcher NPC welche Waren anbietet.
data/etc/ui_manager.py:

Verwaltet die Elemente der Benutzeroberfläche (User Interface - UI).
Kümmert sich um das Zeichnen und die Interaktion mit Buttons, Textfeldern, Menüs, dem HUD (Heads-Up Display), Inventarfenstern etc.
