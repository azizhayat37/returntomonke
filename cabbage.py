import math
import pygame

ROLL_SPEED = 40   # canvas px / sec
GRAVITY    = 380
RADIUS     = 5    # collision + draw radius

# Each floor's roll direction once a cabbage lands there
# (floor y_top → direction: +1 right, -1 left)
_FLOOR_DIR = {81: 1, 119: -1, 157: 1, 195: -1}

# ── Palette ───────────────────────────────────────────────────────────────────

_CAB_DARK  = ( 30, 110,  30)
_CAB_MID   = ( 55, 155,  55)
_CAB_LIGHT = ( 85, 195,  85)

_SHIRT  = (215, 210, 188)   # off-white kosovorotka
_DECOR  = (175,  95,  50)   # embroidery stripe
_PANTS  = ( 55,  42,  28)   # baggy dark trousers
_BOOTS  = ( 38,  26,  16)
_SKIN   = (218, 165, 125)   # ruddy complexion
_BEARD  = (155,  82,  32)   # thick reddish beard
_NOSE   = (200, 128,  98)
_EYE    = ( 48,  48,  75)
_HAT    = (110,  78,  48)   # ushanka fur
_HAT_BD = ( 82,  56,  32)   # hat band


# ── Cabbage ───────────────────────────────────────────────────────────────────

class Cabbage:
    def __init__(self, x, y, vx):
        self.x     = float(x)
        self.y     = float(y)    # bottom y
        self.vx    = float(vx)
        self.vy    = 0.0
        self.on_ground = False
        self.angle = 0.0
        self.alive = True

    def update(self, dt, platforms):
        prev_y     = self.y
        prev_on    = self.on_ground
        self.vy    = min(self.vy + GRAVITY * dt, 300)
        self.x    += self.vx * dt
        self.y    += self.vy * dt

        self.on_ground = False
        for p in platforms:
            if (self.x + RADIUS > p.x and self.x - RADIUS < p.x + p.width
                    and prev_y <= p.y and self.y >= p.y and self.vy >= 0):
                self.y     = float(p.y)
                self.vy    = 0.0
                self.on_ground = True
                if not prev_on:   # just landed — set floor-specific direction
                    self.vx = ROLL_SPEED * _FLOOR_DIR.get(p.y, 1)
                break

        self.angle += self.vx * dt * 0.4

        if self.y > 230 or self.x < -20 or self.x > 290:
            self.alive = False

    def hits(self, px, py):
        return abs(self.x - px) < RADIUS + 5 and abs(self.y - py) < RADIUS + 12

    def draw(self, surf):
        cx = round(self.x)
        cy = round(self.y - RADIUS)
        pygame.draw.circle(surf, _CAB_DARK,  (cx, cy), RADIUS)
        pygame.draw.circle(surf, _CAB_MID,   (cx, cy), RADIUS - 1)
        for i in range(4):
            a  = self.angle + i * math.pi / 2
            dx = int(math.cos(a) * (RADIUS - 1))
            dy = int(math.sin(a) * (RADIUS - 1))
            pygame.draw.line(surf, _CAB_DARK, (cx, cy), (cx + dx, cy + dy), 1)
        pygame.draw.circle(surf, _CAB_LIGHT, (cx - 1, cy - 1), 1)


# ── Farmer ────────────────────────────────────────────────────────────────────

class Farmer:
    FIRST_THROW    = 1.5    # delay before first throw (sec)
    THROW_INTERVAL = 3.2    # seconds between throws
    WINDUP_DUR     = 0.45
    THROW_DUR      = 0.25

    def __init__(self, x, y):
        self.x       = x
        self.y       = y     # bottom y (floor 4)
        self.timer   = self.FIRST_THROW
        self.phase   = "idle"
        self.phase_t = 0.0
        self._thrown = False

    def update(self, dt):
        """Returns a new Cabbage instance on throw frame, else None."""
        self.timer -= dt
        spawned = None

        if self.phase == "idle":
            if self.timer <= 0:
                self.phase   = "windup"
                self.phase_t = 0.0
                self._thrown = False

        elif self.phase == "windup":
            self.phase_t += dt
            if self.phase_t >= self.WINDUP_DUR:
                self.phase   = "throw"
                self.phase_t = 0.0

        elif self.phase == "throw":
            self.phase_t += dt
            if not self._thrown and self.phase_t >= 0.05:
                spawned      = Cabbage(self.x + 14, self.y, ROLL_SPEED)
                self._thrown = True
            if self.phase_t >= self.THROW_DUR:
                self.phase = "idle"
                self.timer = self.THROW_INTERVAL

        return spawned

    def draw(self, surf):
        frame = {"idle": 0, "windup": 1, "throw": 2}[self.phase]
        _draw_farmer(surf, self.x, self.y, frame)


