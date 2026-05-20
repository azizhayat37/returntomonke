import pygame

WALK_SPEED   = 60
JUMP_VEL     = -150
GRAVITY      = 380
MAX_FALL     = 220
CLIMB_SPEED  = 35
COLL_HW      = 4
FRAME_DUR    = 0.15
LADDER_X_TOL = 5
LADDER_Y_TOL = 4

_BROWN = (128,  72,  24)
_TAN   = (192, 140,  80)
_CREAM = (220, 185, 140)
_EYE_W = (240, 240, 248)
_EYE_K = ( 12,  12,  12)

_WALK = [
    (-2,  0,  2,  0),
    (-4,  0,  0, -1),
    (-2,  0,  2,  0),
    ( 0, -1,  4,  0),
]


class Player:
    def __init__(self, x, y):
        self.x  = float(x)
        self.y  = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground    = False
        self.on_ladder    = False
        self.facing_right = True
        self.walk_timer   = 0.0
        self.climb_timer  = 0.0

    def update(self, dt, platforms, ladders):
        keys  = pygame.key.get_pressed()
        up    = keys[pygame.K_UP]    or keys[pygame.K_w]
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump  = keys[pygame.K_SPACE]

        if self.on_ladder:
            self._climb(dt, ladders, up, down, jump)
            return

        if self.on_ground and (up or down):
            for ladder in ladders:
                if abs(self.x - ladder.x) <= LADDER_X_TOL:
                    at_bottom = up   and abs(self.y - ladder.y_bottom) <= LADDER_Y_TOL
                    at_top    = down and abs(self.y - ladder.y_top)    <= LADDER_Y_TOL
                    if at_bottom or at_top:
                        self.on_ladder = True
                        self.x = float(ladder.x)
                        self._climb(dt, ladders, up, down, jump)
                        return

        self.vx = 0.0
        if left:
            self.vx = -WALK_SPEED
            self.facing_right = False
        if right:
            self.vx = WALK_SPEED
            self.facing_right = True

        if jump and self.on_ground:
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
                self.y = float(p.y)
                self.vy = 0.0
                self.on_ground = True

        self.x = max(COLL_HW + 2.0, min(320 - COLL_HW - 2.0, self.x))

        if self.vx != 0 and self.on_ground:
            self.walk_timer += dt
        else:
            self.walk_timer = 0.0

    def _climb(self, dt, ladders, up, down, jump):
        active = None
        for ladder in ladders:
            if abs(self.x - ladder.x) > LADDER_X_TOL:
                continue
            if not (ladder.y_top - 2 <= self.y <= ladder.y_bottom + 2):
                continue
            # Skip a ladder whose tip the player is already standing on —
            # otherwise two stacked ladders at the same X cause an exit loop.
            if up   and self.y <= ladder.y_top    + 1:
                continue
            if down and self.y >= ladder.y_bottom - 1:
                continue
            active = ladder
            break

        if active is None or jump:
            self.on_ladder = False
            if jump:
                self.vy = JUMP_VEL
            return

        self.x  = float(active.x)
        self.vy = 0.0
        if up:
            self.vy = -CLIMB_SPEED
        elif down:
            self.vy = CLIMB_SPEED

        if self.vy != 0:
            self.climb_timer += dt

        self.y += self.vy * dt

        if self.y <= active.y_top:
            self.y = float(active.y_top)
            self.on_ladder = False
            self.on_ground = True
        elif self.y >= active.y_bottom:
            self.y = float(active.y_bottom)
            self.on_ladder = False
            self.on_ground = True

    @property
    def walk_frame(self):
        return int(self.walk_timer / FRAME_DUR) % 4

    @property
    def climb_frame(self):
        return int(self.climb_timer / FRAME_DUR) % 4

    def draw(self, surf, cam_y=0):
        _draw_monke(
            surf,
            round(self.x),
            round(self.y) - cam_y,
            self.facing_right,
            self.walk_frame if (self.on_ground and not self.on_ladder) else 0,
            self.on_ladder,
            self.climb_frame,
        )


def _draw_monke(surf, cx, by, fr, wf, climbing, cf):
    if climbing:
        pygame.draw.line(surf, _BROWN, (cx - 1, by - 5), (cx - 3, by), 2)
        pygame.draw.line(surf, _BROWN, (cx + 1, by - 5), (cx + 3, by), 2)
    else:
        ldx, ldy, rdx, rdy = _WALK[wf]
        if not fr:
            ldx, rdx = -rdx, -ldx
            ldy, rdy = rdy, ldy
        pygame.draw.line(surf, _BROWN, (cx - 1, by - 5), (cx + ldx, by + ldy), 2)
        pygame.draw.line(surf, _BROWN, (cx + 1, by - 5), (cx + rdx, by + rdy), 2)

    pygame.draw.rect(surf, _BROWN, (cx - 4, by - 13, 8, 8))

    if climbing:
        if cf % 2 == 0:
            pygame.draw.line(surf, _BROWN, (cx - 4, by - 12), (cx - 5, by - 18), 2)
            pygame.draw.line(surf, _BROWN, (cx + 4, by - 12), (cx + 6, by -  8), 2)
        else:
            pygame.draw.line(surf, _BROWN, (cx - 4, by - 12), (cx - 6, by -  8), 2)
            pygame.draw.line(surf, _BROWN, (cx + 4, by - 12), (cx + 5, by - 18), 2)
    else:
        pygame.draw.line(surf, _BROWN, (cx - 4, by - 12), (cx - 7, by - 8), 2)
        pygame.draw.line(surf, _BROWN, (cx + 4, by - 12), (cx + 7, by - 8), 2)

    hy = by - 19
    pygame.draw.ellipse(surf, _BROWN, (cx - 6, hy - 4, 12, 10))
    pygame.draw.ellipse(surf, _TAN,   (cx - 5, hy - 3, 10,  8))
    pygame.draw.ellipse(surf, _BROWN, (cx - 9, hy - 3, 5, 5))
    pygame.draw.ellipse(surf, _TAN,   (cx - 8, hy - 2, 3, 3))
    pygame.draw.ellipse(surf, _BROWN, (cx + 4, hy - 3, 5, 5))
    pygame.draw.ellipse(surf, _TAN,   (cx + 5, hy - 2, 3, 3))

    for ex in (cx - 4, cx + 1):
        pygame.draw.rect(surf, _EYE_W, (ex, hy - 1, 3, 3))
        pygame.draw.rect(surf, _EYE_K, (ex + (1 if fr else 0), hy, 1, 1))

    pygame.draw.ellipse(surf, _CREAM, (cx - 3, hy + 2, 6, 4))
    pygame.draw.rect(surf, _BROWN, (cx - 1, hy + 4, 1, 1))
    pygame.draw.rect(surf, _BROWN, (cx + 1, hy + 4, 1, 1))
