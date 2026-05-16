import pygame
from player import Player

_BG           = (  8,   8,  36)
_GIRDER       = (100, 148, 220)
_GIRDER2      = ( 60,  96, 168)
_GIRDER3      = ( 40,  68, 136)
_RIVET        = (200, 220, 255)
_BEAM         = ( 18,  24,  60)
_LADDER_RAIL  = (200, 168,  80)
_LADDER_RUNG  = (160, 128,  48)
_HUD          = ( 80,  80, 120)


class Platform:
    def __init__(self, x, y, width):
        self.x     = x
        self.y     = y       # top surface — player stands here
        self.width = width


class Ladder:
    def __init__(self, x, y_top, y_bottom):
        self.x        = x
        self.y_top    = y_top     # upper floor level
        self.y_bottom = y_bottom  # lower floor level


def _draw_girder(surf, x, y, w):
    pygame.draw.rect(surf, _GIRDER2, (x, y,     w, 4))
    pygame.draw.rect(surf, _GIRDER,  (x, y,     w, 2))
    pygame.draw.line(surf, _GIRDER3, (x, y + 3), (x + w, y + 3), 1)
    for rx in range(x + 8, x + w - 4, 14):
        pygame.draw.circle(surf, _RIVET,   (rx, y + 2), 2)
        pygame.draw.circle(surf, _GIRDER2, (rx, y + 2), 1)


def _draw_ladder(surf, ladder):
    lx, yt, yb = ladder.x, ladder.y_top, ladder.y_bottom
    pygame.draw.line(surf, _LADDER_RAIL, (lx - 3, yt), (lx - 3, yb), 1)
    pygame.draw.line(surf, _LADDER_RAIL, (lx + 3, yt), (lx + 3, yb), 1)
    for ry in range(yt + 2, yb, 4):
        pygame.draw.line(surf, _LADDER_RUNG, (lx - 2, ry), (lx + 2, ry), 1)


# (x_left, y_top, width) — 4 floors, 38 px apart
_FLOOR_DATA = [
    (  8, 195, 240),   # floor 1  ground
    (  8, 157, 200),   # floor 2
    ( 48, 119, 200),   # floor 3
    (  8,  81, 200),   # floor 4  top
]

# (x_center, y_top, y_bottom) — zigzag path up the level
_LADDER_DATA = [
    (180, 157, 195),   # floor 1 → floor 2  (right side)
    ( 60, 119, 157),   # floor 2 → floor 3  (left side)
    (190,  81, 119),   # floor 3 → floor 4  (right side)
]


class GameScene:
    def __init__(self):
        self.platforms = [Platform(*d) for d in _FLOOR_DATA]
        self.ladders   = [Ladder(*d)   for d in _LADDER_DATA]
        self.player    = Player(40.0, 195.0)
        self.hud_font  = pygame.font.Font(None, 10)

    def update(self, events, dt):
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "menu"
        self.player.update(dt, self.platforms, self.ladders)
        return None

    def draw(self, surf):
        surf.fill(_BG)

        # Vertical support beams
        for bx in (8, 128, 248):
            pygame.draw.rect(surf, _BEAM, (bx - 2, 81, 4, 118))

        # Ladders drawn first so girders overlap their ends
        for ladder in self.ladders:
            _draw_ladder(surf, ladder)

        for p in self.platforms:
            _draw_girder(surf, p.x, p.y, p.width)

        self.player.draw(surf)

        hint = self.hud_font.render("ARROWS/WASD  SPACE=JUMP  ESC=MENU", False, _HUD)
        surf.blit(hint, (4, 3))
