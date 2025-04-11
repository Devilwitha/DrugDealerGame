# camera.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "camera")

class Camera:
    def __init__(self, world_width, world_height, screen_width, screen_height):
        self.camera_rect = pygame.Rect(0, 0, screen_width, screen_height)
        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        logger.info(f"Kamera initialisiert: Welt({world_width}x{world_height}), Screen({screen_width}x{screen_height})")

    def apply(self, entity):
        # Diese Funktion wird sehr oft aufgerufen, daher sparsam mit Logging sein
        # logger.debug(f"Wende Kameraversatz auf {entity} an.") # Sehr noisy!
        return entity.rect.move(-self.camera_rect.left, -self.camera_rect.top)

    def apply_rect(self, rect):
        # logger.debug(f"Wende Kameraversatz auf Rect {rect} an.") # Sehr noisy!
        return rect.move(-self.camera_rect.left, -self.camera_rect.top)

    def update(self, target):
        player_moved_screens = False
        original_cam_pos = self.camera_rect.topleft # Für Logging speichern
        target_rect = target.rect
        cam_x = self.camera_rect.left
        cam_y = self.camera_rect.top
        edge_tolerance = target.speed + 1

        moved_direction = None

        if target_rect.right >= self.camera_rect.right and self.camera_rect.right < self.world_width:
            cam_x += self.screen_width
            target.set_position(cam_x + target.rect.width // 2 + edge_tolerance, target_rect.centery)
            player_moved_screens = True
            moved_direction = "rechts"
        elif target_rect.left <= self.camera_rect.left and self.camera_rect.left > 0:
            cam_x -= self.screen_width
            target.set_position(cam_x + self.screen_width - target.rect.width // 2 - edge_tolerance, target_rect.centery)
            player_moved_screens = True
            moved_direction = "links"
        elif target_rect.bottom >= self.camera_rect.bottom and self.camera_rect.bottom < self.world_height:
            cam_y += self.screen_height
            target.set_position(target_rect.centerx, cam_y + target.rect.height // 2 + edge_tolerance)
            player_moved_screens = True
            moved_direction = "unten"
        elif target_rect.top <= self.camera_rect.top and self.camera_rect.top > 0:
            cam_y -= self.screen_height
            target.set_position(target_rect.centerx, cam_y + self.screen_height - target.rect.height // 2 - edge_tolerance)
            player_moved_screens = True
            moved_direction = "oben"

        # Begrenze Kamera auf Weltgrenzen
        final_cam_x = max(0, min(cam_x, self.world_width - self.screen_width))
        final_cam_y = max(0, min(cam_y, self.world_height - self.screen_height))

        if (final_cam_x, final_cam_y) != original_cam_pos:
            self.camera_rect.topleft = (final_cam_x, final_cam_y)
            if moved_direction:
                logger.info(f"Kamera wechselt Bildschirm nach {moved_direction}. Neue Kamera-Position: {self.camera_rect.topleft}")
            else: # Passiert, wenn die Kamera an den Rand stösst, aber kein Screenwechsel ausgelöst wurde
                 logger.debug(f"Kamera-Position angepasst an Weltgrenze: {self.camera_rect.topleft}")

        return player_moved_screens

    def get_current_screen_rect(self):
        # logger.debug(f"Aktueller Kamera-Screen Bereich abgefragt: {self.camera_rect}") # Kann noisy sein
        return self.camera_rect.copy()