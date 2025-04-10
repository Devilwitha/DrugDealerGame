# npc.py
import pygame

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, color):
        super().__init__()
        # Erstelle ein einfaches Kreis-Image für den NPC
        self.radius = radius
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        # self.image = pygame.image.load("npc_type1.png").convert_alpha() # Später: Lade ein echtes Bild
        self.rect = self.image.get_rect(center=(x, y))

        # Hier könnten NPC-spezifische Attribute hin:
        # self.dialogue = ["Hallo!", "Wie geht es dir?"]
        # self.movement_pattern = ...
        # self.state = "idle"

    def update(self):
        # Momentan tun NPCs nichts.
        # Hier könntest du Bewegungsmuster, Zustandsänderungen etc. implementieren.
        # z.B. self.move()
        pass

    def interact(self):
        # Wird aufgerufen, wenn der Spieler mit dem NPC interagiert
        # print(random.choice(self.dialogue))
        print(f"NPC bei ({self.rect.centerx}, {self.rect.centery}) sagt: 'Hallo!'")
        pass

    # Optional: Bewegungsmethoden, falls NPCs sich bewegen sollen
    # def move(self):
    #     ...