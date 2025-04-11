# player.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "player")

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, color):
        super().__init__()
        logger.debug(f"Initialisiere Spieler bei ({x}, {y}) mit Radius {radius}")
        self.radius = radius
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.dx = 0
        self.dy = 0
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)
        self._prevent_exit_timer = 0
        self._prevent_exit_duration = 5
        logger.info(f"Spieler erstellt mit ID {id(self)} bei {self.rect.center}")


    def update(self, keys, screen_bounds_rect):
        self.dx = 0
        self.dy = 0
        moved = False

        if self._prevent_exit_timer > 0:
            self._prevent_exit_timer -= 1
            # logger.debug(f"Spieler {id(self)}: Exit-Prevention Timer: {self._prevent_exit_timer}") # Kann noisy sein
            return # Keine Bewegung während des Timers erlauben
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.dx = -self.speed
                moved = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.dx = self.speed
                moved = True
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.dy = -self.speed
                moved = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.dy = self.speed
                moved = True

            if self.dx != 0 and self.dy != 0:
                self.dx *= 0.7071
                self.dy *= 0.7071

        if not moved and (self.dx == 0 and self.dy == 0): # Nur loggen, wenn sich was ändern *könnte*
             return # Keine Bewegung, kein Update nötig

        new_x = self.x + self.dx
        new_y = self.y + self.dy
        predicted_rect = self.rect.copy()
        predicted_rect.center = (new_x, new_y)

        original_pos = (self.x, self.y) # Für Logging speichern

        if screen_bounds_rect.contains(predicted_rect):
             self.x = new_x
             self.y = new_y
        else:
            logger.debug(f"Spieler {id(self)}: Bewegung zu ({new_x:.1f}, {new_y:.1f}) ausserhalb von {screen_bounds_rect} blockiert.")
            predicted_rect.center = (new_x, self.y)
            if screen_bounds_rect.contains(predicted_rect):
                self.x = new_x
                logger.debug(f"Spieler {id(self)}: Nur X-Bewegung erlaubt.")
            predicted_rect.center = (self.x, new_y)
            if screen_bounds_rect.contains(predicted_rect):
                self.y = new_y
                logger.debug(f"Spieler {id(self)}: Nur Y-Bewegung erlaubt.")


        # Nur loggen, wenn sich die Position tatsächlich geändert hat
        if self.x != original_pos[0] or self.y != original_pos[1]:
            self.rect.center = (int(self.x), int(self.y))
            # logger.debug(f"Spieler {id(self)}: Position aktualisiert auf {self.rect.center}") # Kann sehr noisy sein


    def prevent_immediate_exit(self):
        """Startet einen kurzen Timer, um zu verhindern, dass der Spieler
           sofort wieder den Bildschirm wechselt."""
        if self._prevent_exit_timer <= 0: # Nur starten, wenn nicht schon aktiv
            logger.debug(f"Spieler {id(self)}: Aktiviere Exit-Prevention für {self._prevent_exit_duration} Frames.")
            self._prevent_exit_timer = self._prevent_exit_duration

    def set_position(self, x, y):
        """Setzt die Position des Spielers direkt (nützlich nach Screenwechsel)."""
        old_pos = self.rect.center
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))
        logger.info(f"Spieler {id(self)}: Position manuell gesetzt von {old_pos} zu {self.rect.center}")