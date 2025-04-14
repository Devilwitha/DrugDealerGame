# npc.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "npc")

class NPC(pygame.sprite.Sprite):
    """
    Eine einfache Klasse für einen Nicht-Spieler-Charakter (NPC).
    Aktuell nur ein statischer Kreis.
    """
    def __init__(self, x, y, radius, color):
        """
        Initialisiert den NPC.

        Args:
            x (int): Welt-X-Koordinate des Mittelpunkts.
            y (int): Welt-Y-Koordinate des Mittelpunkts.
            radius (int): Radius des NPC-Kreises.
            color (tuple): Farbe des NPCs (RGB).
        """
        super().__init__()
        logger.debug(f"Initialisiere NPC bei ({x}, {y}) mit Radius {radius}")
        self.radius = radius
        # Erstelle das Aussehen des NPCs (hier ein einfacher Kreis)
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        # Setze das rect-Attribut basierend auf dem Mittelpunkt
        self.rect = self.image.get_rect(center=(x, y))
        logger.info(f"NPC erstellt mit ID {id(self)} bei {self.rect.center}")

    def update(self):
        """
        Aktualisiert den Zustand des NPCs (z.B. Bewegung, Animation).
        Momentan leer.
        """
        # Hier könnte zukünftige Logik für NPC-Verhalten hinzukommen
        # z.B. self.move_randomly()
        pass

    def interact(self):
        """Wird aufgerufen, wenn der Spieler mit dem NPC interagiert."""
        # Beispiel-Interaktion: Gibt Nachricht auf Konsole aus.
        logger.info(f"NPC {id(self)} bei {self.rect.center} interagiert.")
        print(f"NPC bei ({self.rect.centerx}, {self.rect.centery}) sagt: 'Hallo!'")
        # Hier könnte komplexere Dialog- oder Quest-Logik folgen.
        pass