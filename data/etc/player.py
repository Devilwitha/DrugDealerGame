# player.py
import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, color):
        super().__init__()
        # Erstelle ein einfaches Kreis-Image für den Spieler
        self.radius = radius
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA) # SRCALPHA für Transparenz
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        # self.image = pygame.image.load("player.png").convert_alpha() # Später: Lade ein echtes Bild
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = 5
        self.dx = 0 # Bewegungsdelta x
        self.dy = 0 # Bewegungsdelta y
        # Trackt die tatsächliche Position als float für potenziell geschmeidigere Bewegung
        # obwohl die Zelda-Kamera oft eher Grid-basiert ist.
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)

        # Verhindert, dass der Spieler direkt nach einem Screenwechsel wieder zurückwechselt
        self._prevent_exit_timer = 0
        self._prevent_exit_duration = 5 # Frames


    def update(self, keys, screen_bounds_rect):
        self.dx = 0
        self.dy = 0

        if self._prevent_exit_timer > 0:
            self._prevent_exit_timer -= 1
            # Während des Timers keine Bewegung erlauben, die aus dem Screen führt
            # (Dies ist eine einfache Implementierung, könnte verfeinert werden)
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.dx = -self.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.dx = self.speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.dy = -self.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.dy = self.speed

            # Diagonalbewegung normalisieren (optional, aber üblich)
            if self.dx != 0 and self.dy != 0:
                self.dx *= 0.7071 # ca. 1/sqrt(2)
                self.dy *= 0.7071

        # Neue Position berechnen
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        # Vorausschauendes Rechteck für Kollisionsprüfung mit Bildschirmgrenzen
        predicted_rect = self.rect.copy()
        predicted_rect.center = (new_x, new_y)

        # Spieler an die Grenzen des *aktuellen Kamera-Bildschirms* binden
        # Wir prüfen, ob die *nächste* Position innerhalb der Grenzen liegt
        # Wichtig für den Zelda-Kamera-Effekt: Der Spieler stoppt am Rand.
        if screen_bounds_rect.contains(predicted_rect):
             self.x = new_x
             self.y = new_y
        else:
            # Wenn nicht ganz drin, versuche nur X oder nur Y Bewegung
            # Nur X bewegen
            predicted_rect.center = (new_x, self.y)
            if screen_bounds_rect.contains(predicted_rect):
                self.x = new_x
            # Nur Y bewegen
            predicted_rect.center = (self.x, new_y)
            if screen_bounds_rect.contains(predicted_rect):
                self.y = new_y

            # Falls immer noch nicht drin (in einer Ecke feststeckt), bleibt die Position gleich.


        # Aktualisiere das Rect des Sprites basierend auf der Float-Position
        self.rect.center = (int(self.x), int(self.y))

    def prevent_immediate_exit(self):
        """Startet einen kurzen Timer, um zu verhindern, dass der Spieler
           sofort wieder den Bildschirm wechselt."""
        self._prevent_exit_timer = self._prevent_exit_duration

    def set_position(self, x, y):
        """Setzt die Position des Spielers direkt (nützlich nach Screenwechsel)."""
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))