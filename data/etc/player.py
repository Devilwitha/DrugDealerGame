# player.py
import pygame
import logging

logger = logging.getLogger(__name__) # Logger für dieses Modul (__name__ wird zu "player")

class Player(pygame.sprite.Sprite):
    """
    Repräsentiert den Spielercharakter. Verwaltet Position, Bewegung und Kollision
    innerhalb der vom Kamera-Rechteck vorgegebenen Grenzen.
    """
    def __init__(self, x, y, radius, color):
        """
        Initialisiert den Spieler.

        Args:
            x (int): Die initiale X-Koordinate der linken oberen Ecke (top-left).
            y (int): Die initiale Y-Koordinate der linken oberen Ecke (top-left).
            radius (int): Der Radius des Spieler-Kreises. Beeinflusst die Größe.
            color (tuple): Die Farbe des Spielers (RGB).
        """
        super().__init__() # Initialisiert die Basisklasse pygame.sprite.Sprite
        logger.debug(f"Initialisiere Spieler mit top-left bei ({x}, {y}) und Radius {radius}")
        self.radius = radius
        # Erstelle eine transparente Oberfläche für den Spieler
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        # Zeichne den Spieler als Kreis auf die Oberfläche, zentriert in der Surface
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        # Erstelle das rect-Attribut mit top-left bei (x, y).
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 5 # Geschwindigkeit in Pixel pro Frame
        # Aktuelle Bewegungsänderung pro Frame (wird in update gesetzt)
        self.dx = 0
        self.dy = 0
        # Benutze float für präzisere Positionsberechnung intern (basierend auf Mittelpunkt)
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)
        # Timer, um sofortiges Zurückwechseln des Bildschirms zu verhindern
        self._prevent_exit_timer = 0
        self._prevent_exit_duration = 5 # Dauer des Timers in Frames
        logger.info(f"Spieler erstellt mit ID {id(self)} bei Rect={self.rect}")


    def update(self, keys, screen_bounds_rect):
        """
        Aktualisiert die Spielerposition basierend auf Tastatureingaben und Grenzen.

        Args:
            keys (dict): Ergebnis von pygame.key.get_pressed().
            screen_bounds_rect (pygame.Rect): Das Rechteck des aktuell sichtbaren
                                             Bildschirms (von der Kamera).
        """
        self.dx = 0
        self.dy = 0
        moved = False

        # Prüfe, ob der Screen-Wechsel-Verhinderungs-Timer aktiv ist
        if self._prevent_exit_timer > 0:
            self._prevent_exit_timer -= 1
            return # Keine Bewegung erlauben, solange Timer aktiv ist
        else:
            # Timer ist nicht aktiv, prüfe Bewegungstasten
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.dx = -self.speed; moved = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.dx = self.speed; moved = True
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.dy = -self.speed; moved = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.dy = self.speed; moved = True

            # Normiere diagonale Bewegung
            if self.dx != 0 and self.dy != 0:
                self.dx *= 0.7071
                self.dy *= 0.7071

        if not moved: return # Kein Update nötig bei keiner Eingabe

        # Berechne die potenzielle neue Mittelpunkt-Position (float)
        new_center_x = self.x + self.dx
        new_center_y = self.y + self.dy

        # Erstelle ein temporäres Rechteck zur Kollisionsprüfung
        predicted_rect = self.rect.copy()
        predicted_rect.center = (new_center_x, new_center_y)

        original_center = (self.x, self.y) # Für Logging merken

        # Prüfe, ob die neue Position innerhalb der Bildschirmgrenzen liegt
        if screen_bounds_rect.contains(predicted_rect):
            self.x = new_center_x
            self.y = new_center_y
        else:
            # Bewegung würde Grenzen überschreiten, versuche nur X oder nur Y
            # logger.debug(f"Spieler {id(self)}: Bewegung blockiert bei ({new_center_x:.1f}, {new_center_y:.1f})")
            # Prüfe nur X-Bewegung
            predicted_rect.center = (new_center_x, self.y)
            if screen_bounds_rect.contains(predicted_rect):
                self.x = new_center_x
            # Prüfe nur Y-Bewegung (unabhängig von X)
            predicted_rect.center = (self.x, new_center_y)
            if screen_bounds_rect.contains(predicted_rect):
                self.y = new_center_y

        # Aktualisiere das tatsächliche rect (int-basiert) nur bei Änderung
        if self.x != original_center[0] or self.y != original_center[1]:
            self.rect.center = (int(self.x), int(self.y))

    def prevent_immediate_exit(self):
        """Startet einen Timer, der Spielerbewegung kurz unterbricht."""
        if self._prevent_exit_timer <= 0:
            logger.debug(f"Spieler {id(self)}: Aktiviere Exit-Prevention ({self._prevent_exit_duration} Frames).")
            self._prevent_exit_timer = self._prevent_exit_duration

    def set_position(self, x, y):
        """
        Setzt die Spielerposition (Mittelpunkt) direkt. Wird von der Kamera genutzt.

        Args:
            x (float or int): Neue X-Koordinate des Mittelpunkts.
            y (float or int): Neue Y-Koordinate des Mittelpunkts.
        """
        old_center = self.rect.center
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))
        logger.info(f"Spieler {id(self)}: Position manuell gesetzt von Center={old_center} zu Center={self.rect.center}")