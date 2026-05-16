import random

import pygame

from player import Player
from cabbage import Farmer, Cabbage

LEVEL_H = 512
SNES_W  = 256
SNES_H  = 224

_BG          = (  8,   8,  36)
_GIRDER      = (100, 148, 220)
_GIRDER2     = ( 60,  96, 168)
_GIRDER3     = ( 40,  68, 136)
_RIVET       = (200, 220, 255)
_BEAM        = ( 18,  24,  60)
_LADDER_RAIL = (200, 168,  80)
_LADDER_RUNG = (160, 128,  48)
_HUD         = ( 80,  80, 120)
_FLASH       = (240,  60,  60)

# Fixed floor Y positions — spacing kept at 56 px so jump feel stays consistent
_FLOOR_YS = (480, 424, 368, 312, 256, 200, 144, 88)
_MARGIN   = 8
_FARMER_X = 18   # always on top floor, far left


# ── Procedural level generator ────────────────────────────────────────────────

def _generate_level(rng):
    """Return (platforms, ladders) as lists of constructor-arg tuples."""

    W = SNES_W
    M = _MARGIN

    def rand_sections(i):
        """Random (x, w) sections for floor index i."""
        if i == 0:                        # ground — always full width
            return [(M, W - 2 * M)]
        if i == len(_FLOOR_YS) - 1:      # top — wide enough for farmer
            return [(M, 200)]

        choice = rng.randint(0, 4)
        if choice <= 1:                   # 40 % full
            return [(M, W - 2 * M)]
        elif choice == 2:                 # 20 % left-heavy
            w = rng.randint(110, 185)
            return [(M, w)]
        elif choice == 3:                 # 20 % right-heavy
            w = rng.randint(110, 185)
            return [(W - M - w, w)]
        else:                             # 20 % split (two sections + gap)
            gap = rng.randint(24, 44)
            lw  = rng.randint(80, 110)
            rx  = M + lw + gap
            rw  = W - M - rx
            if rw >= 70:
                return [(M, lw), (rx, rw)]
            return [(M, W - 2 * M)]       # fallback to full

    def has_overlap(sA, sB, edge=8):
        """True if any pair of sections overlaps by > edge*2 px."""
        for ax, aw in sA:
            for bx, bw in sB:
                if min(ax + aw, bx + bw) - max(ax, bx) > edge * 2:
                    return True
        return False

    # Generate sections bottom-to-top; re-roll up to 8× if no overlap
    sections = []
    for i in range(len(_FLOOR_YS)):
        for _ in range(8):
            cand = rand_sections(i)
            if i == 0 or has_overlap(sections[-1], cand):
                sections.append(cand)
                break
        else:
            sections.append([(M, W - 2 * M)])   # safe fallback

    # Platforms
    platforms = [
        (x, _FLOOR_YS[i], w)
        for i, secs in enumerate(sections)
        for x, w in secs
    ]

    # Ladders — 1-2 per adjacent floor pair, placed within overlapping areas
    ladders = []
    for i in range(len(_FLOOR_YS) - 1):
        fy_lo, fy_hi = _FLOOR_YS[i], _FLOOR_YS[i + 1]

        valid = []
        for ax, aw in sections[i]:
            for bx, bw in sections[i + 1]:
                il = max(ax, bx) + 8
                ir = min(ax + aw, bx + bw) - 8
                if ir - il >= 8:
                    valid.append((il, ir))

        if not valid:
            continue   # floor unreachable — shouldn't happen after overlap check

        n_target = rng.randint(1, min(2, len(valid) + 1))
        placed   = []
        for _ in range(30):
            lo, hi = rng.choice(valid)
            lx = rng.randint(lo, hi)
            if all(abs(lx - p) > 22 for p in placed):
                ladders.append((lx, fy_hi, fy_lo))
                placed.append(lx)
            if len(placed) >= n_target:
                break

        if not placed:   # guarantee at least one
            lo, hi = valid[0]
            ladders.append(((lo + hi) // 2, fy_hi, fy_lo))

    return platforms, ladders


# ── Draw helpers ──────────────────────────────────────────────────────────────

def _draw_girder(surf, x, y, w):
    pygame.draw.rect(surf, _GIRDER2, (x, y,     w, 4))
    pygame.draw.rect(surf, _GIRDER,  (x, y,     w, 2))
    pygame.draw.line(surf, _GIRDER3, (x, y + 3), (x + w, y + 3), 1)
    for rx in range(x + 8, x + w - 4, 14):
        pygame.draw.circle(surf, _RIVET,   (rx, y + 2), 2)
        pygame.draw.circle(surf, _GIRDER2, (rx, y + 2), 1)


def _draw_ladder(surf, lx, yt, yb):
    pygame.draw.line(surf, _LADDER_RAIL, (lx - 3, yt), (lx - 3, yb), 1)
    pygame.draw.line(surf, _LADDER_RAIL, (lx + 3, yt), (lx + 3, yb), 1)
    for ry in range(yt + 2, yb, 4):
        pygame.draw.line(surf, _LADDER_RUNG, (lx - 2, ry), (lx + 2, ry), 1)


# ── Data classes ──────────────────────────────────────────────────────────────

class Platform:
    def __init__(self, x, y, width):
        self.x, self.y, self.width = x, y, width


class Ladder:
    def __init__(self, x, y_top, y_bottom):
        self.x, self.y_top, self.y_bottom = x, y_top, y_bottom


# ── Scene ─────────────────────────────────────────────────────────────────────

class GameScene:
    def __init__(self):
        plat_data, ladd_data = _generate_level(random.Random())
        self.platforms = [Platform(*d) for d in plat_data]
        self.ladders   = [Ladder(*d)   for d in ladd_data]
        self.player    = Player(40.0, float(_FLOOR_YS[0]))
        self.farmer    = Farmer(_FARMER_X, _FLOOR_YS[-1])
        self.cabbages  = []
        self.cam_y     = float(LEVEL_H - SNES_H)
        self.flash     = 0.0
        self.hud_font  = pygame.font.Font(None, 10)

    def _respawn(self):
        self.player.x  = 40.0
        self.player.y  = float(_FLOOR_YS[0])
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.on_ground = False
        self.player.on_ladder = False
        self.cabbages.clear()
        self.flash = 0.4

    def update(self, events, dt):
        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "menu"

        self.player.update(dt, self.platforms, self.ladders)

        if self.player.y > LEVEL_H + 30:
            self._respawn()

        cab = self.farmer.update(dt)
        if cab:
            self.cabbages.append(cab)

        for c in self.cabbages:
            c.update(dt, self.platforms)
        self.cabbages = [c for c in self.cabbages if c.alive]

        if self.flash <= 0:
            for c in self.cabbages:
                if c.hits(self.player.x, self.player.y):
                    self._respawn()
                    break

        self.flash = max(0.0, self.flash - dt)

        target    = self.player.y - SNES_H * 0.65
        self.cam_y += (target - self.cam_y) * min(1.0, dt * 6)
        self.cam_y  = max(0.0, min(float(LEVEL_H - SNES_H), self.cam_y))

        return None

    def draw(self, surf):
        icy = round(self.cam_y)
        surf.fill(_BG)

        beam_top = _FLOOR_YS[-1] - icy
        beam_h   = _FLOOR_YS[0] - _FLOOR_YS[-1]
        for bx in (8, 128, 248):
            pygame.draw.rect(surf, _BEAM, (bx - 2, beam_top, 4, beam_h))

        for ld in self.ladders:
            _draw_ladder(surf, ld.x, ld.y_top - icy, ld.y_bottom - icy)

        for p in self.platforms:
            _draw_girder(surf, p.x, p.y - icy, p.width)

        self.farmer.draw(surf, icy)

        for c in self.cabbages:
            c.draw(surf, icy)

        self.player.draw(surf, icy)

        if self.flash > 0:
            alpha = int(180 * (self.flash / 0.4))
            ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            ov.fill((*_FLASH, alpha))
            surf.blit(ov, (0, 0))

        surf.blit(
            self.hud_font.render("ARROWS/WASD  SPACE=JUMP  ESC=MENU", False, _HUD),
            (4, 3),
        )
