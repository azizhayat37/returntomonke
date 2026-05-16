import pygame
from player import Player
from cabbage import Farmer, Cabbage

_BG          = (  8,   8,  36)
_GIRDER      = (100, 148, 220)
_GIRDER2     = ( 60,  96, 168)
_GIRDER3     = ( 40,  68, 136)
_RIVET       = (200, 220, 255)
_BEAM        = ( 18,  24,  60)
_LADDER_RAIL = (200, 168,  80)
_LADDER_RUNG = (160, 128,  48)
_HUD         = ( 80,  80, 120)
_FLASH       = (240,  60,  60)   # death flash tint


class Platform:
    def __init__(self, x, y, width):
        self.x     = x
        self.y     = y
        self.width = width


class Ladder:
    def __init__(self, x, y_top, y_bottom):
        self.x        = x
        self.y_top    = y_top
        self.y_bottom = y_bottom


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


# (x_left, y_top, width)
_FLOOR_DATA = [
    (  8, 195, 240),
    (  8, 157, 200),
    ( 48, 119, 200),
    (  8,  81, 200),
]

# (x_centre, y_top, y_bottom)
_LADDER_DATA = [
    (180, 157, 195),
    ( 60, 119, 157),
    (190,  81, 119),
]

_FARMER_X = 25
_FARMER_Y = 81   # stands on floor 4


class GameScene:
    def __init__(self):
        self.platforms = [Platform(*d) for d in _FLOOR_DATA]
        self.ladders   = [Ladder(*d)   for d in _LADDER_DATA]
        self.player    = Player(40.0, 195.0)
        self.farmer    = Farmer(_FARMER_X, _FARMER_Y)
        self.cabbages  = []
        self.hud_font  = pygame.font.Font(None, 10)
        self.flash     = 0.0   # seconds remaining for death flash

    def _respawn_player(self):
        self.player.x  = 40.0
        self.player.y  = 195.0
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.on_ground  = False
        self.player.on_ladder  = False
        self.flash = 0.4

    def update(self, events, dt):
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "menu"

        self.player.update(dt, self.platforms, self.ladders)

        # Farmer throws a cabbage
        new_cab = self.farmer.update(dt)
        if new_cab:
            self.cabbages.append(new_cab)

        # Update cabbages + cull dead ones
        for cab in self.cabbages:
            cab.update(dt, self.platforms)
        self.cabbages = [c for c in self.cabbages if c.alive]

        # Collision: cabbage hits player
        if self.flash <= 0:
            for cab in self.cabbages:
                if cab.hits(self.player.x, self.player.y):
                    self._respawn_player()
                    self.cabbages.clear()
                    break

        self.flash = max(0.0, self.flash - dt)
        return None

    def draw(self, surf):
        surf.fill(_BG)

        # Vertical support beams
        for bx in (8, 128, 248):
            pygame.draw.rect(surf, _BEAM, (bx - 2, 81, 4, 118))

        # Ladders behind girders
        for ladder in self.ladders:
            _draw_ladder(surf, ladder)

        for p in self.platforms:
            _draw_girder(surf, p.x, p.y, p.width)

        # Farmer
        self.farmer.draw(surf)

        # Cabbages
        for cab in self.cabbages:
            cab.draw(surf)

        # Player
        self.player.draw(surf)

        # Death flash overlay
        if self.flash > 0:
            alpha = int(180 * (self.flash / 0.4))
            overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            overlay.fill((*_FLASH, alpha))
            surf.blit(overlay, (0, 0))

        hint = self.hud_font.render("ARROWS/WASD  SPACE=JUMP  ESC=MENU", False, _HUD)
        surf.blit(hint, (4, 3))
