# Return to Monke

A shamelessly low-fi Donkey Kong clone rendered at SNES resolution (256×224) and scaled up 3× with a CRT scanline overlay. Instead of a gorilla throwing barrels, you have a big Russian farmer hurling cabbages.

## Gameplay

Climb the girders, dodge the rolling cabbages, and reach the farmer at the top to win.

- **3 lives** — a cabbage hit or falling off the screen costs one life
- **Win** — touch the Russian farmer on the top floor
- **Cabbages** — the farmer starts throwing the moment you move; they roll, bounce off walls, and reverse direction when they land on a platform
- **Procedural levels** — the platform layout is randomised every run; no two games are the same

## Controls

| Action | Keys |
|--------|------|
| Move | Arrow keys or WASD |
| Jump | Space |
| Climb ladder | Up / Down (while standing next to one) |
| Exit to menu | Escape |

## Requirements

- Python 3.11+
- pygame 2.5+

> **macOS note:** Python 3.14 has a known broken `pyexpat` on macOS. Use 3.11 or 3.12.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Project structure

```
main.py       — window, scene machine, scanline overlay
menu.py       — animated title screen
game.py       — game loop, procedural level generator, HUD
player.py     — monkey physics, climbing logic, sprite renderer
cabbage.py    — cabbage physics, farmer AI and sprite renderer
```

## Technical notes

- **Resolution:** 256×224 canvas (SNES standard) scaled 3× to 768×672
- **Rendering:** all sprites drawn with primitive pygame shapes — no image assets
- **Camera:** float lerp toward player position, clamped to level bounds
- **Level gen:** fixed floor Y positions with randomised platform sections; adjacency overlap check guarantees every floor is reachable via at least one ladder
