# npc.py (Angepasst für Typen und Dialog)
# Formatierung optimiert für Lesbarkeit
# Stand: 2025-04-15

import pygame
import logging

logger = logging.getLogger(__name__)

class NPC(pygame.sprite.Sprite):
    """
    Eine Klasse für Nicht-Spieler-Charaktere (NPCs).
    Kann verschiedene Typen haben (z.B. 'generic', 'merchant', 'client').
    """
    def __init__(self, x, y, radius, color, npc_type="generic", dialog_id=None):
        """
        Initialisiert den NPC.

        Args:
            x (int): Welt-X-Koordinate des Mittelpunkts.
            y (int): Welt-Y-Koordinate des Mittelpunkts.
            radius (int): Radius des NPC-Kreises.
            color (tuple): Farbe des NPCs (RGB).
            npc_type (str): Typ des NPCs (z.B. 'merchant', 'client').
            dialog_id (str, optional): Start-ID für den Dialogbaum dieses NPCs. Defaults to None.
        """
        super().__init__()
        logger.debug(f"Initialisiere NPC Typ '{npc_type}' bei ({x}, {y}) mit Radius {radius}")
        self.radius = radius
        self.npc_type = npc_type # Typ des NPCs
        self.dialog_id = dialog_id # Zugehörige Dialog-ID

        # --- Aussehen (bleibt vorerst ein Kreis) ---
        # In Zukunft könnte dies basierend auf npc_type ein Bild laden
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        logger.info(f"NPC Typ '{self.npc_type}' erstellt mit ID {id(self)} bei {self.rect.center}")

    def update(self):
        """
        Aktualisiert den Zustand des NPCs. Momentan leer.
        """
        pass

    # Die interact Methode hier ist nicht mehr zwingend nötig,
    # da die Logik in game.py anhand des Typs entscheidet, was passiert.
    # Man könnte sie aber nutzen, um z.B. den Start-Dialog dynamisch zu machen.
    # def interact(self):
    #     logger.info(f"NPC {id(self)} ({self.npc_type}) interagiert.")
    #     return self.dialog_id # Gibt z.B. die Dialog-ID zurück