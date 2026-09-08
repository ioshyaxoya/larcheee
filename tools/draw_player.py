#!/usr/bin/env python3
"""draw_player.py — фигура игрока по частям, чтобы она могла ходить.

Фигуры в игре — плоские вырезки, и анимируются они как шарнирные вырезки
(visual_direction §3, метод Darkest Dungeon): перемещаются части, а не
перерисовываются кадры. Поэтому игрок собирается не одним контуром, а
группами со своими точками вращения: корпус, две ноги, две руки, голова.
Движок вращает бёдра и плечи вокруг этих точек — получается шаг.

Пишет `data/player.json`. Одежда зависит от происхождения и класса: цвета
подставляются по коду происхождения, силуэт один.

Запуск: python tools/draw_player.py
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draw_lib import curve, mirror, part, smooth, stroke

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

H = 1.72                      # рост игрока в метрах
SKIN = [0.54, 0.36, 0.24]
SKIN_LIT = [0.66, 0.46, 0.32]
HAIR = [0.09, 0.07, 0.07]
COAT = [0.30, 0.26, 0.30]     # дорожное платье: перекрашивается по происхождению
COAT_LIT = [0.40, 0.35, 0.39]
COAT_FOLD = [0.20, 0.17, 0.20]
TROUSER = [0.24, 0.22, 0.25]
TROUSER_LIT = [0.33, 0.30, 0.34]
BOOT = [0.13, 0.11, 0.11]
SHIRT = [0.80, 0.77, 0.70]
TICKET = [0.92, 0.88, 0.76]


def line(nodes: list, n: int = 10) -> list:
    return curve([smooth((x, y), dx, dy) for x, y, dx, dy in nodes], n=n)


def shape(nodes: list, n: int = 10) -> list:
    return curve([smooth((x, y), dx, dy) for x, y, dx, dy in nodes], n=n, closed=True)


def oval(cx: float, cy: float, rx: float, ry: float) -> list:
    kx, ky = rx * 0.5523, ry * 0.5523
    return curve([
        smooth((cx, cy + ry), rx * 0.55, 0.0),
        smooth((cx + rx, cy), 0.0, -ky),
        smooth((cx, cy - ry * 0.94), -kx, 0.0),
        smooth((cx - rx, cy), 0.0, ky),
    ], n=9, closed=True)


def side(nodes: list, n: int = 12) -> list:
    return mirror(curve([smooth((x * H, y * H), dx * H, dy * H) for x, y, dx, dy in nodes], n=n))


# --- части -------------------------------------------------------------------
# Ноги и руки нарисованы от точки вращения вниз: движок крутит их вокруг неё,
# поэтому в контуре начало координат совпадает с бедром и плечом.

def leg(sx: float) -> dict:
    """Нога от бедра: голень, ботинок. Точка вращения — бедро (0, 0)."""
    thigh = line([(0.0, 0.0, 0.01, -0.10), (sx * 0.012, -0.40, 0.0, -0.10),
                  (sx * 0.004, -0.76, 0.0, -0.06)], n=10)
    return {
        "pivot": [sx * 0.072 * H, 0.455 * H, 0.0],
        "parts": [
            part(stroke(thigh, 0.150, 0.104), TROUSER, "leg_%d" % int(sx)),
            part(stroke([(p[0], p[1] + 0.012) for p in thigh], 0.046, 0.030),
                 TROUSER_LIT, "leg_lit_%d" % int(sx)),
            part(shape([(sx * -0.055, -0.760, 0.02, 0.0), (sx * 0.075, -0.752, 0.0, -0.02),
                        (sx * 0.086, -0.812, -0.03, 0.0), (sx * -0.062, -0.818, 0.0, 0.02)], n=8),
                 BOOT, "boot_%d" % int(sx)),
        ],
    }


def arm(sx: float) -> dict:
    """Рука от плеча: предплечье и кисть. Точка вращения — плечо."""
    limb = line([(0.0, 0.0, sx * 0.01, -0.08), (sx * 0.028, -0.26, 0.0, -0.08),
                 (sx * 0.020, -0.50, 0.0, -0.05)], n=10)
    return {
        "pivot": [sx * 0.148 * H, 0.808 * H, 0.0],
        "parts": [
            part(stroke(limb, 0.116, 0.078), COAT, "arm_%d" % int(sx)),
            part(stroke([(p[0], p[1] + 0.010) for p in limb], 0.036, 0.024),
                 COAT_LIT, "arm_lit_%d" % int(sx)),
            part(oval(sx * 0.020, -0.520, 0.044, 0.048), SKIN, "hand_%d" % int(sx)),
        ],
    }


def body() -> list:
    """Корпус: пальто до колен, рубашка в вырезе, голова, билет за лентой."""
    torso = side([
        (-0.128, 0.400, -0.004, 0.070),
        (-0.140, 0.560, 0.006, 0.070),
        (-0.116, 0.700, -0.004, 0.060),
        (-0.152, 0.800, 0.030, 0.020),
        (-0.058, 0.842, 0.010, 0.016),
    ], n=13)
    return [
        part(torso, COAT, "torso"),
        part(stroke(line([(-0.128 * H, 0.420 * H, 0.004 * H, 0.060 * H),
                          (-0.138 * H, 0.580 * H, 0.006 * H, 0.060 * H),
                          (-0.120 * H, 0.720 * H, 0.020 * H, 0.030 * H)], n=12),
                    0.052, 0.034), COAT_LIT, "torso_rim"),
        part(shape([(-0.030 * H, 0.700 * H, 0.014 * H, 0.0),
                    (0.030 * H, 0.700 * H, 0.0, 0.020 * H),
                    (0.022 * H, 0.820 * H, -0.014 * H, 0.0),
                    (-0.022 * H, 0.820 * H, 0.0, -0.020 * H)], n=9), SHIRT, "shirt"),
        part(stroke(line([(-0.010 * H, 0.560 * H, 0.004 * H, 0.070 * H),
                          (0.004 * H, 0.760 * H, 0.0, 0.040 * H)], n=8), 0.030, 0.022),
             COAT_FOLD, "coat_seam"),
        # Билет за лентой шляпы — он же документ и лист персонажа (§1.4).
        part(shape([(0.052 * H, 0.884 * H, 0.010 * H, 0.0),
                    (0.104 * H, 0.890 * H, 0.0, 0.008 * H),
                    (0.100 * H, 0.916 * H, -0.010 * H, 0.0),
                    (0.048 * H, 0.910 * H, 0.0, -0.008 * H)], n=8), TICKET, "ticket"),
        part(shape([(-0.052 * H, 0.836 * H, 0.016 * H, 0.0),
                    (0.052 * H, 0.836 * H, 0.0, 0.010 * H),
                    (0.046 * H, 0.868 * H, -0.016 * H, 0.0),
                    (-0.046 * H, 0.868 * H, 0.0, -0.010 * H)], n=9), SKIN, "neck"),
        part(oval(0.0, 0.912 * H, 0.058 * H, 0.066 * H), SKIN, "head"),
        part(stroke([(-0.060 * H, 0.926 * H), (0.0, 0.948 * H), (0.060 * H, 0.926 * H)],
                    0.040, 0.040), HAIR, "hair"),
        # Шляпа: по ней игрока и видно со спины.
        part(shape([(-0.086 * H, 0.940 * H, 0.028 * H, 0.0),
                    (0.086 * H, 0.940 * H, 0.0, 0.008 * H),
                    (0.078 * H, 0.958 * H, -0.028 * H, 0.0),
                    (-0.078 * H, 0.958 * H, 0.0, -0.008 * H)], n=9), COAT_FOLD, "hat_brim"),
        part(shape([(-0.054 * H, 0.954 * H, 0.018 * H, 0.0),
                    (0.054 * H, 0.954 * H, 0.0, 0.016 * H),
                    (0.046 * H, 1.006 * H, -0.018 * H, 0.0),
                    (-0.046 * H, 1.006 * H, 0.0, -0.016 * H)], n=9), COAT, "hat_crown"),
    ]


def main() -> int:
    doc = {
        "_comment": ("Фигура игрока по частям: движок вращает бёдра и плечи вокруг "
                     "их точек вращения — так вырезка шагает (visual_direction §3). "
                     "Рисует tools/draw_player.py; править форму — там."),
        "height": H,
        "ground_shadow": part(oval(0.0, 0.014, 0.150, 0.030), [0.10, 0.08, 0.07], "shadow"),
        "groups": [
            {"id": "leg_far", **leg(-1.0), "z": -0.012, "swing": {"phase": 0.5, "amp": 26.0}},
            {"id": "arm_far", **arm(-1.0), "z": -0.008, "swing": {"phase": 0.0, "amp": 17.0}},
            {"id": "body", "pivot": [0.0, 0.0, 0.0], "z": 0.0, "parts": body()},
            {"id": "leg_near", **leg(1.0), "z": 0.010, "swing": {"phase": 0.0, "amp": 26.0}},
            {"id": "arm_near", **arm(1.0), "z": 0.014, "swing": {"phase": 0.5, "amp": 17.0}},
        ],
    }
    path = os.path.join(ROOT, "data", "player.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    n = sum(len(g["parts"]) for g in doc["groups"])
    print("draw_player: %d групп, %d контуров → data/player.json" % (len(doc["groups"]), n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
