# camera.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "camera")

class Camera:
    """
    Verwaltet den sichtbaren Ausschnitt der Spielwelt (Kamera-Rechteck).
    Implementiert Bildschirmwechsel, wenn der Spieler den Rand erreicht.
    Bietet Methoden, um Welt-Koordinaten in Bildschirm-Koordinaten umzurechnen.
    """
    def __init__(self, world_width, world_height, screen_width, screen_height):
        """
        Initialisiert die Kamera.

        Args:
            world_width (int): Die Gesamtbreite der Spielwelt in Pixeln.
            world_height (int): Die Gesamthöhe der Spielwelt in Pixeln.
            screen_width (int): Die Breite des sichtbaren Bildschirms (Fensterbreite).
            screen_height (int): Die Höhe des sichtbaren Bildschirms (Fensterhöhe).
        """
        # Das Rechteck, das den aktuellen Kameraausschnitt in Weltkoordinaten darstellt.
        # Wird initial auf (0,0) gesetzt und in game.py nach Spielerstellung angepasst.
        self.camera_rect = pygame.Rect(0, 0, screen_width, screen_height)
        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        logger.info(f"Kamera initialisiert: Welt({world_width}x{world_height}), Screen({screen_width}x{screen_height})")

    def apply(self, entity):
        """
        Berechnet die Bildschirmkoordinaten für ein Sprite (entity) basierend
        auf dem Kameraversatz. Wird beim Zeichnen verwendet.

        Args:
            entity (pygame.sprite.Sprite): Das Sprite mit 'rect'-Attribut.

        Returns:
            pygame.Rect: Ein neues Rechteck mit den Bildschirmkoordinaten.
        """
        # Verschiebt das Rechteck um den negativen Kamera-Offset.
        return entity.rect.move(-self.camera_rect.left, -self.camera_rect.top)

    def apply_rect(self, rect):
        """
        Berechnet die Bildschirmkoordinaten für ein Rechteck (rect)
        basierend auf dem Kameraversatz.

        Args:
            rect (pygame.Rect): Das Rechteck.

        Returns:
            pygame.Rect: Ein neues Rechteck mit den Bildschirmkoordinaten.
        """
        return rect.move(-self.camera_rect.left, -self.camera_rect.top)

    def screen_to_world(self, screen_x, screen_y):
        """
        Rechnet Bildschirmkoordinaten (z.B. Mausposition) in Weltkoordinaten um.

        Args:
            screen_x (int): X-Koordinate auf dem Bildschirm.
            screen_y (int): Y-Koordinate auf dem Bildschirm.

        Returns:
            tuple: (world_x, world_y) - die entsprechenden Weltkoordinaten.
        """
        world_x = screen_x + self.camera_rect.left
        world_y = screen_y + self.camera_rect.top
        return world_x, world_y

    def update(self, target):
        """
        Aktualisiert die Kameraposition basierend auf der Position des Ziels (target).
        Implementiert den Bildschirmwechsel und positioniert das Ziel neu.

        Args:
            target (Player): Das Spielerobjekt mit 'rect', 'speed',
                             'set_position' und 'prevent_immediate_exit'.

        Returns:
            bool: True, wenn ein Bildschirmwechsel stattfand, sonst False.
        """
        player_moved_screens = False
        original_cam_pos = self.camera_rect.topleft
        target_rect = target.rect
        cam_x = self.camera_rect.left
        cam_y = self.camera_rect.top
        # Puffer, um Spieler nach Wechsel leicht vom Rand zu entfernen
        edge_tolerance = target.speed + 1 # Beispielwert

        moved_direction = None # Für Logging

        # --- Bildschirmwechsel-Logik ---
        # Prüfe rechten Rand
        if target_rect.right >= self.camera_rect.right and self.camera_rect.right < self.world_width:
            cam_x += self.screen_width # Neue Kamera-X
            new_player_x = cam_x + target.rect.width // 2 + edge_tolerance # Position auf neuem Screen
            target.set_position(new_player_x, target_rect.centery)
            target.prevent_immediate_exit() # Verhindere sofortiges Zurücklaufen
            player_moved_screens = True; moved_direction = "rechts"
        # Prüfe linken Rand
        elif target_rect.left <= self.camera_rect.left and self.camera_rect.left > 0:
            cam_x -= self.screen_width # Neue Kamera-X
            new_player_x = cam_x + self.screen_width - target.rect.width // 2 - edge_tolerance # Position auf neuem Screen
            target.set_position(new_player_x, target_rect.centery)
            target.prevent_immediate_exit() # Verhindere sofortiges Zurücklaufen
            player_moved_screens = True; moved_direction = "links"
        # Prüfe unteren Rand
        elif target_rect.bottom >= self.camera_rect.bottom and self.camera_rect.bottom < self.world_height:
            cam_y += self.screen_height # Neue Kamera-Y
            new_player_y = cam_y + target.rect.height // 2 + edge_tolerance # Position auf neuem Screen
            target.set_position(target_rect.centerx, new_player_y)
            target.prevent_immediate_exit() # Verhindere sofortiges Zurücklaufen
            player_moved_screens = True; moved_direction = "unten"
        # Prüfe oberen Rand
        elif target_rect.top <= self.camera_rect.top and self.camera_rect.top > 0:
            cam_y -= self.screen_height # Neue Kamera-Y
            new_player_y = cam_y + self.screen_height - target.rect.height // 2 - edge_tolerance # Position auf neuem Screen
            target.set_position(target_rect.centerx, new_player_y)
            target.prevent_immediate_exit() # Verhindere sofortiges Zurücklaufen
            player_moved_screens = True; moved_direction = "oben"

        # --- Kamera an Weltgrenzen anpassen ---
        final_cam_x = max(0, min(cam_x, self.world_width - self.screen_width))
        final_cam_y = max(0, min(cam_y, self.world_height - self.screen_height))

        # --- Kamera-Rechteck aktualisieren ---
        if (final_cam_x, final_cam_y) != original_cam_pos:
            self.camera_rect.topleft = (final_cam_x, final_cam_y)
            if moved_direction:
                logger.info(f"Kamera wechselt Bildschirm nach {moved_direction}. Neue Position: {self.camera_rect.topleft}")
            else:
                logger.debug(f"Kamera-Position an Weltgrenze angepasst: {self.camera_rect.topleft}")

        return player_moved_screens

    def get_current_screen_rect(self):
        """
        Gibt das aktuelle Kamera-Rechteck (sichtbarer Bereich) in Weltkoordinaten zurück.

        Returns:
            pygame.Rect: Eine Kopie des aktuellen Kamera-Rechtecks.
        """
        return self.camera_rect.copy()