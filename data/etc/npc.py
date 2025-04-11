# npc.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "npc")

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, color):
        super().__init__()
        logger.debug(f"Initialisiere NPC bei ({x}, {y}) mit Radius {radius}")
        self.radius = radius
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        logger.info(f"NPC erstellt mit ID {id(self)} bei {self.rect.center}")

    def update(self):
        # Hier könnte Logging für NPC-Verhalten hinzukommen
        # logger.debug(f"NPC {id(self)}: Update - Zustand: {self.state}")
        pass

    def interact(self):
        logger.info(f"NPC {id(self)} bei {self.rect.center} interagiert.")
        print(f"NPC bei ({self.rect.centerx}, {self.rect.centery}) sagt: 'Hallo!'")
        pass