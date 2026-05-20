import math
import random

import pygame

from player import Player
from cabbage import Farmer, Cabbage, ROLL_SPEED

LEVEL_H  = 640
WORLD_W  = 320
SNES_W   = 320
SNES_H   = 240
MAX_LIVES = 3
_BG_H    = SNES_H + round((LEVEL_H - SNES_H) * 0.2)  # 320 — tall enough for parallax scroll

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

_SPIKE_COL   = (180, 180, 210)
_SPIKE_SHAD  = ( 80,  80, 120)
_FIRE_CORE   = (255, 240, 120)
_FIRE_MID    = (255, 140,   0)
_FIRE_OUT    = (200,  40,   0)
_SPRING_A    = (200, 220, 255)
_SPRING_B    = (100, 160, 255)
_MOVING_TOP  = (100, 210, 120)
_MOVING_DARK = ( 40, 120,  60)
_MOVING_RIV  = (180, 240, 200)

_FLOOR_YS = (624, 568, 512, 456, 400, 344, 288, 232, 176, 120, 64)
_MARGIN   = 8
_FARMER_X = 18


# ── Trap entity classes ───────────────────────────────────────────────────────

class MovingPlatform:
    def __init__(self, x, y, width, travel, speed):
        self.origin_x = float(x)
        self.x        = float(x)
        self.y        = y
        self.width    = width
        self.travel   = travel
        self.speed    = speed
        self._t       = 0.0
        self.prev_x   = float(x)

    def update(self, dt):
        self.prev_x = self.x
        self._t    += dt * self.speed
        self.x      = self.origin_x + math.sin(self._t) * self.travel

    @property
    def dx(self):
        return self.x - self.prev_x


