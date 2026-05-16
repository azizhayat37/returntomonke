import colorsys
import math
import random

import pygame

SNES_W, SNES_H = 256, 224
SCALE = 3

# Palette
BG     = (  4,   4,  20)
BLACK  = (  0,   0,   0)
WHITE  = (248, 248, 248)
BROWN  = (112,  56,  16)
TAN    = (192, 136,  80)
CREAM  = (224, 192, 144)
EYE_W  = (240, 240, 248)
EYE_K  = (  8,   8,   8)
BAND   = (208, 168,  96)
GOLD   = (248, 200,   0)
ORANGE = (248, 112,   0)
CYAN   = (  0, 200, 232)
DIM    = ( 72,  72, 120)
BTN_BG = ( 16,  16,  64)
BTN_ON = ( 56,  56, 180)
BTN_BD = (144, 144, 220)

_rng   = random.Random(42)
_STARS = [
    (_rng.randint(0, SNES_W - 1), _rng.randint(0, SNES_H - 1), _rng.choice([1, 1, 1, 2]))
    for _ in range(80)
]


def _hue(tick, speed=0.004, s=0.9, v=1.0):
    r, g, b = colorsys.hsv_to_rgb((tick * speed) % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def _blit_cx(surf, img, y):
    surf.blit(img, (SNES_W // 2 - img.get_width() // 2, y))


def _draw_monke_face(surf, cx, cy):
    pygame.draw.ellipse(surf, BROWN, (cx - 12, cy - 11, 24, 22))
    pygame.draw.ellipse(surf, TAN,   (cx - 10, cy -  9, 20, 18))
    for sx in (-1, 1):
        ex = cx + sx * 13
        pygame.draw.ellipse(surf, BROWN, (ex - 4, cy - 5, 8, 8))
        pygame.draw.ellipse(surf, TAN,   (ex - 3, cy - 4, 6, 6))
    for ex in (cx - 6, cx + 2):
        pygame.draw.rect(surf, EYE_W, (ex,     cy - 6, 4, 4))
        pygame.draw.rect(surf, EYE_K, (ex + 1, cy - 5, 2, 2))
    pygame.draw.ellipse(surf, CREAM, (cx - 7, cy + 2, 14,  9))
    pygame.draw.rect(surf, BROWN, (cx - 3, cy + 5, 2, 2))
    pygame.draw.rect(surf, BROWN, (cx + 1, cy + 5, 2, 2))


def _draw_barrel(surf, cx, cy):
    inner = (min(255, BROWN[0]+24), min(255, BROWN[1]+16), min(255, BROWN[2]+8))
    pygame.draw.ellipse(surf, BROWN, (cx -  9, cy - 8, 18, 16))
    pygame.draw.ellipse(surf, inner, (cx -  7, cy - 6, 14, 12))
    for by in (cy - 3, cy + 1, cy + 5):
        pygame.draw.line(surf, BAND, (cx - 8, by), (cx + 8, by), 1)


def _draw_button(surf, rect, label, active, f_med, f_sm):
    pygame.draw.rect(surf, BTN_ON if active else BTN_BG, rect)
    pygame.draw.rect(surf, BTN_BD if active else (40, 40, 100), rect, 1)
    col = GOLD if active else (140, 140, 190)
    t = f_med.render(label, False, col)
    surf.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
    if active:
        cur = f_sm.render(">", False, GOLD)
        surf.blit(cur, (rect.left - 8, rect.centery - cur.get_height() // 2))


class MenuScene:
    def __init__(self):
        self.tick = 0
        self.sel  = 0
        self.f_big = pygame.font.Font(None, 22)
        self.f_med = pygame.font.Font(None, 14)
        self.f_sm  = pygame.font.Font(None, 10)
        self.btn_start = pygame.Rect(SNES_W // 2 - 44, 148, 88, 16)
        self.btn_about = pygame.Rect(SNES_W // 2 - 44, 170, 88, 16)
        self.buttons   = [self.btn_start, self.btn_about]
        self.labels    = ["START GAME", "ABOUT"]

    def update(self, events, dt):
        self.tick += 1
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.sel = 0
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = 1
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "start" if self.sel == 0 else "about"
                elif ev.key == pygame.K_ESCAPE:
                    import sys, pygame as pg
                    pg.quit(); __import__('sys').exit()
            if ev.type == pygame.MOUSEMOTION:
                mx, my = ev.pos[0] // SCALE, ev.pos[1] // SCALE
                for i, r in enumerate(self.buttons):
                    if r.collidepoint(mx, my):
                        self.sel = i
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos[0] // SCALE, ev.pos[1] // SCALE
                for i, r in enumerate(self.buttons):
                    if r.collidepoint(mx, my):
                        self.sel = i
                        return "start" if i == 0 else "about"
        return None

    def draw(self, surf):
        t = self.tick
        surf.fill(BG)

        # Gradient sky (top 50px)
        for gy in range(50):
            v = int(gy * 0.7)
            pygame.draw.line(surf, (4 + v, 4 + v, 20 + v * 2), (0, gy), (SNES_W, gy))

        # Stars
        for sx, sy, sz in _STARS:
            tw = 80 + int(175 * abs(math.sin(t * 0.03 + sx * 0.27)))
            pygame.draw.rect(surf, (tw, tw, min(255, tw + 30)), (sx, sy, sz, sz))

        # "RETURN TO"
        _blit_cx(surf, self.f_med.render("RETURN TO", False, CYAN), 30)

        # "MONKE" — rainbow, with shadow
        _blit_cx(surf, self.f_big.render("MONKE", False, (24, 12, 0)), 47)
        _blit_cx(surf, self.f_big.render("MONKE", False, _hue(t)), 46)

        # Divider
        lx = SNES_W // 2
        pygame.draw.line(surf, GOLD,   (lx - 68, 67), (lx + 68, 67), 1)
        pygame.draw.line(surf, ORANGE, (lx - 60, 69), (lx + 60, 69), 1)

        # Monke face (bobs up and down)
        bob = int(math.sin(t * 0.06) * 1.5)
        _draw_monke_face(surf, SNES_W // 2, 100 + bob)

        # Barrels
        _draw_barrel(surf, 44,            104)
        _draw_barrel(surf, SNES_W - 44,   104)

        # Nav hint (blinks)
        if (t // 25) % 2 == 0:
            _blit_cx(surf, self.f_sm.render("UP / DOWN  OR  MOUSE  TO  NAVIGATE", False, DIM), 137)

        # Buttons
        for i, (r, lbl) in enumerate(zip(self.buttons, self.labels)):
            _draw_button(surf, r, lbl, self.sel == i, self.f_med, self.f_sm)

        # Copyright
        _blit_cx(surf, self.f_sm.render("(C) 2024  RETURN TO MONKE", False, (44, 44, 84)), 213)
