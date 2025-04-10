# camera.py
import pygame

class Camera:
    def __init__(self, world_width, world_height, screen_width, screen_height):
        # Das Kamera-Rechteck repräsentiert den sichtbaren Ausschnitt der Welt
        # Es startet oben links (0, 0)
        self.camera_rect = pygame.Rect(0, 0, screen_width, screen_height)
        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height

    def apply(self, entity):
        """Verschiebt das Rechteck einer Entität (Sprite) relativ zur Kamera."""
        return entity.rect.move(-self.camera_rect.left, -self.camera_rect.top)

    def apply_rect(self, rect):
        """Verschiebt ein beliebiges Rechteck relativ zur Kamera."""
        return rect.move(-self.camera_rect.left, -self.camera_rect.top)

    def update(self, target):
        """
        Prüft, ob das Ziel (Spieler) den Rand des aktuellen Bildschirms erreicht hat
        und verschiebt die Kamera zum nächsten "Bildschirm".
        Gibt True zurück, wenn der Bildschirm gewechselt wurde und der Spieler
        neu positioniert werden musste, sonst False.
        """
        player_moved_screens = False
        target_rect = target.rect
        cam_x = self.camera_rect.left
        cam_y = self.camera_rect.top

        # Toleranz, damit der Spieler nicht *exakt* am Rand sein muss
        edge_tolerance = target.speed + 1 # Etwas mehr als die max. Bewegung pro Frame

        # Nach Rechts wechseln?
        if target_rect.right >= self.camera_rect.right and self.camera_rect.right < self.world_width:
            cam_x += self.screen_width
            # Spieler auf die linke Seite des neuen Screens setzen
            target.set_position(cam_x + target.rect.width // 2 + edge_tolerance, target_rect.centery)
            player_moved_screens = True

        # Nach Links wechseln?
        elif target_rect.left <= self.camera_rect.left and self.camera_rect.left > 0:
            cam_x -= self.screen_width
            # Spieler auf die rechte Seite des neuen Screens setzen
            target.set_position(cam_x + self.screen_width - target.rect.width // 2 - edge_tolerance, target_rect.centery)
            player_moved_screens = True

        # Nach Unten wechseln?
        elif target_rect.bottom >= self.camera_rect.bottom and self.camera_rect.bottom < self.world_height:
            cam_y += self.screen_height
            # Spieler auf die obere Seite des neuen Screens setzen
            target.set_position(target_rect.centerx, cam_y + target.rect.height // 2 + edge_tolerance)
            player_moved_screens = True

        # Nach Oben wechseln?
        elif target_rect.top <= self.camera_rect.top and self.camera_rect.top > 0:
            cam_y -= self.screen_height
            # Spieler auf die untere Seite des neuen Screens setzen
            target.set_position(target_rect.centerx, cam_y + self.screen_height - target.rect.height // 2 - edge_tolerance)
            player_moved_screens = True

        # Stelle sicher, dass die Kamera nicht über die Weltgrenzen hinausgeht
        self.camera_rect.left = max(0, min(cam_x, self.world_width - self.screen_width))
        self.camera_rect.top = max(0, min(cam_y, self.world_height - self.screen_height))

        return player_moved_screens

    def get_current_screen_rect(self):
        """Gibt das Rechteck zurück, das den aktuellen sichtbaren Bereich
           in Weltkoordinaten darstellt."""
        return self.camera_rect.copy()