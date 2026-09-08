#!/usr/bin/env python3
"""draw_shani.py — рисует встречу с присутствием: испытание Шани.

Это не «бог в глубине сарая». Человек влетел в тормозной вагон — и его встретило
присутствие: **Шани в три человеческих роста на гигантском вороне**. Камера
снизу вверх, потому что смотрит ошарашенный человек. Вокруг — мир Шани: белое
поле, скалы, река, холодное кольцо Сатурна. Мир монохромный и точечный (режим
испытания, docs/visual_direction.md §4): время стоит — цвета нет. Цветной здесь
только он: тёмно-синий, почти холодно-чёрный, лакированный золотом.

Иконография взята не с потолка: Шани — тёмно-синего, почти чёрного цвета, в
синих или чёрных одеждах, с дандой (жезлом судьи), канонически едет на большом
вороне; его взгляд по «Брахма-вайварта-пуране» несёт беду тому, на кого падёт.
Поэтому холодный глаз здесь у ворона — он и зыркает на вас как на добычу; лица
у присутствия нет (visual_direction §3: фигуры без лиц), и от этого хуже.

Хромота канонична и нарисована: одна нога сложена, другая висит вдоль птицы.

Всё, что рисует этот скрипт, — данные: `data/trials/trial_shani.json`, блок
`stage`. Движок (StageBuilder) только заливает контуры плоским цветом.

Запуск: python tools/draw_shani.py
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draw_lib import bez, curve, mirror, part, smooth, stroke

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- мир Шани: белое поле, а не чёрный фон -----------------------------------
PAPER       = [0.945, 0.940, 0.915]
GROUND      = [0.880, 0.872, 0.845]
GROUND_LINE = [0.780, 0.772, 0.748]
RIDGE_1     = [0.560, 0.560, 0.552]   # ближний хребет — темнее
RIDGE_2     = [0.660, 0.662, 0.652]
RIDGE_3     = [0.752, 0.754, 0.744]
RIDGE_4     = [0.836, 0.838, 0.828]
RIVER       = [0.520, 0.548, 0.582]
RIVER_LINE  = [0.680, 0.706, 0.734]
STONE       = [0.430, 0.428, 0.420]
STONE_LIT   = [0.600, 0.598, 0.588]
DEADWOOD    = [0.330, 0.322, 0.310]
SATURN      = [0.700, 0.696, 0.676]
SATURN_RING = [0.560, 0.556, 0.540]

# --- ворон: чёрный с холодной радужностью ------------------------------------
CROW        = [0.052, 0.054, 0.072]
CROW_DEEP   = [0.028, 0.029, 0.042]
CROW_SHEEN  = [0.115, 0.140, 0.245]   # синий отлив
CROW_VIOLET = [0.165, 0.115, 0.235]   # фиолетовый отлив
CROW_EDGE   = [0.300, 0.335, 0.450]   # блик по кромке пера
BEAK        = [0.085, 0.088, 0.105]
BEAK_LIT    = [0.290, 0.300, 0.340]
CLAW        = [0.145, 0.140, 0.150]
CLAW_LIT    = [0.330, 0.325, 0.330]
EYE_GOLD    = [0.880, 0.760, 0.300]
EYE_PALE    = [0.900, 0.915, 0.900]
EYE_PUPIL   = [0.020, 0.020, 0.032]

# --- Шани: тёмно-синий, почти холодно-чёрный ---------------------------------
SKIN        = [0.108, 0.130, 0.215]
SKIN_LIT    = [0.190, 0.225, 0.350]
SKIN_DEEP   = [0.060, 0.072, 0.130]
ROBE        = [0.072, 0.082, 0.158]
ROBE_LIT    = [0.140, 0.160, 0.300]
ROBE_FOLD   = [0.040, 0.046, 0.098]
ROBE_EDGE   = [0.230, 0.255, 0.420]
GOLD        = [0.820, 0.660, 0.270]
GOLD_DIM    = [0.520, 0.405, 0.155]
GOLD_LIT    = [0.960, 0.860, 0.520]
IRON        = [0.235, 0.245, 0.278]
IRON_LIT    = [0.420, 0.435, 0.478]
HALO        = [0.048, 0.050, 0.070]
AUREOLE     = [0.760, 0.605, 0.235]   # светлое кольцо за головой: голова тёмная
AUREOLE_DIM = [0.520, 0.400, 0.150]
AUREOLE_LIT = [0.930, 0.820, 0.470]


# --- ходы --------------------------------------------------------------------

def arc(cx: float, cy: float, rx: float, ry: float, a0: float, a1: float, n: int = 20) -> list:
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
             cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def ring(cx: float, cy: float, rx: float, ry: float, w: float, n: int = 30) -> list:
    """Кольцо со швом: нимб, обод Сатурна, обруч жезла."""
    slit = 0.05
    return (arc(cx, cy, rx + w / 2, ry + w / 2, slit, math.tau, n)
            + arc(cx, cy, rx - w / 2, ry - w / 2, math.tau, slit, n))


def oval(cx: float, cy: float, rx: float, ry: float, squash: float = 0.94) -> list:
    kx, ky = rx * 0.5523, ry * 0.5523
    return curve([
        smooth((cx, cy + ry), rx * 0.55, 0.0),
        smooth((cx + rx, cy), 0.0, -ky * 1.02),
        smooth((cx, cy - ry * squash), -kx * 0.92, 0.0),
        smooth((cx - rx, cy), 0.0, ky * 1.02),
    ], n=10, closed=True)


def shape(nodes: list, n: int = 10) -> list:
    """Замкнутая кривая по узлам (x, y, dx, dy) — силуэт одним движением."""
    return curve([smooth((x, y), dx, dy) for x, y, dx, dy in nodes], n=n, closed=True)


def line(nodes: list, n: int = 10) -> list:
    """Открытая кривая по узлам — под линию-обводку."""
    return curve([smooth((x, y), dx, dy) for x, y, dx, dy in nodes], n=n)


def side(nodes: list, n: int = 12) -> list:
    """Линия бока, отражённая: симметричная фигура одной кривой."""
    return mirror(curve([smooth((x, y), dx, dy) for x, y, dx, dy in nodes], n=n))


def moved(parts: list, dx: float, dy: float = 0.0) -> list:
    return [{"points": [[round(p[0] + dx, 4), round(p[1] + dy, 4)] for p in pt["points"]],
             "color": pt["color"]} for pt in parts]


def feather(base: tuple, tip: tuple, bow: float, w0: float, w1: float) -> list:
    """Перо: линия от основания к концу, изогнутая, с сужением."""
    bx, by = base
    tx, ty = tip
    mx, my = (bx + tx) / 2.0 - by * 0.0, (by + ty) / 2.0
    nx, ny = -(ty - by), (tx - bx)
    d = math.hypot(nx, ny) or 1.0
    pts = bez(base, (bx + (mx - bx) * 0.4 + nx / d * bow, by + (my - by) * 0.4 + ny / d * bow),
              (tx - (tx - mx) * 0.4 + nx / d * bow, ty - (ty - my) * 0.4 + ny / d * bow), tip, 12)
    pts.append(tip)
    return stroke(pts, w0, w1)


# --- ВОРОН -------------------------------------------------------------------
# Ворон, а не водоплавающая птица: тяжёлый клин клюва, лохматая грива на горле,
# компактный корпус, короткие толстые лапы, короткий клиновидный хвост. Профиль
# влево, голова повёрнута к вам — иначе плоская вырезка не смотрит в упор.

def crow() -> list:
    parts: list = []

    # Лапы: короткие, толстые, с чешуёй и когтями. Он стоит на земле, тяжело.
    for sx, hx, ax in [(-1.0, -0.34, -0.54), (1.0, 0.40, 0.56)]:
        tarsus = line([(hx, 1.16, 0.02, -0.16), (ax, 0.34, 0.0, -0.14)], n=10)
        parts.append(part(stroke(tarsus, 0.520, 0.360), CLAW, "crow_tarsus"))
        parts.append(part(stroke(tarsus, 0.140, 0.090), CLAW_LIT, "crow_tarsus_lit"))
        for k in range(5):     # чешуя плюсны: по ней лапа читается птичьей
            t = 0.12 + 0.19 * k
            cx0 = hx + (ax - hx) * t
            cy0 = 1.16 + (0.34 - 1.16) * t
            parts.append(part(stroke(arc(cx0, cy0, 0.195 - 0.020 * k, 0.062,
                                         math.pi * 1.12, math.pi * 1.88, 10), 0.036),
                              [0.088, 0.086, 0.092], "crow_scale_%d_%d" % (int(sx), k)))
        for k, (tx, ty) in enumerate([(ax - 0.86 * sx, 0.03), (ax + 0.10 * sx, 0.02),
                                      (ax + 0.92 * sx, 0.04)]):
            toe = line([(ax, 0.28, (tx - ax) * 0.34, -0.16), (tx, ty, (tx - ax) * 0.26, 0.0)], n=10)
            parts.append(part(stroke(toe, 0.250, 0.075), CLAW, "crow_toe_%d" % k))
            claw_tip = line([(tx, ty, (tx - ax) * 0.10, 0.02),
                             (tx + 0.20 * (1.0 if tx > ax else -1.0), ty + 0.10, 0.04, 0.02)], n=6)
            parts.append(part(stroke(claw_tip, 0.062, 0.018), CLAW_LIT, "crow_claw_%d" % k))
        # Оперённая «штанина» над плюсной — у ворона она мохнатая.
        parts.append(part(shape([(hx - 0.34, 1.06, 0.14, 0.0), (hx + 0.30, 1.10, 0.0, 0.16),
                                 (hx + 0.22, 1.52, -0.16, 0.0), (hx - 0.30, 1.48, 0.0, -0.16)], n=8),
                          CROW_DEEP, "crow_thigh"))

    # Корпус: тяжёлый, низкий, грудь вперёд. Одна замкнутая кривая.
    parts.append(part(shape([
        (-1.66, 1.70, 0.04, 0.32),
        (-1.44, 2.34, 0.26, 0.16),
        (-0.54, 2.66, 0.44, 0.02),
        (0.64, 2.58, 0.34, -0.12),
        (1.62, 2.18, 0.06, -0.26),
        (1.88, 1.74, -0.14, -0.20),
        (1.14, 1.22, -0.34, -0.04),
        (-0.14, 1.04, -0.44, 0.0),
        (-1.18, 1.22, -0.16, 0.20),
    ], n=11), CROW, "crow_body"))
    # Отлив: перья ворона не матовые, они с синим и фиолетовым лаком.
    parts.append(part(shape([
        (-1.52, 1.82, 0.04, 0.24),
        (-1.34, 2.26, 0.20, 0.10),
        (-0.76, 2.44, 0.16, -0.08),
        (-0.72, 1.72, -0.06, -0.24),
        (-1.16, 1.42, -0.14, 0.08),
    ], n=9), CROW_SHEEN, "crow_breast_sheen"))
    parts.append(part(stroke(line([(-1.38, 2.38, 0.26, 0.12), (-0.32, 2.66, 0.44, 0.0),
                                   (0.74, 2.56, 0.30, -0.14), (1.58, 2.20, 0.08, -0.20)], n=13),
                             0.105, 0.055), CROW_EDGE, "crow_back_edge"))

    # Грива на горле: главный признак ворона. Перья висят вниз-вперёд.
    for k, (tx, ty) in enumerate([(-1.98, 1.54), (-1.78, 1.38), (-1.52, 1.30),
                                  (-1.24, 1.34), (-0.98, 1.48)]):
        parts.append(part(feather((-1.46 + 0.06 * k, 2.24 - 0.04 * k), (tx, ty), 0.08, 0.230, 0.060),
                          CROW_DEEP if k % 2 else CROW, "crow_hackle_%d" % k))
    parts.append(part(stroke(line([(-1.62, 1.92, 0.14, -0.16), (-1.32, 1.56, 0.20, -0.10),
                                   (-0.96, 1.44, 0.14, -0.02)], n=10), 0.055, 0.026),
                      CROW_SHEEN, "crow_hackle_edge"))

    # Хвост: короткий клин, а не плюмаж.
    parts.append(part(shape([
        (1.72, 2.10, 0.30, -0.06),
        (3.06, 1.74, 0.02, -0.14),
        (3.12, 1.40, -0.28, -0.02),
        (1.74, 1.38, -0.26, 0.10),
    ], n=9), CROW_DEEP, "crow_tail"))
    for k in range(4):
        t = k / 3.0
        parts.append(part(feather((1.80, 2.00 - 0.16 * t), (2.98 + 0.10 * t, 1.72 - 0.28 * t), -0.05,
                                  0.150, 0.075), CROW if k % 2 else CROW_DEEP, "crow_rect_%d" % k))
    parts.append(part(stroke(line([(1.76, 2.06, 0.30, -0.06), (2.50, 1.90, 0.26, -0.10),
                                   (3.02, 1.72, 0.08, -0.08)], n=10), 0.055, 0.028),
                      CROW_EDGE, "crow_tail_edge"))

    # Сложенное крыло: форма, поверх — маховые перья линиями, кроющие дугами.
    parts.append(part(shape([
        (-0.78, 2.56, 0.32, 0.02),
        (0.36, 2.54, 0.36, -0.04),
        (1.36, 2.14, 0.20, -0.26),
        (2.08, 1.52, -0.16, -0.16),
        (1.12, 1.54, -0.32, 0.04),
        (0.04, 1.94, -0.24, 0.14),
        (-0.76, 2.26, -0.16, 0.12),
    ], n=10), CROW_DEEP, "crow_wing"))
    for k in range(6):
        t = k / 5.0
        parts.append(part(feather((-0.06 + 0.52 * t, 2.42 - 0.10 * t),
                                  (1.72 + 0.34 * t, 1.86 - 0.46 * t), -0.12, 0.220, 0.070),
                          CROW if k % 2 else CROW_DEEP, "crow_primary_%d" % k))
    for k, (r, w) in enumerate([(1.10, 0.045), (0.86, 0.038), (0.64, 0.030)]):
        parts.append(part(stroke(arc(0.10, 1.52, r * 1.15, r, math.pi * 0.10, math.pi * 0.56, 14), w),
                          CROW_SHEEN, "crow_covert_%d" % k))
    parts.append(part(shape([(-0.62, 2.50, 0.26, 0.0), (0.30, 2.48, 0.22, -0.06),
                             (0.42, 2.14, -0.10, -0.14), (-0.54, 2.20, -0.24, 0.04)], n=8),
                      CROW_VIOLET, "crow_scapular"))
    parts.append(part(stroke(line([(-0.74, 2.54, 0.32, 0.0), (0.40, 2.52, 0.32, -0.06),
                                   (1.34, 2.16, 0.16, -0.20)], n=11), 0.085, 0.045),
                      CROW_SHEEN, "crow_wing_edge"))

    # Шея короткая и толстая, голова большая — так читается ворон.
    parts.append(part(stroke(line([(-1.34, 2.32, -0.14, 0.16), (-1.88, 2.74, -0.08, 0.12)], n=8),
                             1.020, 0.940), CROW, "crow_neck"))
    parts.append(part(shape([
        (-2.68, 2.92, 0.10, 0.24),
        (-2.16, 3.44, 0.34, 0.04),
        (-1.62, 3.26, 0.10, -0.24),
        (-1.52, 2.72, -0.20, -0.16),
        (-2.24, 2.44, -0.30, 0.04),
    ], n=11), CROW, "crow_head"))
    parts.append(part(shape([(-2.52, 3.14, 0.14, 0.12), (-2.10, 3.36, 0.22, 0.0),
                             (-1.78, 3.16, 0.0, -0.16), (-2.22, 2.98, -0.18, 0.02)], n=8),
                      CROW_SHEEN, "crow_head_sheen"))

    # Клюв: тяжёлый клин с изогнутым надклювьем. Им можно ударить.
    parts.append(part(shape([
        (-2.62, 3.10, -0.20, -0.02),
        (-3.24, 2.94, -0.18, -0.06),
        (-3.86, 2.62, -0.02, -0.10),
        (-3.04, 2.66, 0.26, 0.0),
        (-2.58, 2.70, 0.08, 0.14),
    ], n=10), BEAK, "crow_beak_upper"))
    parts.append(part(shape([
        (-2.58, 2.68, -0.22, -0.02),
        (-3.62, 2.56, -0.06, -0.06),
        (-3.02, 2.40, 0.22, 0.02),
        (-2.56, 2.44, 0.08, 0.10),
    ], n=9), CROW_DEEP, "crow_beak_lower"))
    parts.append(part(stroke(line([(-2.58, 2.70, -0.24, 0.0), (-3.24, 2.64, -0.20, -0.04),
                                   (-3.76, 2.60, -0.06, -0.02)], n=9), 0.052, 0.024),
                      BEAK_LIT, "crow_gape"))
    parts.append(part(stroke(line([(-2.64, 3.08, -0.20, -0.02), (-3.30, 2.90, -0.16, -0.08),
                                   (-3.82, 2.64, -0.04, -0.04)], n=9), 0.075, 0.028),
                      BEAK_LIT, "crow_culmen"))
    # Глаз. Небольшой, без белка — у птицы его нет, — но с холодным золотом.
    parts.append(part(oval(-2.30, 3.06, 0.230, 0.220), CROW_DEEP, "crow_eye_socket"))
    parts.append(part(oval(-2.30, 3.06, 0.150, 0.145), EYE_GOLD, "crow_eye_iris"))
    parts.append(part(oval(-2.30, 3.06, 0.072, 0.072), EYE_PUPIL, "crow_eye_pupil"))
    parts.append(part(oval(-2.35, 3.11, 0.026, 0.024), EYE_PALE, "crow_eye_spark"))
    parts.append(part(stroke(arc(-2.30, 3.02, 0.290, 0.270, math.pi * 0.06, math.pi * 0.88, 14), 0.115),
                      CROW_DEEP, "crow_brow"))
    return parts


# --- ШАНИ --------------------------------------------------------------------
# Три человеческих роста: 5,2 м, голова в 1/7,5 роста — от этого он и читается
# гигантом, а не человеком на большой птице. Сидит ровно, руки покойны, никуда
# не спешит. Лица нет (visual_direction §3) — и от этого хуже.

def shani() -> list:
    parts: list = []
    hip = 2.74        # сидит на спине птицы

    # Нимб светлый, голова тёмная: только так силуэт головы читается вообще.
    parts.append(part(oval(0.0, 5.30, 1.180, 1.180), AUREOLE_DIM, "shani_aureole_back"))
    parts.append(part(oval(0.0, 5.30, 1.060, 1.060), AUREOLE, "shani_aureole"))
    parts.append(part(oval(0.0, 5.30, 0.860, 0.860), AUREOLE_LIT, "shani_aureole_lit"))
    parts.append(part(ring(0.0, 5.30, 1.300, 1.300, 0.070), AUREOLE_DIM, "shani_aureole_ring"))
    for k in range(16):     # лучи: медленное солнце Сатурна
        a = math.tau * k / 16.0
        parts.append(part(stroke(line([(1.34 * math.cos(a), 5.30 + 1.34 * math.sin(a),
                                       0.10 * math.cos(a), 0.10 * math.sin(a)),
                                       (1.62 * math.cos(a), 5.30 + 1.62 * math.sin(a),
                                        0.08 * math.cos(a), 0.08 * math.sin(a))], n=4),
                                 0.075, 0.028), AUREOLE_DIM, "shani_ray_%d" % k))

    # Подол лежит на спине птицы, а не висит в воздухе.
    parts.append(part(shape([
        (-0.98, 2.92, 0.26, 0.06),
        (0.00, 3.02, 0.32, 0.0),
        (1.02, 2.88, 0.08, -0.18),
        (1.12, 2.44, -0.08, -0.16),
        (0.74, 2.20, -0.22, -0.04),
        (0.06, 2.14, -0.26, 0.0),
        (-0.62, 2.26, -0.16, 0.10),
        (-1.02, 2.52, -0.04, 0.18),
    ], n=11), ROBE, "shani_skirt"))
    for k, (x0, x1) in enumerate([(-0.66, -0.74), (-0.22, -0.26), (0.22, 0.26), (0.64, 0.74)]):
        parts.append(part(stroke(line([(x0, 2.90, 0.02, -0.18), ((x0 + x1) / 2, 2.52, 0.0, -0.16),
                                       (x1, 2.20, 0.0, -0.10)], n=10), 0.050, 0.080),
                          ROBE_FOLD, "shani_skirt_fold_%d" % k))
    parts.append(part(stroke(line([(-0.98, 2.40, 0.24, -0.10), (0.04, 2.14, 0.30, 0.0),
                                   (1.06, 2.40, 0.20, 0.12)], n=14), 0.085, 0.070),
                      GOLD_DIM, "shani_hem"))

    # Сложенная нога: колено далеко наружу, чтобы посадка читалась.
    parts.append(part(shape([
        (0.52, 3.06, 0.34, 0.06),
        (1.62, 3.06, 0.16, -0.20),
        (1.74, 2.44, -0.12, -0.18),
        (0.62, 2.44, -0.36, 0.0),
    ], n=9), ROBE_LIT, "shani_knee"))
    parts.append(part(stroke(arc(1.10, 2.74, 0.660, 0.340, math.pi * 0.06, math.pi * 0.94, 14), 0.070),
                      ROBE_EDGE, "shani_knee_edge"))
    parts.append(part(stroke(line([(1.66, 2.52, -0.10, -0.22), (1.44, 1.96, -0.14, -0.20),
                                   (1.16, 1.62, -0.16, -0.06)], n=10), 0.340, 0.245),
                      ROBE, "shani_shin_folded"))
    parts.append(part(oval(1.06, 1.54, 0.250, 0.160), SKIN, "shani_foot_folded"))

    # Корпус: одна линия бока, отражённая. Длинный, плечи широкие.
    parts.append(part(side([
        (-0.80, 2.80, 0.02, 0.34),
        (-0.66, 3.62, -0.04, 0.36),
        (-0.74, 4.16, 0.06, 0.26),
        (-0.90, 4.62, 0.24, 0.10),
        (-0.30, 4.90, 0.10, 0.08),
    ], n=13), ROBE, "shani_torso"))
    for k, (x0, x1, w0, w1) in enumerate([(-0.40, -0.52, 0.070, 0.125),
                                          (0.04, 0.02, 0.055, 0.105),
                                          (0.46, 0.56, 0.065, 0.115)]):
        parts.append(part(stroke(line([(x0, 4.70, 0.02, -0.30), ((x0 + x1) / 2, 3.80, 0.0, -0.34),
                                       (x1, 2.90, 0.0, -0.22)], n=12), w0, w1),
                          ROBE_FOLD, "shani_fold_%d" % k))
    # Блик по левой кромке: словно лакированный.
    parts.append(part(stroke(line([(-0.80, 2.88, 0.02, 0.32), (-0.68, 3.70, -0.04, 0.34),
                                   (-0.76, 4.22, 0.06, 0.22), (-0.86, 4.66, 0.22, 0.10)], n=15),
                             0.100, 0.070), ROBE_EDGE, "shani_rim"))

    # Ожерелье и перевязь — золото, которое переживает монохром.
    parts.append(part(stroke(arc(0.0, 4.74, 0.640, 0.280, math.pi * 1.04, math.pi * 1.96, 16), 0.115),
                      GOLD_DIM, "shani_necklace"))
    parts.append(part(stroke(arc(0.0, 4.78, 0.450, 0.200, math.pi * 1.06, math.pi * 1.94, 14), 0.055),
                      GOLD, "shani_necklace_2"))
    parts.append(part(stroke(line([(-0.74, 4.44, 0.32, -0.12), (0.0, 4.02, 0.34, -0.16),
                                   (0.72, 3.56, 0.18, -0.16)], n=12), 0.110, 0.080),
                      GOLD_DIM, "shani_sash"))
    parts.append(part(stroke(line([(-0.76, 3.02, 0.32, 0.04), (0.0, 3.10, 0.34, 0.0),
                                   (0.78, 2.98, 0.26, -0.06)], n=12), 0.080, 0.062),
                      GOLD_DIM, "shani_belt"))

    # Правая рука держит данду, левая покойна на колене — как Мона Лиза.
    arm_r = line([(0.78, 4.62, 0.20, -0.24), (1.20, 4.06, 0.10, -0.26), (1.50, 3.62, 0.10, -0.12)], n=12)
    parts.append(part(stroke(arm_r, 0.330, 0.215), ROBE, "shani_arm_r"))
    parts.append(part(stroke(arm_r, 0.078, 0.046), ROBE_EDGE, "shani_arm_r_rim"))
    arm_l = line([(-0.84, 4.58, -0.06, -0.30), (-0.94, 3.96, 0.0, -0.30), (-0.92, 3.34, 0.04, -0.20)], n=12)
    parts.append(part(stroke(arm_l, 0.320, 0.205), ROBE, "shani_arm_l"))
    parts.append(part(stroke(arm_l, 0.076, 0.044), ROBE_EDGE, "shani_arm_l_rim"))
    parts.append(part(oval(1.56, 3.56, 0.215, 0.235), SKIN, "shani_hand_r"))
    parts.append(part(oval(-0.94, 3.20, 0.230, 0.210), SKIN, "shani_hand_l"))
    parts.append(part(stroke(arc(1.56, 3.74, 0.215, 0.125, math.pi * 1.04, math.pi * 1.96, 12), 0.062),
                      GOLD, "shani_bracelet_r"))
    parts.append(part(stroke(arc(1.56, 3.50, 0.240, 0.190, math.pi * 1.20, math.pi * 1.80, 12), 0.075),
                      SKIN_LIT, "shani_grip"))
    parts.append(part(stroke(arc(-0.94, 3.38, 0.225, 0.125, math.pi * 1.04, math.pi * 1.96, 12), 0.062),
                      GOLD, "shani_bracelet_l"))
    for k, (x, y) in enumerate([(-0.88, 4.34), (0.88, 4.38)]):
        parts.append(part(oval(x, y, 0.165, 0.130), GOLD_DIM, "shani_armlet_%d" % k))

    # Хромая нога висит вдоль птицы — канон, и она поверх всего, значит видна.
    lame = line([(-0.98, hip - 0.12, -0.20, -0.09), (-1.58, 2.34, -0.17, -0.12),
                 (-1.86, 1.94, -0.07, -0.11)], n=12)
    parts.append(part(stroke(lame, 0.430, 0.290), ROBE, "shani_leg_lame"))
    parts.append(part(stroke(lame, 0.100, 0.055), ROBE_FOLD, "shani_leg_lame_fold"))
    parts.append(part(stroke(lame, 0.090, 0.055), ROBE_EDGE, "shani_leg_lame_rim"))
    parts.append(part(oval(-1.92, 1.82, 0.270, 0.175), SKIN, "shani_foot"))
    parts.append(part(stroke(arc(-1.90, 1.96, 0.250, 0.160, math.pi * 1.06, math.pi * 1.94, 12), 0.078),
                      GOLD_DIM, "shani_anklet"))

    # Шея и голова: голова в 1/7,5 роста. Лица нет.
    parts.append(part(shape([(-0.22, 4.86, 0.10, 0.02), (0.22, 4.88, 0.02, 0.08),
                             (0.19, 5.06, -0.09, 0.02), (-0.20, 5.05, -0.03, -0.08)], n=8),
                      SKIN_DEEP, "shani_neck"))
    parts.append(part(oval(0.0, 5.32, 0.300, 0.350), SKIN, "shani_head"))
    parts.append(part(stroke(arc(0.0, 5.32, 0.300, 0.345, math.pi * 0.60, math.pi * 1.40, 14), 0.075),
                      SKIN_LIT, "shani_head_rim"))
    parts.append(part(stroke(arc(0.0, 5.28, 0.275, 0.300, math.pi * 1.12, math.pi * 1.88, 14), 0.060),
                      SKIN_DEEP, "shani_jaw"))

    # Корона: три зубца, тёмная с золотой кромкой.
    parts.append(part(shape([(-0.34, 5.58, 0.12, 0.0), (0.34, 5.58, 0.02, 0.08),
                             (0.29, 5.80, -0.10, 0.0), (-0.29, 5.80, -0.02, -0.08)], n=8),
                      HALO, "shani_crown"))
    for k, (x, h) in enumerate([(-0.22, 6.06), (0.0, 6.28), (0.22, 6.06)]):
        parts.append(part(shape([(x - 0.105, 5.78, 0.04, 0.0), (x + 0.105, 5.78, 0.0, 0.08),
                                 (x, h, -0.07, 0.0)], n=8), HALO, "shani_crown_spike_%d" % k))
        parts.append(part(oval(x, h + 0.055, 0.050, 0.050), GOLD, "shani_crown_bead_%d" % k))
    parts.append(part(stroke(line([(-0.34, 5.62, 0.12, 0.0), (0.0, 5.65, 0.12, 0.0),
                                   (0.34, 5.62, 0.10, 0.0)], n=10), 0.060, 0.060),
                      GOLD, "shani_crown_band"))

    # Данда — жезл судьи. Справа, поодаль от головы, выше короны.
    staff = line([(1.70, 2.06, -0.04, 0.50), (1.52, 4.00, -0.04, 0.52), (1.38, 6.10, 0.0, 0.30)], n=16)
    parts.append(part(stroke(staff, 0.185, 0.135), IRON, "shani_danda"))
    parts.append(part(stroke(staff, 0.052, 0.036), IRON_LIT, "shani_danda_lit"))
    for k, (x, y) in enumerate([(1.62, 2.90), (1.48, 4.44), (1.42, 5.62)]):
        parts.append(part(ring(x, y, 0.170, 0.070, 0.058, 18), GOLD_DIM, "shani_danda_ring_%d" % k))
    parts.append(part(shape([(1.38, 6.14, 0.14, 0.0), (1.62, 6.30, 0.0, 0.14),
                             (1.38, 6.74, -0.14, 0.0), (1.14, 6.30, 0.0, -0.14)], n=9),
                      IRON, "shani_danda_head"))
    parts.append(part(ring(1.38, 6.34, 0.290, 0.290, 0.070, 22), GOLD, "shani_danda_finial"))
    parts.append(part(oval(1.38, 6.34, 0.105, 0.105), GOLD_LIT, "shani_danda_eye"))
    return moved(parts, 0.30)


# --- ЗАСТЫВШИЕ ЛЮДИ ----------------------------------------------------------
# Масштаб не читается без человека. В застывшем миге вокруг стоят те, кто был
# в вагоне: полтора-два метра ростом рядом с шестиметровой птицей. Они в мире
# Шани, то есть в точках, и они силуэты — на них не нужно смотреть.

def bystander(h: float = 1.72, seated: bool = False) -> list:
    if seated:
        body = side([(-0.21, 0.0, -0.02, 0.05), (-0.23, 0.11, 0.04, 0.06),
                     (-0.15, 0.25, 0.01, 0.07), (-0.15, 0.40, -0.01, 0.07),
                     (-0.16, 0.52, 0.02, 0.04), (-0.14, 0.57, 0.06, 0.01),
                     (-0.05, 0.60, 0.01, 0.02)], n=10)
        head_y, head_r = 0.66, 0.058
    else:
        body = side([(-0.13, 0.0, -0.01, 0.06), (-0.14, 0.30, 0.01, 0.10),
                     (-0.11, 0.52, 0.0, 0.08), (-0.12, 0.68, 0.01, 0.05),
                     (-0.13, 0.79, 0.03, 0.02), (-0.05, 0.83, 0.01, 0.02)], n=10)
        head_y, head_r = 0.89, 0.056
    body = [(x * h, y * h) for x, y in body]
    return [part(body, [0.300, 0.298, 0.292], "bystander_body"),
            part(oval(0.0, head_y * h, head_r * h, head_r * h * 1.14), [0.300, 0.298, 0.292], "bystander_head"),
            part(oval(0.0, 0.012 * h, 0.17 * h, 0.032 * h), [0.185, 0.183, 0.178], "bystander_ground")]


# --- МИР ШАНИ ----------------------------------------------------------------
# Белое поле, скалы, река, холодное кольцо. Всё это уйдёт в точки — и должно
# читаться плотностью точек, поэтому серые разведены по светлоте.

def ridge_facets(width: float, height: float, seed: float, teeth: int, tone: list) -> list:
    """Грани хребта: линии по склонам. Без них гряда — серое пятно."""
    out = []
    for i in range(teeth):
        t = (i + 0.5) / float(teeth)
        x = -width / 2 + width * t
        h = height * (0.34 + 0.66 * abs(math.sin(seed + t * 5.2)) ** 0.7)
        out.append(part(stroke(line([(x, h * 0.97, width / teeth * 0.16, -h * 0.24),
                                     (x + width / teeth * 0.40, h * 0.30, width / teeth * 0.14, -h * 0.18)], n=8),
                               height * 0.030, height * 0.012), tone, "ridge_facet_%d" % i))
    return out


def ridge(width: float, height: float, seed: float, teeth: int = 7) -> list:
    """Хребет: ломаная гряда одной кривой, замкнутая по низу."""
    nodes = []
    for i in range(teeth + 1):
        t = i / float(teeth)
        x = -width / 2 + width * t
        h = height * (0.34 + 0.66 * abs(math.sin(seed + t * 5.2)) ** 0.7)
        nodes.append(smooth((x, h), width / teeth * 0.34, 0.0))
    pts = curve(nodes, n=8)
    return pts + [(width / 2, -0.5), (-width / 2, -0.5)]


def river() -> list:
    """Река: лента по земле, извивается от горизонта к вам."""
    spine = line([(-1.60, -30.0, 1.20, 6.0), (2.60, -18.0, -1.60, 5.0),
                  (-2.20, -8.0, 1.80, 3.0), (1.40, -1.0, 0.60, 2.0), (0.20, 5.0, -0.40, 2.0)], n=14)
    band = stroke(spine, 1.30, 5.60)
    inner = stroke(spine, 0.55, 2.30)
    return [part(band, RIVER, "river"), part(inner, RIVER_LINE, "river_line")]


def saturn() -> list:
    """Холодное кольцо в небе: не солнце и не луна. Планета медленного бога."""
    return [
        part(oval(0.0, 0.0, 2.10, 2.10), SATURN, "saturn_disc"),
        part(ring(0.0, 0.0, 3.30, 0.72, 0.230, 34), SATURN_RING, "saturn_ring"),
        part(ring(0.0, 0.0, 3.95, 0.90, 0.095, 34), SATURN_RING, "saturn_ring_2"),
        part(stroke(arc(0.0, 0.0, 2.00, 2.00, math.pi * 0.55, math.pi * 1.45, 18), 0.185), SATURN_RING, "saturn_limb"),
    ]


def deadwood(h: float, seed: float) -> list:
    """Сухое дерево: только линии. Ветки — то, что осталось от времени."""
    trunk = line([(0.0, 0.0, 0.04, h * 0.3), (0.10 * seed, h * 0.55, -0.02, h * 0.3), (0.0, h, 0.0, h * 0.1)], n=10)
    parts = [part(stroke(trunk, 0.230 * h / 6.0, 0.070), DEADWOOD, "wood_trunk")]
    for k in range(5):
        t = 0.42 + 0.13 * k
        sx = 1.0 if k % 2 else -1.0
        br = line([(0.02 * seed, h * t, 0.20 * sx, 0.05 * h),
                   (0.62 * sx * (1.0 + 0.2 * k), h * (t + 0.16), 0.20 * sx, 0.02 * h)], n=8)
        parts.append(part(stroke(br, 0.110 * h / 6.0, 0.040), DEADWOOD, "wood_branch_%d" % k))
    return parts


def slab(w: float, hgt: float) -> list:
    """Плита чёрного камня: у Шани земля не мягкая."""
    return [
        part(shape([(-w / 2, 0.0, w * 0.2, 0.0), (w / 2, 0.04, 0.0, hgt * 0.3),
                    (w / 2 - 0.2, hgt, -w * 0.2, 0.0), (-w / 2 + 0.14, hgt - 0.06, 0.0, -hgt * 0.3)], n=8),
             STONE, "slab"),
        part(stroke(arc(0.0, hgt - 0.06, w * 0.42, hgt * 0.16, math.pi * 0.06, math.pi * 0.94, 12), 0.070),
             STONE_LIT, "slab_lit"),
    ]


def stage() -> dict:
    """Кадр встречи: снизу вверх, потому что смотрит ошарашенный человек."""
    world_layers = [
        {"id": "sky", "size": [260.0, 150.0], "pos": [0.0, 40.0, -70.0], "color": PAPER, "layer": 3},
        {"id": "ground", "size": [260.0, 200.0], "pos": [0.0, 0.0, -60.0],
         "rot": [-90.0, 0.0, 0.0], "color": GROUND, "layer": 3},
    ]
    # Полосы земли: ритм, по которому читается, как далеко до горизонта.
    world_layers.append({"id": "ground_near", "size": [260.0, 14.0], "pos": [0.0, 0.01, 3.0],
                         "rot": [-90.0, 0.0, 0.0], "color": [0.800, 0.792, 0.766], "layer": 3})
    for i, (z, ln, c) in enumerate([(-4.0, 0.10, GROUND_LINE), (-11.0, 0.14, GROUND_LINE),
                                    (-21.0, 0.20, GROUND_LINE), (-36.0, 0.26, GROUND_LINE)]):
        world_layers.append({"id": "ground_line_%d" % i, "size": [200.0, ln], "pos": [0.0, 0.02, z],
                             "rot": [-90.0, 0.0, 0.0], "color": c, "layer": 3})

    world_props = [
        ("ridge_near", [part(ridge(46.0, 7.4, 1.1, 8), RIDGE_1, "ridge_1")]
         + ridge_facets(46.0, 7.4, 1.1, 8, [0.455, 0.455, 0.448]), [-4.0, 0.0, -16.0], None),
        ("ridge_mid", [part(ridge(78.0, 11.5, 2.7, 9), RIDGE_2, "ridge_2")]
         + ridge_facets(78.0, 11.5, 2.7, 9, [0.570, 0.572, 0.562]), [3.0, 0.0, -27.0], None),
        ("ridge_far", [part(ridge(120.0, 17.0, 4.3, 10), RIDGE_3, "ridge_3")]
         + ridge_facets(120.0, 17.0, 4.3, 10, [0.672, 0.674, 0.664]), [-6.0, 0.0, -44.0], None),
        ("ridge_last", [part(ridge(190.0, 25.0, 5.9, 11), RIDGE_4, "ridge_4")], [8.0, 0.0, -62.0], None),
        ("river", river(), [0.0, 0.03, 0.0], [-90.0, 0.0, 0.0]),
        ("saturn", saturn(), [10.5, 12.0, -46.0], None),
        ("wood_l", deadwood(6.4, 1.0), [-7.6, 0.0, -9.0], None),
        ("wood_r", deadwood(4.8, -1.0), [8.2, 0.0, -13.0], None),
        ("slab_l", slab(3.6, 0.70), [-6.6, 0.0, -3.4], None),
        ("slab_r", slab(2.8, 0.52), [7.4, 0.0, -5.0], None),
        ("slab_c", slab(5.4, 0.34), [0.4, 0.0, 2.4], None),
        ("witness", bystander(1.74, False), [-3.45, 0.0, 3.30], None),
        ("bystander_2", bystander(1.60, True), [3.90, 0.0, 0.6], None),
        ("bystander_3", bystander(1.66, False), [5.60, 0.0, -4.2], None),
    ]
    return {
        "_comment": ("Встреча с присутствием: Шани в три человеческих роста на вороне, "
                     "камера снизу вверх. Мир (layer 3) уходит в точки, присутствие "
                     "(layer 2) остаётся цветным. Контуры рисует tools/draw_shani.py."),
        "camera": {"pos": [0.0, 0.74, 8.0], "rot": [15.5, 0.0, 0.0],
                   "projection": "perspective", "fov": 52.0, "near": 0.05, "far": 400.0},
        "layers": world_layers,
        "props": [{"id": pid, "pos": pos, "parts": parts, "layer": 3,
                   **({"rot": rot} if rot else {})}
                  for pid, parts, pos, rot in world_props],
        "presence": [
            {"id": "crow", "pos": [-0.95, 0.0, 0.0], "parts": crow(), "layer": 2},
            {"id": "shani", "pos": [0.05, 0.0, 0.35], "parts": shani(), "layer": 2},
        ],
    }


def main() -> int:
    path = os.path.join(ROOT, "data", "trials", "trial_shani.json")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc["stage"] = stage()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    st = doc["stage"]
    print("draw_shani: присутствие %d контуров, мир %d кулис и %d предметов (%d контуров)"
          % (sum(len(p["parts"]) for p in st["presence"]), len(st["layers"]),
             len(st["props"]), sum(len(p["parts"]) for p in st["props"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
