import sys

import pygame

from menu import MenuScene
from game import GameScene

SNES_W, SNES_H = 256, 224
SCALE = 3
WIN_W, WIN_H = SNES_W * SCALE, SNES_H * SCALE


def _build_scanlines():
    surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    for y in range(SCALE - 1, WIN_H, SCALE):
        pygame.draw.line(surf, (0, 0, 0, 70), (0, y), (WIN_W - 1, y))
    return surf


def main():
    pygame.init()
    screen    = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Return to Monke")
    canvas    = pygame.Surface((SNES_W, SNES_H))
    scanlines = _build_scanlines()
    clock     = pygame.time.Clock()

    scene = MenuScene()

    while True:
        dt     = clock.tick(60) / 1000.0
        events = pygame.event.get()

        for ev in events:
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        result = scene.update(events, dt)

        if result == "start":
            scene = GameScene()
        elif result == "menu":
            scene = MenuScene()
        # "about" is unimplemented for now — stays on menu

        scene.draw(canvas)
        scaled = pygame.transform.scale(canvas, (WIN_W, WIN_H))
        screen.blit(scaled, (0, 0))
        screen.blit(scanlines, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
