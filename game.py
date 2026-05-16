import random

import pygame

from player import Player
from cabbage import Farmer, Cabbage, ROLL_SPEED

LEVEL_H  = 512
SNES_W   = 256
SNES_H   = 224
MAX_LIVES = 3

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
_HEART_ON    = (220,  40,  60)
_HEART_OFF   = ( 60,  40,  60)
_OVERLAY_BG  = (  0,   0,   0)
_WIN_COL     = (248, 200,   0)
_LOSE_COL    = (240,  60,  60)
_WHITE       = (240, 240, 248)

_FLOOR_YS = (480, 424, 368, 312, 256, 200, 144, 88)
_MARGIN   = 8
_FARMER_X = 18


# ── Procedural level generator ────────────────────────────────────────────────

def _generate_level(rng):
    W = SNES_W
    M = _MARGIN

    def rand_sections(i):
        if i == len(_FLOOR_YS) - 1:
            # Top floor: wide left section only (farmer stands here)
            return [(M, 200)]

        if i == 0:
            # Ground floor: always split so cabbages can fall through
            gap   = rng.randint(20, 36)
            lw    = rng.randint(50, 90)
            rx    = M + lw + gap
            rw    = W - M - rx
            if rw >= 50:
                return [(M, lw), (rx, rw)]
            # fallback: small right gap
            lw2 = W - 2 * M - 24
            return [(M, lw2)]

        choice = rng.randint(0, 4)
        if choice <= 1:
            # "full" becomes left-heavy to ensure a gap always exists
            w = rng.randint(170, 210)
            return [(M, w)]
        elif choice == 2:
            w = rng.randint(110, 185)
            return [(M, w)]
        elif choice == 3:
            w = rng.randint(110, 185)
            return [(W - M - w, w)]
        else:
            gap = rng.randint(24, 44)
            lw  = rng.randint(80, 110)
            rx  = M + lw + gap
            rw  = W - M - rx
            if rw >= 70:
                return [(M, lw), (rx, rw)]
            return [(M, W - 2 * M - 20)]

    def has_overlap(sA, sB, edge=8):
        for ax, aw in sA:
            for bx, bw in sB:
                if min(ax + aw, bx + bw) - max(ax, bx) > edge * 2:
                    return True
        return False

    sections = []
    for i in range(len(_FLOOR_YS)):
        for _ in range(8):
            cand = rand_sections(i)
            if i == 0 or has_overlap(sections[-1], cand):
                sections.append(cand)
                break
        else:
            sections.append([(M, W - 2 * M - 20)])

    platforms = [
        (x, _FLOOR_YS[i], w)
        for i, secs in enumerate(sections)
        for x, w in secs
    ]

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
            continue

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

        if not placed:
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


def _draw_heart(surf, cx, cy, filled):
    col = _HEART_ON if filled else _HEART_OFF
    pygame.draw.rect(surf, col, (cx - 1, cy,     3, 1))
    pygame.draw.rect(surf, col, (cx - 2, cy + 1, 5, 1))
    pygame.draw.rect(surf, col, (cx - 2, cy + 2, 5, 1))
    pygame.draw.rect(surf, col, (cx - 1, cy + 3, 3, 1))
    pygame.draw.rect(surf, col, (cx,     cy + 4, 1, 1))


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
        self.lives     = MAX_LIVES
        self.state     = "playing"   # "playing" | "won" | "game_over"
        self.result_timer = 0.0      # delay before accepting keypress on overlay
        self.player_started = False
        self.hud_font  = pygame.font.Font(None, 10)
        self.big_font  = pygame.font.Font(None, 28)
        self.med_font  = pygame.font.Font(None, 14)

    def _respawn(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state        = "game_over"
            self.result_timer = 0.5
            return
        self.player.x  = 40.0
        self.player.y  = float(_FLOOR_YS[0])
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.on_ground = False
        self.player.on_ladder = False
        self.cabbages.clear()
        self.flash = 0.4

    def _check_win(self):
        return (abs(self.player.x - self.farmer.x) < 18
                and abs(self.player.y - _FLOOR_YS[-1]) < 8)

    def update(self, events, dt):
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if self.state in ("won", "game_over"):
                    if self.result_timer <= 0:
                        if ev.key == pygame.K_ESCAPE:
                            return "menu"
                        return "menu"
                elif ev.key == pygame.K_ESCAPE:
                    return "menu"

        if self.state != "playing":
            self.result_timer = max(0.0, self.result_timer - dt)
            return None

        self.player.update(dt, self.platforms, self.ladders)

        # Detect first move
        if not self.player_started:
            if (abs(self.player.vx) > 0
                    or self.player.on_ladder
                    or not self.player.on_ground):
                self.player_started = True

        if self.player.y > LEVEL_H + 30:
            self._respawn()
            if self.state != "playing":
                return None

        # Farmer only throws once the monkey starts moving
        if self.player_started:
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
                    if self.state != "playing":
                        return None
                    break

        self.flash = max(0.0, self.flash - dt)

        if self._check_win():
            self.state        = "won"
            self.result_timer = 0.5
            return None

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

        # HUD — controls hint left, hearts right
        surf.blit(
            self.hud_font.render("ARROWS/WASD  SPACE=JUMP", False, _HUD),
            (4, 3),
        )
        for i in range(MAX_LIVES):
            _draw_heart(surf, SNES_W - 10 - i * 9, 3, i < self.lives)

        # Overlay for won / game_over
        if self.state in ("won", "game_over"):
            self._draw_overlay(surf)

    def _draw_overlay(self, surf):
        ov = pygame.Surface((SNES_W, SNES_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        surf.blit(ov, (0, 0))

        if self.state == "won":
            headline = "MONKE WINS!"
            col      = _WIN_COL
        else:
            headline = "GAME OVER"
            col      = _LOSE_COL

        t1 = self.big_font.render(headline, False, col)
        surf.blit(t1, (SNES_W // 2 - t1.get_width() // 2, SNES_H // 2 - 20))

        if self.result_timer <= 0:
            t2 = self.med_font.render("PRESS ANY KEY", False, _WHITE)
            surf.blit(t2, (SNES_W // 2 - t2.get_width() // 2, SNES_H // 2 + 10))