def _draw_farmer(surf, cx, by, frame):
    # ── Boots ────────────────────────────────────────────────────────────────
    pygame.draw.rect(surf, _BOOTS, (cx - 7, by - 7,  6, 7))
    pygame.draw.rect(surf, _BOOTS, (cx + 1, by - 7,  6, 7))

    # ── Baggy trousers ───────────────────────────────────────────────────────
    pygame.draw.rect(surf, _PANTS, (cx - 8, by - 15, 16, 9))

    # ── Kosovorotka (side-button shirt) ──────────────────────────────────────
    pygame.draw.rect(surf, _SHIRT, (cx - 7, by - 25, 14, 11))
    pygame.draw.line(surf, _DECOR, (cx,     by - 25), (cx,     by - 20), 1)  # centre seam
    pygame.draw.line(surf, _DECOR, (cx - 7, by - 18), (cx - 4, by - 18), 1)  # cuff stripe

    # ── Arms ─────────────────────────────────────────────────────────────────
    if frame == 0:   # idle — both arms loosely down
        pygame.draw.line(surf, _SHIRT, (cx - 7, by - 23), (cx - 11, by - 17), 3)
        pygame.draw.line(surf, _SHIRT, (cx + 7, by - 23), (cx + 11, by - 17), 3)
    elif frame == 1: # wind-up — right arm raised, cabbage visible in fist
        pygame.draw.line(surf, _SHIRT, (cx - 7, by - 23), (cx - 10, by - 18), 3)
        pygame.draw.line(surf, _SHIRT, (cx + 7, by - 23), (cx + 11, by - 29), 3)
        pygame.draw.circle(surf, _CAB_MID, (cx + 12, by - 30), 4)   # cabbage in hand
        pygame.draw.circle(surf, _CAB_DARK,(cx + 12, by - 30), 4, 1)
    elif frame == 2: # throw — right arm thrust forward
        pygame.draw.line(surf, _SHIRT, (cx - 7, by - 23), (cx - 10, by - 18), 3)
        pygame.draw.line(surf, _SHIRT, (cx + 7, by - 23), (cx + 16, by - 23), 3)

    # ── Face ─────────────────────────────────────────────────────────────────
    pygame.draw.rect(surf, _SKIN,  (cx - 5, by - 32, 10, 8))

    # Bushy brows
    pygame.draw.line(surf, _BEARD, (cx - 5, by - 31), (cx - 1, by - 31), 2)
    pygame.draw.line(surf, _BEARD, (cx + 1, by - 31), (cx + 5, by - 31), 2)

    # Eyes
    pygame.draw.rect(surf, _EYE, (cx - 4, by - 29, 2, 2))
    pygame.draw.rect(surf, _EYE, (cx + 2, by - 29, 2, 2))

    # Big red nose
    pygame.draw.rect(surf, _NOSE, (cx - 1, by - 27, 3, 3))

    # Thick beard + moustache
    pygame.draw.rect(surf, _BEARD, (cx - 5, by - 25, 10, 2))  # moustache
    pygame.draw.rect(surf, _BEARD, (cx - 5, by - 23, 10, 5))  # beard

    # ── Ushanka ───────────────────────────────────────────────────────────────
    pygame.draw.rect(surf, _HAT,   (cx - 7,  by - 40, 14,  6))  # crown
    pygame.draw.rect(surf, _HAT_BD,(cx - 8,  by - 35, 16,  3))  # band
    pygame.draw.rect(surf, _HAT,   (cx - 10, by - 37,  4,  5))  # left ear flap
    pygame.draw.rect(surf, _HAT,   (cx + 6,  by - 37,  4,  5))  # right ear flap