class SpringPad:
    LAUNCH_VEL = -260
    W = 12

    def __init__(self, x, y):
        self.x    = float(x)
        self.y    = float(y)
        self.anim = 0.0

    def trigger(self):
        self.anim = 0.35

    def update(self, dt):
        self.anim = max(0.0, self.anim - dt * 3)

    def draw(self, surf, cam_y):
        cx   = round(self.x + self.W // 2)
        base = round(self.y) - cam_y
        comp = round(self.anim * 6)
        coil_h = max(2, 8 - comp)
        step   = max(1, coil_h // 3)
        for i in range(3):
            ly = base - i * step - 1
            dx = 3 if i % 2 == 0 else -3
            pygame.draw.line(surf, _SPRING_A, (cx - 3, ly), (cx + dx, ly - step), 1)
        pygame.draw.rect(surf, _SPRING_B, (round(self.x), base - 1, self.W, 2))


class Spike:
    W_PER = 6

    def __init__(self, x, y, count):
        self.x     = float(x)
        self.y     = float(y)
        self.count = count

    def hits(self, px, py, prev_py=None):
        if not (self.x - 4 <= px <= self.x + self.count * self.W_PER + 4):
            return False
        # Swept: did the player cross the spike level this frame?
        if prev_py is not None and prev_py < self.y:
            return py >= self.y
        return abs(py - self.y) < 8

    def draw(self, surf, cam_y):
        base = round(self.y) - cam_y
        for i in range(self.count):
            tx = round(self.x) + i * self.W_PER
            for h in range(7):
                w  = max(1, self.W_PER - 2 - h)
                ox = (self.W_PER - w) // 2
                col = _SPIKE_COL if h < 5 else _SPIKE_SHAD
                pygame.draw.rect(surf, col, (tx + ox, base - h - 1, w, 1))


class FireJet:
    def __init__(self, x, y, period, phase):
        self.x       = float(x)
        self.y       = float(y)
        self.period  = period
        self._t      = phase
        self.active  = False
        self._on_dur = period * 0.3

    def update(self, dt):
        self._t    = (self._t + dt) % self.period
        self.active = self._t < self._on_dur

    def hits(self, px, py):
        return self.active and abs(px - self.x) < 6 and (self.y - 22) <= py <= self.y

    def draw(self, surf, cam_y, tick):
        base = round(self.y) - cam_y
        pygame.draw.rect(surf, (80, 50, 30), (round(self.x) - 3, base - 2, 6, 2))
        if self.active:
            height = int(16 + math.sin(tick * 0.22) * 4)
            for h in range(height):
                t   = h / max(1, height)
                flk = int(math.sin(tick * 0.35 + h * 0.7) * 1)
                w   = max(1, int((1.0 - t * 0.6) * 5))
                col = _FIRE_CORE if t < 0.25 else (_FIRE_MID if t < 0.6 else _FIRE_OUT)
                pygame.draw.rect(surf, col, (round(self.x) - w//2 + flk, base - h - 1, w, 1))


# ── Procedural level generator ────────────────────────────────────────────────

def _generate_level(rng):
    W = WORLD_W
    M = _MARGIN

    def rand_sections(i):
        if i == len(_FLOOR_YS) - 1:
            # Top floor: wide left section only (farmer stands here)
            return [(M, 200)]

        if i == 0:
            # Ground floor: always split so cabbages can fall through
            gap   = rng.randint(20, 40)
            lw    = rng.randint(80, 130)
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
            w = rng.randint(210, 270)
            return [(M, w)]
        elif choice == 2:
            w = rng.randint(140, 230)
            return [(M, w)]
        elif choice == 3:
            w = rng.randint(140, 230)
            return [(W - M - w, w)]
        else:
            gap = rng.randint(30, 55)
            lw  = rng.randint(80, 110)
            rx  = M + lw + gap
            mw  = rng.randint(60, 90)
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

    return platforms, sections, ladders


def _generate_traps(rng, sections):
    moving_data = []
    spring_data = []
    spike_data  = []
    jet_data    = []

    for i, (fy, secs) in enumerate(zip(_FLOOR_YS, sections)):
        if i == 0 or i == len(_FLOOR_YS) - 1:
            continue

        # Moving platforms in wide gaps
        for j in range(len(secs) - 1):
            ax, aw = secs[j]
            bx, _  = secs[j + 1]
            gap_x  = ax + aw
            gap_w  = bx - gap_x
            if gap_w >= 52 and rng.random() < 0.4:
                pw     = rng.randint(30, min(44, gap_w - 12))
                travel = (gap_w - pw) // 2 - 2
                if travel >= 6:
                    mid = gap_x + (gap_w - pw) // 2
                    spd = rng.uniform(0.9, 2.2)
                    moving_data.append((mid, fy, pw, travel, spd))

        # Spring pads
        if rng.random() < 0.35:
            sec = rng.choice(secs)
            sx, sw = sec
            if sw >= 28:
                px = rng.randint(sx + 6, sx + sw - 18)
                spring_data.append((px, fy))

        # Spikes in gaps
        for j in range(len(secs) - 1):
            ax, aw = secs[j]
            bx, _  = secs[j + 1]
            gap_x  = ax + aw
            gap_w  = bx - gap_x
            if gap_w >= 10 and rng.random() < 0.45:
                count = max(1, min(4, gap_w // 6))
                sx    = gap_x + (gap_w - count * 6) // 2
                spike_data.append((sx, fy, count))

        # Fire jets — more common on higher floors
        jet_chance = 0.2 + (i / len(_FLOOR_YS)) * 0.3
        if i >= 2 and rng.random() < jet_chance:
            sec = rng.choice(secs)
            sx, sw = sec
            jx     = rng.randint(sx + 6, max(sx + 7, sx + sw - 6))
            period = rng.uniform(2.0, 4.5)
            phase  = rng.random() * period
            jet_data.append((jx, fy, period, phase))

    return moving_data, spring_data, spike_data, jet_data


# ── Deep-space background (pre-rendered once at scene init) ───────────────────

def _generate_background(rng, w, h):
    bg = pygame.Surface((w, h))

    # Dark gradient base — deep indigo-black
    for y in range(h):
        t = y / h
        pygame.draw.line(bg, (int(3 + t * 5), int(3 + t * 3), int(16 + t * 10)),
                         (0, y), (w, y))

    # Nebulae — layered ellipses at low alpha for soft cloud look
    neb = pygame.Surface((w, h), pygame.SRCALPHA)
    nebula_defs = [
        (rng.randint(30, w - 30), rng.randint(20, h - 20), 72, 42,  80, 18, 150),  # violet
        (rng.randint(30, w - 30), rng.randint(20, h - 20), 62, 36,  18, 80, 140),  # deep blue
        (rng.randint(30, w - 30), rng.randint(20, h - 20), 58, 32, 140, 28,  70),  # crimson-pink
        (rng.randint(30, w - 30), rng.randint(20, h - 20), 52, 30,  16, 110, 100), # teal
        (rng.randint(30, w - 30), rng.randint(20, h - 20), 68, 40, 110,  55,  18), # amber-orange
    ]
    for nx, ny, rx, ry, nr, ng, nb in nebula_defs:
        for layer in range(7):
            scale = 1.0 - layer * 0.12
            alpha = max(0, int(30 * (1.0 - layer * 0.13)))
            lw = max(4, int(rx * 2 * scale))
            lh = max(4, int(ry * 2 * scale))
            jx = rng.randint(-10, 10)
            jy = rng.randint(-7, 7)
            pygame.draw.ellipse(neb, (nr, ng, nb, alpha),
                                (nx - lw // 2 + jx, ny - lh // 2 + jy, lw, lh))
    bg.blit(neb, (0, 0))

    # Stars — varied colors and sizes
    for _ in range(320):
        sx  = rng.randint(0, w - 1)
        sy  = rng.randint(0, h - 1)
        bri = rng.randint(80, 255)
        roll = rng.random()
        if roll < 0.25:
            col = (max(0, bri - 50), max(0, bri - 20), bri)                        # blue-white
        elif roll < 0.45:
            col = (min(255, bri + 30), min(255, bri + 10), max(0, bri - 50))       # yellow
        elif roll < 0.58:
            col = (min(255, bri + 45), max(0, bri - 70), max(0, bri - 70))         # red giant
        else:
            col = (bri, bri, bri)                                                   # white

        size = rng.choices([1, 1, 1, 2, 2, 3], weights=[40, 40, 40, 15, 15, 5])[0]
        pygame.draw.rect(bg, col, (sx, sy, size, size))

        # Diffraction cross on the brightest single-pixel stars
        if bri > 215 and size == 1 and rng.random() < 0.45:
            arm = (min(255, col[0] // 3), min(255, col[1] // 3), min(255, col[2] // 3))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= sx + dx < w and 0 <= sy + dy < h:
                    pygame.draw.rect(bg, arm, (sx + dx, sy + dy, 1, 1))

    # Two dense star clusters
    for _ in range(2):
        cx = rng.randint(40, w - 40)
        cy = rng.randint(40, h - 40)
        for _ in range(60):
            ang  = rng.random() * math.pi * 2
            dist = rng.random() ** 0.5 * 22
            px   = int(cx + math.cos(ang) * dist)
            py   = int(cy + math.sin(ang) * dist)
            if 0 <= px < w and 0 <= py < h:
                bri2 = rng.randint(140, 255)
                pygame.draw.rect(bg, (bri2, bri2, min(255, bri2 + 55)), (px, py, 1, 1))

    return bg


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


def _draw_moving_girder(surf, x, y, w):
    ix = round(x)
    pygame.draw.rect(surf, _MOVING_DARK, (ix, y,     w, 4))
    pygame.draw.rect(surf, _MOVING_TOP,  (ix, y,     w, 2))
    pygame.draw.line(surf, _MOVING_DARK, (ix, y + 3), (ix + w, y + 3), 1)
    for rx in range(ix + 6, ix + w - 2, 10):
        pygame.draw.circle(surf, _MOVING_RIV,  (rx, y + 2), 2)
        pygame.draw.circle(surf, _MOVING_DARK, (rx, y + 2), 1)


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
        rng = random.Random()
        plat_data, sections, ladd_data = _generate_level(rng)
        mov_data, spr_data, spk_data, jet_data = _generate_traps(rng, sections)

        self.platforms        = [Platform(*d) for d in plat_data]
        self.ladders          = [Ladder(*d)   for d in ladd_data]
        self.moving_platforms = [MovingPlatform(*d) for d in mov_data]
        self.springs          = [SpringPad(*d)      for d in spr_data]
        self.spikes           = [Spike(*d)          for d in spk_data]
        self.fire_jets        = [FireJet(*d)        for d in jet_data]

        self._bg_surf = _generate_background(random.Random(42), WORLD_W, _BG_H)

        self.player   = Player(40.0, float(_FLOOR_YS[0]))
        self.farmer   = Farmer(_FARMER_X, _FLOOR_YS[-1])
        self.cabbages = []
        self.cam_y    = float(LEVEL_H - SNES_H)
        self.flash    = 0.0
        self.lives    = MAX_LIVES
        self.state    = "playing"
        self.result_timer   = 0.0
        self.player_started = False
        self.tick      = 0
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

        self.tick += 1

        # Update moving platforms first
        for mp in self.moving_platforms:
            mp.update(dt)

        # Player update — collision against static + moving platforms combined
        prev_player_y = self.player.y
        all_plats     = self.platforms + self.moving_platforms
        self.player.update(dt, all_plats, self.ladders)

        # Carry player on moving platform
        COLL_HW = 4
        for mp in self.moving_platforms:
            if (self.player.on_ground
                    and self.player.x + COLL_HW > mp.x
                    and self.player.x - COLL_HW < mp.x + mp.width
                    and abs(self.player.y - mp.y) < 3):
                self.player.x = max(COLL_HW + 2.0,
                                    min(float(WORLD_W) - COLL_HW - 2.0,
                                        self.player.x + mp.dx))

        # Spring pads
        for sp in self.springs:
            sp.update(dt)
            if (self.player.on_ground
                    and abs(self.player.x - (sp.x + sp.W // 2)) < sp.W // 2 + 4
                    and abs(self.player.y - sp.y) < 4):
                self.player.vy = SpringPad.LAUNCH_VEL
                self.player.on_ground = False
                sp.trigger()

        # Fire jets
        for fj in self.fire_jets:
            fj.update(dt)

        # Detect first move
        if not self.player_started:
            if abs(self.player.vx) > 0 or self.player.on_ladder or not self.player.on_ground:
                self.player_started = True

        # Fell out of the world
        if self.player.y > LEVEL_H + 30:
            self._respawn()
            if self.state != "playing":
                return None

        # Farmer throws — speed up based on player height
        if self.player_started:
            climb_frac = max(0.0, min(1.0, 1.0 - (self.player.y - _FLOOR_YS[-1]) / (_FLOOR_YS[0] - _FLOOR_YS[-1])))
            self.farmer.throw_interval = max(1.0, 2.5 - climb_frac * 1.4)
            cab = self.farmer.update(dt)
            if cab:
                self.cabbages.append(cab)

        for c in self.cabbages:
            c.update(dt, self.platforms)
        self.cabbages = [c for c in self.cabbages if c.alive]

        # Damage checks
        if self.flash <= 0:
            for c in self.cabbages:
                if c.hits(self.player.x, self.player.y):
                    self._respawn()
                    if self.state != "playing":
                        return None
                    break
            else:
                for s in self.spikes:
                    if s.hits(self.player.x, self.player.y, prev_player_y):
                        self._respawn()
                        if self.state != "playing":
                            return None
                        break
                else:
                    for fj in self.fire_jets:
                        if fj.hits(self.player.x, self.player.y):
                            self._respawn()
                            if self.state != "playing":
                                return None
                            break

        self.flash = max(0.0, self.flash - dt)

        if self._check_win():
            self.state        = "won"
            self.result_timer = 0.5
            return None

        # Camera
        target     = self.player.y - SNES_H * 0.65
        self.cam_y += (target - self.cam_y) * min(1.0, dt * 6)
        self.cam_y  = max(0.0, min(float(LEVEL_H - SNES_H), self.cam_y))

        return None

    def draw(self, surf):
        icy   = round(self.cam_y)
        par_y = round(self.cam_y * 0.2)
        surf.blit(self._bg_surf, (0, 0), pygame.Rect(0, par_y, WORLD_W, SNES_H))

        beam_top = _FLOOR_YS[-1] - icy
        beam_h   = _FLOOR_YS[0] - _FLOOR_YS[-1]
        for bx in (8, 160, 312):
            pygame.draw.rect(surf, _BEAM, (bx - 2, beam_top, 4, beam_h))

        for ld in self.ladders:
            _draw_ladder(surf, ld.x, ld.y_top - icy, ld.y_bottom - icy)

        for p in self.platforms:
            _draw_girder(surf, p.x, p.y - icy, p.width)

        # Moving platforms
        for mp in self.moving_platforms:
            _draw_moving_girder(surf, mp.x, mp.y - icy, mp.width)

        # Spikes
        for s in self.spikes:
            s.draw(surf, icy)

        # Fire jets
        for fj in self.fire_jets:
            fj.draw(surf, icy, self.tick)

        # Spring pads
        for sp in self.springs:
            sp.draw(surf, icy)

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
            headline = "oh no monke ded"
            col      = _LOSE_COL

        t1 = self.big_font.render(headline, False, col)
        surf.blit(t1, (SNES_W // 2 - t1.get_width() // 2, SNES_H // 2 - 20))

        if self.result_timer <= 0:
            t2 = self.med_font.render("PRESS ANY KEY", False, _WHITE)
            surf.blit(t2, (SNES_W // 2 - t2.get_width() // 2, SNES_H // 2 + 10))
