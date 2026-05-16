import colorsys
import math
import random
import sys

import pygame

# ── Resolution ────────────────────────────────────────────────────────────────
SNES_W, SNES_H = 256, 224
SCALE          = 3
WIN_W, WIN_H   = SNES_W * SCALE, SNES_H * SCALE

# ── Palette ───────────────────────────────────────────────────────────────────
BG     = (4,   4,   20)
BLACK  = (0,   0,   0)
WHITE  = (248, 248, 248)
BROWN  = (112, 56,  16)
TAN    = (192, 136, 80)
CREAM  = (224, 192, 144)
EYE_W  = (240, 240, 248)
EYE_K  = (8,   8,   8)
BAND   = (208, 168, 96)
GOLD   = (248, 200, 0)
ORANGE = (248, 112, 0)
CYAN   = (0,   200, 232)
DIM    = (72,  72,  120)
BTN_BG = (16,  16,  64)
BTN_ON = (56,  56,  180)
BTN_BD = (144, 144, 220)


def _build_scanlines():
    surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    for y in range(SCALE - 1, WIN_H, SCALE):
        pygame.draw.line(surf, (0, 0, 0, 70), (0, y), (WIN_W - 1, y))
    return surf


def _build_stars():
    rng = random.Random(42)
    return [
        (rng.randint(0, SNES_W - 1), rng.randint(0, SNES_H - 1), rng.choice([1, 1, 1, 2]))
        for _ in range(80)
    ]


def hue_color(tick, speed=0.004, s=0.9, v=1.0):
    r, g, b = colorsys.hsv_to_rgb((tick * speed) % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def blit_center(surf, img, y):
    surf.blit(img, (SNES_W // 2 - img.get_width() // 2, y))


# ── Pixel art drawers ─────────────────────────────────────────────────────────

def draw_monkey(surf, cx, cy):
    pygame.draw.ellipse(surf, BROWN, (cx - 12, cy - 11, 24, 22))
    pygame.draw.ellipse(surf, TAN,   (cx - 10, cy - 9,  20, 18))
    for sx in (-1, 1):
        ex = cx + sx * 13
        pygame.draw.ellipse(surf, BROWN, (ex - 4, cy - 5, 8, 8))
        pygame.draw.ellipse(surf, TAN,   (ex - 3, cy - 4, 6, 6))
    for ex in (cx - 6, cx + 2):
        pygame.draw.rect(surf, EYE_W, (ex,     cy - 6, 4, 4))
        pygame.draw.rect(surf, EYE_K, (ex + 1, cy - 5, 2, 2))
    pygame.draw.ellipse(surf, CREAM, (cx - 7, cy + 2, 14, 9))
    pygame.draw.rect(surf, BROWN, (cx - 3, cy + 5, 2, 2))
    pygame.draw.rect(surf, BROWN, (cx + 1, cy + 5, 2, 2))


def draw_barrel(surf, cx, cy):
    inner = (min(255, BROWN[0] + 24), min(255, BROWN[1] + 16), min(255, BROWN[2] + 8))
    pygame.draw.ellipse(surf, BROWN, (cx - 9, cy - 8, 18, 16))
    pygame.draw.ellipse(surf, inner, (cx - 7, cy - 6, 14, 12))
    for by in (cy - 3, cy + 1, cy + 5):
        pygame.draw.line(surf, BAND, (cx - 8, by), (cx + 8, by), 1)


def draw_button(surf, rect, label, active, font):
    pygame.draw.rect(surf, BTN_ON if active else BTN_BG, rect)
    pygame.draw.rect(surf, BTN_BD if active else (40, 40, 100), rect, 1)
    col = GOLD if active else (140, 140, 190)
    t = font.render(label, False, col)
    surf.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))
    if active:
        cur = pygame.font.Font(None, 10).render(">", False, GOLD)
        surf.blit(cur, (rect.left - 8, rect.centery - cur.get_height() // 2))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Return to Monkey")

    canvas    = pygame.Surface((SNES_W, SNES_H))
    scanlines = _build_scanlines()
    stars     = _build_stars()

    f_big = pygame.font.Font(None, 22)
    f_med = pygame.font.Font(None, 14)
    f_sm  = pygame.font.Font(None, 10)

    btn_start = pygame.Rect(SNES_W // 2 - 44, 148, 88, 16)
    btn_about = pygame.Rect(SNES_W // 2 - 44, 170, 88, 16)
    buttons   = [btn_start, btn_about]
    labels    = ["START GAME", "ABOUT"]
    sel       = 0
    tick      = 0

    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        tick += 1

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = 0
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = 1
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    _handle_select(sel)
                elif ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if ev.type == pygame.MOUSEMOTION:
                mx, my = ev.pos[0] // SCALE, ev.pos[1] // SCALE
                for i, r in enumerate(buttons):
                    if r.collidepoint(mx, my):
                        sel = i
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos[0] // SCALE, ev.pos[1] // SCALE
                for i, r in enumerate(buttons):
                    if r.collidepoint(mx, my):
                        sel = i
                        _handle_select(sel)

        # ── Draw ──────────────────────────────────────────────────────────────
        canvas.fill(BG)

        # Gradient sky
        for gy in range(50):
            v = int(gy * 0.7)
            pygame.draw.line(canvas, (4 + v, 4 + v, 20 + v * 2), (0, gy), (SNES_W, gy))

        # Stars
        for sx, sy, sz in stars:
            tw = 80 + int(175 * abs(math.sin(tick * 0.03 + sx * 0.27)))
            pygame.draw.rect(canvas, (tw, tw, min(255, tw + 30)), (sx, sy, sz, sz))

        # Title
        blit_center(canvas, f_med.render("RETURN TO", False, CYAN), 30)
        blit_center(canvas, f_big.render("MONKEY", False, (24, 12, 0)), 47)  # shadow
        blit_center(canvas, f_big.render("MONKEY", False, hue_color(tick)), 46)

        # Divider
        lx = SNES_W // 2
        pygame.draw.line(canvas, GOLD,   (lx - 68, 67), (lx + 68, 67), 1)
        pygame.draw.line(canvas, ORANGE, (lx - 60, 69), (lx + 60, 69), 1)

        # Monkey (subtle bob)
        bob = int(math.sin(tick * 0.06) * 1.5)
        draw_monkey(canvas, SNES_W // 2, 100 + bob)

        # Barrels
        draw_barrel(canvas, 44,           104)
        draw_barrel(canvas, SNES_W - 44,  104)

        # Nav hint (blinks)
        if (tick // 25) % 2 == 0:
            blit_center(canvas, f_sm.render("UP / DOWN  OR  MOUSE  TO  NAVIGATE", False, DIM), 137)

        # Buttons
        for i, (r, lbl) in enumerate(zip(buttons, labels)):
            draw_button(canvas, r, lbl, sel == i, f_med)

        # Copyright
        blit_center(canvas, f_sm.render("(C) 2024  RETURN TO MONKEY", False, (44, 44, 84)), 213)

        # Scale + scanlines → screen
        scaled = pygame.transform.scale(canvas, (WIN_W, WIN_H))
        screen.blit(scaled, (0, 0))
        screen.blit(scanlines, (0, 0))
        pygame.display.flip()


def _handle_select(sel):
    if sel == 0:
        pass  # TODO: launch game
    else:
        pass  # TODO: show about screen


if __name__ == "__main__":
    main()
