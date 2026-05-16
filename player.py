import pygame

WALK_SPEED  = 60    # canvas px / sec
JUMP_VEL    = -150  # canvas px / sec  (negative = up)
GRAVITY     = 380   # canvas px / sec²
MAX_FALL    = 220   # terminal velocity
COLL_HW     = 4     # half-width used for platform collision
FRAME_DUR   = 0.15  # seconds per walk animation frame

_BROWN = (128,  72,  24)
_TAN   = (192, 140,  80)
_CREAM = (220, 185, 140)
_EYE_W = (240, 240, 248)
_EYE_K = ( 12,  12,  12)

# Walk frame foot offsets from centre (cx): (left_dx, left_dy, right_dx, right_dy)
# Defined for facing-right; x-mirrored when facing left.
_WALK = [
    (-2,  0,  2,  0),  # 0 neutral
    (-4,  0,  0, -1),  # 1 stride A
    (-2,  0,  2,  0),  # 2 neutral
    ( 0, -1,  4,  0),  # 3 stride B
]


class Player:
    def __init__(self, x, y):
        self.x  = float(x)
        self.y  = float(y)   # bottom Y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground    = False
        self.facing_right = True
        self.walk_timer   = 0.0

    def update(self, dt, platforms):
        keys = pygame.key.get_pressed()

        self.vx = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.vx = -WALK_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = WALK_SPEED
            self.facing_right = True

        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy = JUMP_VEL
            self.on_ground = False

        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)

        prev_y  = self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        self.on_ground = False
        for p in platforms:
            if (self.x + COLL_HW > p.x and self.x - COLL_HW < p.x + p.width
                    and prev_y <= p.y and self.y >= p.y and self.vy >= 0):
                self.y     = float(p.y)
                self.vy    = 0.0
                self.on_ground = True

        # Horizontal screen bounds
        self.x = max(COLL_HW + 2.0, min(256 - COLL_HW - 2.0, self.x))

        # Fell off bottom — reset to ground floor
        if self.y > 230:
            self.y = float(platforms[0].y)
            self.x = 40.0
            self.vy = 0.0

        if self.vx != 0 and self.on_ground:
            self.walk_timer += dt
        else:
            self.walk_timer = 0.0

    @property
    def walk_frame(self):
        return int(self.walk_timer / FRAME_DUR) % 4

    def draw(self, surf):
        _draw_monke(surf, round(self.x), round(self.y),
                    self.facing_right,
                    self.walk_frame if self.on_ground else 0)


def _draw_monke(surf, cx, by, fr, wf):
    ldx, ldy, rdx, rdy = _WALK[wf]
    if not fr:                          # mirror for left-facing
        ldx, rdx = -rdx, -ldx
        ldy, rdy = rdy, ldy

    # ── Legs ──────────────────────────────────────────────────────────
    pygame.draw.line(surf, _BROWN, (cx - 1, by - 5), (cx + ldx, by + ldy), 2)
    pygame.draw.line(surf, _BROWN, (cx + 1, by - 5), (cx + rdx, by + rdy), 2)

    # ── Body ──────────────────────────────────────────────────────────
    pygame.draw.rect(surf, _BROWN, (cx - 4, by - 13, 8, 8))

    # ── Arms ──────────────────────────────────────────────────────────
    pygame.draw.line(surf, _BROWN, (cx - 4, by - 12), (cx - 7, by - 8), 2)
    pygame.draw.line(surf, _BROWN, (cx + 4, by - 12), (cx + 7, by - 8), 2)

    # ── Head ──────────────────────────────────────────────────────────
    hy = by - 19
    pygame.draw.ellipse(surf, _BROWN, (cx - 6, hy - 4, 12, 10))
    pygame.draw.ellipse(surf, _TAN,   (cx - 5, hy - 3, 10,  8))

    # Ears
    pygame.draw.ellipse(surf, _BROWN, (cx - 9, hy - 3, 5, 5))
    pygame.draw.ellipse(surf, _TAN,   (cx - 8, hy - 2, 3, 3))
    pygame.draw.ellipse(surf, _BROWN, (cx + 4, hy - 3, 5, 5))
    pygame.draw.ellipse(surf, _TAN,   (cx + 5, hy - 2, 3, 3))

    # Both eyes; pupils shift toward facing direction
    for ex in (cx - 4, cx + 1):
        pygame.draw.rect(surf, _EYE_W, (ex, hy - 1, 3, 3))
        pygame.draw.rect(surf, _EYE_K, (ex + (1 if fr else 0), hy, 1, 1))

    # Snout
    pygame.draw.ellipse(surf, _CREAM, (cx - 3, hy + 2, 6, 4))
    pygame.draw.rect(surf, _BROWN, (cx - 1, hy + 4, 1, 1))
    pygame.draw.rect(surf, _BROWN, (cx + 1, hy + 4, 1, 1))
