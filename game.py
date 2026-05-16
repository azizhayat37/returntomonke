import pygame
from player import Player

_BG      = ( 8,   8,  36)   # dark midnight blue
_GIRDER  = (100, 148, 220)  # steel top highlight
_GIRDER2 = ( 60,  96, 168)  # steel body
_GIRDER3 = ( 40,  68, 136)  # steel bottom shadow
_RIVET   = (200, 220, 255)
_BEAM    = ( 18,  24,  60)  # vertical support columns
_HUD     = ( 80,  80, 120)


class Platform:
    def __init__(self, x, y, width):
        self.x     = x
        self.y     = y       # top surface — player stands here
        self.width = width


def _draw_girder(surf, x, y, w):
    pygame.draw.rect(surf, _GIRDER2, (x,     y,     w, 4))
    pygame.draw.rect(surf, _GIRDER,  (x,     y,     w, 2))   # top highlight
    pygame.draw.line(surf, _GIRDER3, (x,     y + 3), (x + w, y + 3), 1)  # shadow
    for rx in range(x + 8, x + w - 4, 14):
        pygame.draw.circle(surf, _RIVET,   (rx, y + 2), 2)
        pygame.draw.circle(surf, _GIRDER2, (rx, y + 2), 1)


# Platform layout: (x_left, y_top, width) — 4 floors, 38px apart
_FLOOR_DATA = [
    (  8, 195, 240),   # floor 1  ground
    (  8, 157, 200),   # floor 2
    ( 48, 119, 200),   # floor 3
    (  8,  81, 200),   # floor 4  top
]


class GameScene:
    def __init__(self):
        self.platforms = [Platform(*d) for d in _FLOOR_DATA]
        self.player    = Player(40.0, 195.0)
        self.hud_font  = pygame.font.Font(None, 10)

    def update(self, events, dt):
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "menu"
        self.player.update(dt, self.platforms)
        return None

    def draw(self, surf):
        surf.fill(_BG)

        # Vertical support beams (spanning floor 4 → floor 1)
        for bx in (8, 128, 248):
            pygame.draw.rect(surf, _BEAM, (bx - 2, 81, 4, 118))

        for p in self.platforms:
            _draw_girder(surf, p.x, p.y, p.width)

        self.player.draw(surf)

        hint = self.hud_font.render("ARROWS/WASD  SPACE=JUMP  ESC=MENU", False, _HUD)
        surf.blit(hint, (4, 3))
