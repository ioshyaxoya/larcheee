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
# Тональная лестница: чем ближе, тем темнее. Пять ступеней, без пересечений —
# иначе точечный растр сливает всё в одну серую кашу, и это видно первым.
PAPER       = [0.962, 0.956, 0.936]   # небо
RIDGE_4     = [0.906, 0.908, 0.896]   # дальний хребет
RIDGE_3     = [0.868, 0.870, 0.858]
RIDGE_2     = [0.830, 0.832, 0.818]
RIDGE_1     = [0.788, 0.790, 0.776]   # ближний хребет
GROUND      = [0.856, 0.850, 0.826]   # долина между хребтами
GROUND_LINE = [0.822, 0.816, 0.792]
GROUND_NEAR = [0.762, 0.756, 0.732]   # передний план чуть плотнее, не темнее
RIVER       = [0.520, 0.548, 0.582]
RIVER_LINE  = [0.680, 0.706, 0.734]
STONE       = [0.402, 0.400, 0.392]
STONE_LIT   = [0.560, 0.558, 0.548]
DEADWOOD    = [0.288, 0.282, 0.272]
SATURN      = [0.700, 0.696, 0.676]
SATURN_RING = [0.560, 0.556, 0.540]

# --- ворон: чёрный с холодной радужностью ------------------------------------
CROW        = [0.052, 0.054, 0.072]
CROW_DEEP   = [0.028, 0.029, 0.042]
CROW_SHEEN  = [0.115, 0.140, 0.245]   # синий отлив
CROW_VIOLET = [0.125, 0.105, 0.185]   # фиолетовый отлив, приглушённый
CROW_EDGE   = [0.300, 0.335, 0.450]   # блик по кромке пера
BEAK        = [0.085, 0.088, 0.105]
BEAK_LIT    = [0.290, 0.300, 0.340]
CLAW        = [0.145, 0.140, 0.150]
CLAW_LIT    = [0.330, 0.325, 0.330]
EYE_GOLD    = [0.880, 0.760, 0.300]
EYE_PALE    = [0.900, 0.915, 0.900]
EYE_PUPIL   = [0.020, 0.020, 0.032]

# --- Шани: синий, лакированный, с золотом. Он единственный в игре такой ------
# Вся игра — плоские тёплые поля и точечный монохром. Он — глазурь: три тона на
# каждой форме плюс блик. Поэтому он и выбивается из кадра, как и должен.
SKIN        = [0.330, 0.505, 0.680]
SKIN_LIT    = [0.470, 0.640, 0.790]
SKIN_SPEC   = [0.720, 0.850, 0.940]
SKIN_SHADE  = [0.205, 0.345, 0.520]
SKIN_DEEP   = [0.125, 0.230, 0.380]
DHOTI       = [0.400, 0.530, 0.660]
DHOTI_LIT   = [0.545, 0.665, 0.775]
DHOTI_SHADE = [0.255, 0.370, 0.495]
HEM_GOLD    = [0.905, 0.620, 0.175]
GOLD        = [0.880, 0.720, 0.260]
GOLD_DIM    = [0.600, 0.450, 0.140]
GOLD_LIT    = [0.980, 0.900, 0.580]
HALO_PALE   = [0.950, 0.930, 0.865]
HALO_RIM    = [0.830, 0.780, 0.650]
HAIR        = [0.075, 0.080, 0.115]
EYE_WHITE   = [0.955, 0.955, 0.930]
EYE_IRIS    = [0.135, 0.185, 0.245]
EYE_LID     = [0.150, 0.230, 0.340]
MOUTH       = [0.520, 0.290, 0.310]
MOUTH_LINE  = [0.300, 0.150, 0.180]
IRON        = [0.300, 0.320, 0.360]
IRON_LIT    = [0.560, 0.585, 0.640]
BOW_WOOD    = [0.640, 0.430, 0.180]
BOW_STRING  = [0.880, 0.860, 0.790]
ARROW_WOOD  = [0.560, 0.380, 0.170]
MOUND       = [0.716, 0.710, 0.686]
MOUND_LIT   = [0.802, 0.796, 0.772]
MOUND_LINE  = [0.612, 0.606, 0.586]


# --- ходы --------------------------------------------------------------------

def arc(cx: float, cy: float, rx: float, ry: float, a0: float, a1: float, n: int = 20) -> list:
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
             cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def ring(cx: float, cy: float, rx: float, ry: float, w: float, n: int = 30) -> list:
    """Кольцо со швом: нимб, обруч жезла, серьга."""
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
    """Замкнутая кривая по узлам (x, y, dx, dy) — форма одним движением."""
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


def scaled(parts: list, k: float) -> list:
    """Та же фигура другого размера: соотношение бога и птицы — часть рисунка."""
    return [{"points": [[round(p[0] * k, 4), round(p[1] * k, 4)] for p in pt["points"]],
             "color": pt["color"]} for pt in parts]


def flipped(parts: list) -> list:
    """То же, но зеркально: правое крыло из левого, вторая рука из первой."""
    return [{"points": [[round(-p[0], 4), p[1]] for p in reversed(pt["points"])],
             "color": pt["color"]} for pt in parts]


def plume(base: tuple, tip: tuple, w: float, bow: float = 0.0) -> list:
    """Перо: лист с одной выпуклой стороной и одной почти прямой.

    Лента одинаковой толщины пером не выглядит — перо асимметрично, и именно
    по этой асимметрии крыло читается крылом, а не чёрной лопастью.
    """
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    fat = bez(base,
              (bx + dx * 0.22 + nx * (w * 1.00 + bow), by + dy * 0.22 + ny * (w * 1.00 + bow)),
              (bx + dx * 0.74 + nx * (w * 0.52 + bow), by + dy * 0.74 + ny * (w * 0.52 + bow)),
              tip, 11)
    lean = bez(tip,
               (bx + dx * 0.72 - nx * w * 0.22, by + dy * 0.72 - ny * w * 0.22),
               (bx + dx * 0.24 - nx * w * 0.34, by + dy * 0.24 - ny * w * 0.34),
               base, 11)
    return fat + lean


def plume_edge(base: tuple, tip: tuple, w: float, bow: float = 0.0) -> list:
    """Светлая кромка по выпуклой стороне пера — она и разделяет перья."""
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    pts = bez(base,
              (bx + dx * 0.22 + nx * (w * 1.00 + bow), by + dy * 0.22 + ny * (w * 1.00 + bow)),
              (bx + dx * 0.74 + nx * (w * 0.52 + bow), by + dy * 0.74 + ny * (w * 0.52 + bow)),
              tip, 11)
    pts.append(tip)
    return stroke(pts, w * 0.20, w * 0.07)


def feather(base: tuple, tip: tuple, bow: float, w0: float, w1: float) -> list:
    """Перо: линия от основания к концу, изогнутая, с сужением."""
    bx, by = base
    tx, ty = tip
    mx, my = (bx + tx) / 2.0, (by + ty) / 2.0
    nx, ny = -(ty - by), (tx - bx)
    d = math.hypot(nx, ny) or 1.0
    pts = bez(base, (bx + (mx - bx) * 0.4 + nx / d * bow, by + (my - by) * 0.4 + ny / d * bow),
              (tx - (tx - mx) * 0.4 + nx / d * bow, ty - (ty - my) * 0.4 + ny / d * bow), tip, 12)
    pts.append(tip)
    return stroke(pts, w0, w1)


def glaze(parts: list, base: list, lit: list, spec: list,
          cx: float, cy: float, rx: float, ry: float, name: str) -> None:
    """Лак: под одной формой три тона и блик. От этого фигура и выглядит
    глазурованной игрушкой, а не плоской вырезкой."""
    parts.append(part(oval(cx, cy, rx, ry), base, name))
    parts.append(part(oval(cx - rx * 0.18, cy + ry * 0.20, rx * 0.62, ry * 0.62), lit, name + "_lit"))
    parts.append(part(oval(cx - rx * 0.36, cy + ry * 0.40, rx * 0.22, ry * 0.24), spec, name + "_spec"))


# --- ВОРОН -------------------------------------------------------------------
# Фронтально, крылья раскрыты, стоит на кургане. Голова опущена к вам, клюв
# книзу, два глаза в упор. Крылья — главный силуэт: они шире всего кадра.

def crow_wing(sx: float = -1.0) -> list:
    """Раскрытое крыло: перепонка, маховые, второстепенные, кроющие, плечо.

    Порядок как в природе: длинные маховые снизу, короткие кроющие сверху.
    Каждое перо — форма со светлой кромкой, поэтому крыло не сливается в пятно.
    """
    parts: list = []

    # Перепонка: тёмная подложка, по которой лежат перья.
    parts.append(part(shape([
        (sx * 0.70, 2.66, sx * 0.28, 0.10),
        (sx * 2.20, 3.30, sx * 0.42, 0.16),
        (sx * 4.10, 3.86, sx * 0.28, 0.02),
        (sx * 4.60, 3.58, sx * -0.08, -0.20),
        (sx * 3.20, 2.62, sx * -0.40, -0.18),
        (sx * 1.70, 2.06, sx * -0.32, -0.06),
        (sx * 0.78, 2.10, sx * -0.14, 0.14),
    ], n=11), CROW_DEEP, "wing_web"))

    # Маховые: длинные, к концу разведённые, с промежутками.
    for k in range(9):
        t = k / 8.0
        ease = math.sin(math.pi * (0.20 + 0.80 * t)) * 0.16      # длины неровно
        base = (sx * (1.06 + 2.30 * t), 2.28 + 0.94 * t)
        tip = (sx * (2.32 + 2.66 * t + ease), 1.52 + 2.42 * t + ease * 0.5)
        w = 0.255 - 0.011 * k
        tone = CROW if k % 2 else CROW_DEEP
        parts.append(part(plume(base, tip, w, sx * -0.03), tone, "wing_primary_%d" % k))
        parts.append(part(plume_edge(base, tip, w, sx * -0.03), CROW_EDGE, "wing_primary_edge_%d" % k))
        parts.append(part(oval(tip[0] - (tip[0] - base[0]) * 0.075,
                               tip[1] - (tip[1] - base[1]) * 0.075,
                               w * 0.17, w * 0.17), tone, "wing_primary_tip_%d" % k))

    # Второстепенные: короче и плотнее, у корня крыла.
    for k in range(6):
        t = k / 5.0
        base = (sx * (0.86 + 0.78 * t), 2.42 + 0.30 * t)
        tip = (sx * (1.62 + 1.42 * t), 1.86 + 0.76 * t)
        w = 0.195 - 0.010 * k
        parts.append(part(plume(base, tip, w, sx * -0.02),
                          CROW_DEEP if k % 2 else CROW, "wing_secondary_%d" % k))
        parts.append(part(plume_edge(base, tip, w, sx * -0.02), CROW_SHEEN, "wing_secondary_edge_%d" % k))

    # Кроющие: два ряда коротких чешуйчатых перьев по передней кромке.
    for row, (dy, w, tone) in enumerate([(0.0, 0.150, CROW), (0.20, 0.115, CROW_SHEEN)]):
        for k in range(7):
            t = k / 6.0
            base = (sx * (0.74 + 0.44 * t), 2.58 + 0.30 * t + dy)
            tip = (sx * (1.16 + 0.66 * t), 2.28 + 0.44 * t + dy)
            parts.append(part(plume(base, tip, w, sx * -0.01), tone, "wing_covert_%d_%d" % (row, k)))
            parts.append(part(plume_edge(base, tip, w, sx * -0.01),
                              CROW_EDGE if row else CROW_VIOLET, "wing_covert_edge_%d_%d" % (row, k)))

    # Передняя кромка и плечевой сгиб: линия, по которой глаз читает форму.
    parts.append(part(stroke(line([(sx * 0.72, 2.70, sx * 0.30, 0.10),
                                   (sx * 2.24, 3.32, sx * 0.44, 0.14),
                                   (sx * 4.06, 3.84, sx * 0.26, 0.02)], n=16), 0.130, 0.055),
                      CROW, "wing_leading"))
    parts.append(part(stroke(line([(sx * 0.74, 2.76, sx * 0.30, 0.09),
                                   (sx * 2.26, 3.36, sx * 0.44, 0.13),
                                   (sx * 4.04, 3.86, sx * 0.24, 0.02)], n=16), 0.045, 0.022),
                      CROW_EDGE, "wing_leading_lit"))
    parts.append(part(shape([(sx * 0.66, 2.78, sx * 0.20, 0.02), (sx * 1.34, 2.94, sx * 0.10, -0.14),
                             (sx * 1.20, 2.52, sx * -0.20, -0.06), (sx * 0.62, 2.44, sx * -0.10, 0.14)], n=10),
                      CROW_VIOLET, "wing_shoulder"))
    return parts


def crow() -> list:
    """Корпус, шея, голова, клюв, глаза, лапы. Крылья — отдельно, они позади."""
    parts: list = []

    # Лапы: короткие, толстые, с пальцами и когтями на кургане.
    for sx in [-1.0, 1.0]:
        hx, ax = sx * 0.46, sx * 0.58
        tarsus = line([(hx, 1.32, 0.02 * sx, -0.20), (ax, 0.36, 0.0, -0.16)], n=10)
        parts.append(part(stroke(tarsus, 0.480, 0.340), CLAW, "crow_tarsus"))
        parts.append(part(stroke(tarsus, 0.130, 0.085), CLAW_LIT, "crow_tarsus_lit"))
        for k in range(5):
            t = 0.12 + 0.19 * k
            cx0 = hx + (ax - hx) * t
            cy0 = 1.32 + (0.36 - 1.32) * t
            parts.append(part(stroke(arc(cx0, cy0, 0.150 - 0.016 * k, 0.050,
                                         math.pi * 1.18, math.pi * 1.82, 10), 0.024),
                              [0.105, 0.103, 0.110], "crow_scale_%d_%d" % (int(sx), k)))
        for k, (tx, ty) in enumerate([(ax - 0.62, 0.03), (ax + 0.05 * sx, 0.02), (ax + 0.62, 0.04)]):
            toe = line([(ax, 0.30, (tx - ax) * 0.34, -0.14), (tx, ty, (tx - ax) * 0.26, 0.0)], n=10)
            parts.append(part(stroke(toe, 0.230, 0.070), CLAW, "crow_toe_%d_%d" % (int(sx), k)))
            claw = line([(tx, ty, (tx - ax) * 0.10, 0.02),
                         (tx + 0.18 * (1.0 if tx > ax else -1.0), ty + 0.09, 0.04, 0.02)], n=6)
            parts.append(part(stroke(claw, 0.058, 0.016), CLAW_LIT, "crow_claw_%d_%d" % (int(sx), k)))

    # Корпус: фронтальная капля. Грудь к вам, поэтому по ней идёт блик.
    parts.append(part(shape([
        (0.0, 3.06, 0.52, 0.0),
        (0.98, 2.46, 0.04, -0.44),
        (0.74, 1.44, -0.30, -0.26),
        (0.0, 1.14, -0.44, 0.0),
        (-0.74, 1.44, -0.04, 0.40),
        (-0.98, 2.46, 0.20, 0.36),
    ], n=12), CROW, "crow_body"))
    # Грудь: отлив мягким пятном и перья группами вниз — не панцирь жука.
    parts.append(part(shape([
        (-0.14, 2.78, 0.32, 0.0),
        (0.56, 2.30, 0.02, -0.28),
        (0.34, 1.60, -0.20, -0.14),
        (-0.26, 1.52, -0.22, 0.06),
        (-0.52, 2.16, 0.06, 0.28),
    ], n=11), CROW_SHEEN, "crow_breast"))
    for row in range(4):
        y = 2.44 - 0.34 * row
        span = 0.66 - 0.07 * row
        for k in range(4):
            t = (k - 1.5) / 1.5
            base = (t * span * 0.86, y + 0.10)
            tip = (t * span * 1.06, y - 0.30)
            w = 0.135 - 0.012 * row
            parts.append(part(plume(base, tip, w, 0.0),
                              CROW if (k + row) % 2 else CROW_DEEP, "crow_plume_%d_%d" % (row, k)))
            parts.append(part(plume_edge(base, tip, w, 0.0), CROW_SHEEN, "crow_plume_edge_%d_%d" % (row, k)))

    # Кромка по силуэту корпуса: без неё тело сливается с крыльями в пятно.
    parts.append(part(stroke(line([(-0.94, 2.26, 0.06, 0.34), (-0.86, 2.86, 0.30, 0.16),
                                   (0.0, 3.04, 0.34, 0.0), (0.86, 2.86, 0.10, -0.30),
                                   (0.94, 2.26, -0.06, -0.30)], n=14), 0.075, 0.075),
                      [0.185, 0.215, 0.330], "crow_body_edge"))
    parts.append(part(stroke(line([(-0.90, 2.60, 0.04, 0.22), (-0.80, 2.94, 0.24, 0.12)], n=8),
                             0.048, 0.028), CROW_EDGE, "crow_body_edge_lit"))

    # Шея и голова: голова опущена, поэтому шея короткая и широкая.
    parts.append(part(stroke(line([(0.0, 2.90, 0.30, 0.0), (0.0, 3.34, 0.28, 0.0)], n=6),
                             1.060, 1.000), CROW, "crow_neck"))
    parts.append(part(oval(0.0, 3.52, 0.680, 0.560), CROW, "crow_head"))
    parts.append(part(shape([(-0.42, 3.72, 0.24, 0.04), (0.16, 3.86, 0.22, -0.06),
                             (0.40, 3.56, -0.06, -0.20), (-0.30, 3.48, -0.24, 0.10)], n=10),
                      CROW_SHEEN, "crow_head_sheen"))
    parts.append(part(stroke(arc(0.0, 3.60, 0.640, 0.520, math.pi * 0.08, math.pi * 0.92, 16), 0.075),
                      CROW_EDGE, "crow_head_edge"))

    # Клюв: тяжёлый клин вниз, к зрителю. Им можно ударить.
    parts.append(part(shape([
        (-0.36, 3.34, 0.24, 0.06),
        (0.36, 3.34, 0.05, -0.18),
        (0.19, 2.60, -0.12, -0.24),
        (0.0, 2.40, -0.10, 0.0),
        (-0.19, 2.60, -0.03, 0.24),
    ], n=12), BEAK, "crow_beak"))
    parts.append(part(stroke(line([(-0.06, 3.28, 0.02, -0.20), (0.0, 2.84, 0.0, -0.18),
                                   (0.02, 2.46, 0.0, -0.08)], n=8), 0.090, 0.032),
                      BEAK_LIT, "crow_culmen"))
    parts.append(part(stroke(line([(-0.33, 3.24, 0.18, -0.02), (0.0, 3.17, 0.18, 0.0),
                                   (0.33, 3.24, 0.16, 0.02)], n=10), 0.052, 0.030),
                      CROW_DEEP, "crow_gape"))

    # Ноздря и надклювье: без них клюв — просто треугольник.
    parts.append(part(oval(-0.135, 3.20, 0.052, 0.038), CROW_DEEP, "crow_nostril"))
    parts.append(part(oval(0.135, 3.20, 0.052, 0.038), CROW_DEEP, "crow_nostril_r"))

    # Глаза: в упор. Без белка — у птицы его нет, — но с веком, иначе это
    # пришитые кружки, а не взгляд.
    for sx in [-1.0, 1.0]:
        ex, ey = sx * 0.40, 3.62
        parts.append(part(oval(ex, ey, 0.205, 0.195), CROW_DEEP, "crow_socket"))
        parts.append(part(oval(ex, ey - 0.008, 0.118, 0.112), EYE_GOLD, "crow_iris"))
        parts.append(part(oval(ex, ey - 0.010, 0.062, 0.062), [0.610, 0.470, 0.135], "crow_iris_deep"))
        parts.append(part(oval(ex, ey - 0.012, 0.046, 0.046), EYE_PUPIL, "crow_pupil"))
        parts.append(part(oval(ex - sx * 0.042, ey + 0.044, 0.022, 0.020), EYE_PALE, "crow_spark"))
        # Верхнее веко нависает — от этого взгляд и становится холодным.
        parts.append(part(stroke(arc(ex, ey + 0.030, 0.175, 0.150,
                                     math.pi * 0.02, math.pi * 0.98, 14), 0.085),
                          CROW_DEEP, "crow_lid"))
        parts.append(part(stroke(arc(ex, ey - 0.02, 0.255, 0.235,
                                     math.pi * 0.06, math.pi * 0.90, 14), 0.105),
                          CROW, "crow_brow"))
        parts.append(part(stroke(arc(ex, ey - 0.02, 0.245, 0.225,
                                     math.pi * 0.20, math.pi * 0.74, 12), 0.038),
                          CROW_SHEEN, "crow_brow_lit"))
    return parts


# --- ШАНИ --------------------------------------------------------------------
# Сидит на вороне по-турецки, лицом к вам, четыре руки: стрела, лук, поднятая
# ладонь, рука на колене; тришула за плечом. Лицо есть — и оно спокойное, это
# и есть худшее. Голова в 1/7,4 роста, а рост — три человеческих.

def face(cx: float = 0.0, cy: float = 5.06, r: float = 0.36) -> list:
    """Лицо. Спокойное, тёмно-синее, с золотом в ушах. Смотрит на вас."""
    parts: list = []
    parts.append(part(oval(cx, cy, r, r * 1.16, squash=1.06), SKIN, "face"))
    # Лак: свет слева сверху, блик на лбу и на скуле.
    parts.append(part(shape([(cx - r * 0.94, cy + r * 0.20, r * 0.20, r * 0.40),
                             (cx - r * 0.30, cy + r * 1.02, r * 0.30, 0.0),
                             (cx + r * 0.10, cy + r * 0.72, 0.0, -r * 0.34),
                             (cx - r * 0.48, cy - r * 0.10, -r * 0.24, -r * 0.20)], n=10),
                      SKIN_LIT, "face_lit"))
    parts.append(part(oval(cx - r * 0.52, cy + r * 0.62, r * 0.20, r * 0.16), SKIN_SPEC, "face_spec"))
    parts.append(part(stroke(arc(cx, cy - r * 0.10, r * 0.92, r * 1.02,
                                 math.pi * 1.16, math.pi * 1.84, 14), r * 0.20),
                      SKIN_SHADE, "face_jaw"))
    # Волосы под короной и виски.
    parts.append(part(arc(cx, cy + r * 0.30, r * 1.02, r * 0.94, math.pi * 0.02, math.pi * 0.98, 18),
                      HAIR, "face_hair"))
    for sx in [-1.0, 1.0]:
        parts.append(part(shape([(cx + sx * r * 0.96, cy + r * 0.44, sx * r * 0.10, -r * 0.20),
                                 (cx + sx * r * 1.06, cy - r * 0.16, sx * -r * 0.06, -r * 0.16),
                                 (cx + sx * r * 0.78, cy - r * 0.06, sx * -r * 0.10, r * 0.16),
                                 (cx + sx * r * 0.80, cy + r * 0.40, sx * r * 0.06, r * 0.14)], n=9),
                          HAIR, "face_temple"))
        # Уши с золотой серьгой.
        parts.append(part(oval(cx + sx * r * 1.00, cy + r * 0.06, r * 0.17, r * 0.26), SKIN, "face_ear"))
        parts.append(part(stroke(arc(cx + sx * r * 1.00, cy + r * 0.06, r * 0.10, r * 0.15,
                                     math.pi * 0.2, math.pi * 1.7, 10), r * 0.07),
                          SKIN_SHADE, "face_ear_line"))
        parts.append(part(ring(cx + sx * r * 1.04, cy - r * 0.34, r * 0.17, r * 0.17, r * 0.075, 16),
                          GOLD, "face_earring"))
        # Глаз: миндаль, радужка, зрачок, блик, тяжёлое верхнее веко, бровь.
        ex, ey = cx + sx * r * 0.40, cy + r * 0.16
        parts.append(part(shape([(ex - r * 0.30, ey, r * 0.08, r * 0.02),
                                 (ex, ey + r * 0.16, r * 0.14, 0.0),
                                 (ex + r * 0.30, ey, 0.0, -r * 0.08),
                                 (ex, ey - r * 0.13, -r * 0.14, 0.0)], n=9), EYE_WHITE, "face_eye"))
        parts.append(part(oval(ex + sx * r * 0.02, ey + r * 0.01, r * 0.115, r * 0.115), EYE_IRIS, "face_iris"))
        parts.append(part(oval(ex + sx * r * 0.02, ey + r * 0.01, r * 0.058, r * 0.058), EYE_PUPIL, "face_pupil"))
        parts.append(part(oval(ex + sx * r * 0.06, ey + r * 0.07, r * 0.030, r * 0.028), EYE_PALE, "face_eye_spark"))
        parts.append(part(stroke(arc(ex, ey + r * 0.01, r * 0.32, r * 0.17,
                                     math.pi * 0.02, math.pi * 0.98, 12), r * 0.075),
                          EYE_LID, "face_lid"))
        parts.append(part(stroke(arc(ex, ey + r * 0.10, r * 0.36, r * 0.22,
                                     math.pi * 0.08, math.pi * 0.92, 12), r * 0.085),
                          HAIR, "face_brow"))
        # Усы: тонкая линия из-под носа в сторону.
        parts.append(part(stroke(line([(cx + sx * r * 0.06, cy - r * 0.42, sx * r * 0.14, -r * 0.02),
                                       (cx + sx * r * 0.44, cy - r * 0.46, sx * r * 0.10, r * 0.04)], n=8),
                                 r * 0.085, r * 0.030), HAIR, "face_moustache"))
    # Нос и рот.
    parts.append(part(shape([(cx - r * 0.09, cy + r * 0.10, r * 0.03, -r * 0.10),
                             (cx - r * 0.14, cy - r * 0.30, r * 0.10, -r * 0.02),
                             (cx + r * 0.14, cy - r * 0.30, r * 0.02, r * 0.10),
                             (cx + r * 0.09, cy + r * 0.10, -r * 0.06, r * 0.06)], n=9),
                      SKIN, "face_nose"))
    parts.append(part(stroke(line([(cx - r * 0.15, cy + r * 0.02, r * 0.0, -r * 0.12),
                                   (cx - r * 0.17, cy - r * 0.28, r * 0.06, -r * 0.02)], n=8),
                             r * 0.070, r * 0.050), SKIN_SHADE, "face_nose_line"))
    parts.append(part(oval(cx - r * 0.03, cy - r * 0.20, r * 0.075, r * 0.060), SKIN_LIT, "face_nose_spec"))
    for sx in [-1.0, 1.0]:
        parts.append(part(oval(cx + sx * r * 0.17, cy - r * 0.35, r * 0.055, r * 0.038),
                          SKIN_DEEP, "face_nostril"))
    parts.append(part(shape([(cx - r * 0.20, cy - r * 0.58, r * 0.07, r * 0.01),
                             (cx, cy - r * 0.555, r * 0.08, 0.0),
                             (cx + r * 0.20, cy - r * 0.58, 0.0, -r * 0.04),
                             (cx, cy - r * 0.655, -r * 0.08, 0.0)], n=9), MOUTH, "face_mouth"))
    parts.append(part(stroke(line([(cx - r * 0.21, cy - r * 0.585, r * 0.07, r * 0.005),
                                   (cx, cy - r * 0.578, r * 0.07, 0.0),
                                   (cx + r * 0.21, cy - r * 0.585, r * 0.06, -r * 0.005)], n=10),
                             r * 0.048), MOUTH_LINE, "face_lip_line"))
    parts.append(part(stroke(arc(cx, cy - r * 0.86, r * 0.22, r * 0.10,
                                 math.pi * 1.10, math.pi * 1.90, 10), r * 0.075),
                      SKIN_SHADE, "face_chin"))
    return parts


def trishula(bx: float, by: float, tx: float, ty: float) -> list:
    """Тришула за плечом: древко линией, три зуба кривыми."""
    parts: list = []
    haft = line([(bx, by, (tx - bx) * 0.34, (ty - by) * 0.34),
                 (tx, ty, (tx - bx) * 0.20, (ty - by) * 0.20)], n=12)
    parts.append(part(stroke(haft, 0.150, 0.118), [0.135, 0.145, 0.170], "trishula_haft_edge"))
    parts.append(part(stroke(haft, 0.100, 0.076), IRON, "trishula_haft"))
    parts.append(part(stroke(haft, 0.032, 0.022), IRON_LIT, "trishula_haft_lit"))
    parts.append(part(shape([(tx - 0.30, ty, 0.10, 0.0), (tx + 0.30, ty, 0.0, 0.08),
                             (tx + 0.24, ty + 0.18, -0.10, 0.0), (tx - 0.24, ty + 0.18, 0.0, -0.08)], n=8),
                      GOLD, "trishula_collar"))
    for sx, h in [(-1.0, 0.86), (0.0, 1.34), (1.0, 0.86)]:
        tine = line([(tx + sx * 0.22, ty + 0.18, sx * 0.09, 0.20),
                     (tx + sx * 0.36, ty + h * 0.55, sx * 0.03, 0.24),
                     (tx + sx * 0.30, ty + h, sx * -0.03, 0.10)], n=12)
        parts.append(part(stroke(tine, 0.160, 0.024), [0.135, 0.145, 0.170], "trishula_tine_edge"))
        parts.append(part(stroke(tine, 0.115, 0.014), IRON, "trishula_tine"))
        parts.append(part(stroke(tine, 0.046, 0.008), IRON_LIT, "trishula_tine_lit"))
    return parts


def shani() -> list:
    parts: list = []
    hip = 2.92

    # Тришула за правым плечом — она позади всего.

    # Нимб: бледный диск, как в иконе. Тёмная голова читается только на светлом.
    parts.append(part(oval(0.0, 5.16, 0.980, 0.980), HALO_RIM, "halo_rim"))
    parts.append(part(oval(0.0, 5.16, 0.880, 0.880), HALO_PALE, "halo"))
    parts.append(part(ring(0.0, 5.16, 1.020, 1.020, 0.055, 30), GOLD_DIM, "halo_ring"))

    # Ноги по-турецки: широкий низкий треугольник, дхоти с золотой каймой,
    # ступни наружу. Хромота видна: правая ступня вывернута, левая подобрана.
    parts.append(part(shape([
        (-1.62, 2.56, 0.30, 0.10),
        (-0.86, 3.00, 0.34, 0.06),
        (0.0, 3.10, 0.36, 0.0),
        (0.90, 2.98, 0.10, -0.20),
        (1.66, 2.54, -0.06, -0.24),
        (1.06, 2.20, -0.34, -0.06),
        (0.0, 2.12, -0.40, 0.0),
        (-1.02, 2.22, -0.22, 0.10),
    ], n=12), DHOTI, "shani_dhoti"))
    parts.append(part(shape([
        (-1.20, 2.62, 0.26, 0.10), (-0.52, 2.92, 0.26, 0.02),
        (0.10, 2.90, 0.20, -0.10), (0.02, 2.46, -0.24, -0.06),
        (-0.86, 2.42, -0.20, 0.10),
    ], n=11), DHOTI_LIT, "shani_dhoti_lit"))
    for sx in [-1.0, 1.0]:
        parts.append(part(shape([(sx * 0.56, 2.94, sx * 0.24, 0.04), (sx * 1.30, 2.86, sx * 0.06, -0.20),
                                 (sx * 1.38, 2.44, sx * -0.10, -0.14), (sx * 0.62, 2.42, sx * -0.26, 0.0)], n=10),
                          DHOTI, "shani_knee_%d" % int(sx)))
        parts.append(part(stroke(arc(sx * 0.98, 2.72, 0.420, 0.240, math.pi * 0.10, math.pi * 0.90, 14), 0.055),
                          DHOTI_LIT, "shani_knee_lit_%d" % int(sx)))
        parts.append(part(stroke(arc(sx * 0.98, 2.54, 0.420, 0.240, math.pi * 1.10, math.pi * 1.90, 14), 0.048),
                          DHOTI_SHADE, "shani_knee_line_%d" % int(sx)))
    for k, (x0, x1) in enumerate([(-1.10, -1.34), (-0.52, -0.62), (0.14, 0.18), (0.74, 0.92)]):
        parts.append(part(stroke(line([(x0, 2.96, 0.02, -0.16), ((x0 + x1) / 2, 2.60, 0.0, -0.14),
                                       (x1, 2.28, 0.0, -0.08)], n=10), 0.050, 0.085),
                          DHOTI_SHADE, "shani_dhoti_fold_%d" % k))
    parts.append(part(stroke(line([(-1.58, 2.42, 0.34, -0.10), (0.0, 2.12, 0.42, 0.0),
                                   (1.62, 2.40, 0.30, 0.12)], n=16), 0.120, 0.100),
                      HEM_GOLD, "shani_hem"))
    parts.append(part(stroke(line([(-1.54, 2.32, 0.34, -0.10), (0.0, 2.04, 0.42, 0.0),
                                   (1.58, 2.30, 0.30, 0.12)], n=16), 0.042, 0.036),
                      GOLD_LIT, "shani_hem_lit"))
    # Зубцы подола: ткань кончается складками, а не ровной дугой.
    for k in range(11):
        t = (k - 5) / 5.0
        hx = t * 1.52
        hy = 2.12 - 0.30 * (1.0 - abs(t) ** 1.6)
        parts.append(part(shape([(hx - 0.150, hy + 0.075, 0.05, 0.0),
                                 (hx + 0.150, hy + 0.075, 0.0, -0.05),
                                 (hx, hy - 0.135, -0.06, 0.0)], n=9),
                          DHOTI if k % 2 else DHOTI_SHADE, "shani_hem_tooth_%d" % k))
        parts.append(part(stroke(line([(hx - 0.140, hy + 0.060, 0.05, -0.01),
                                       (hx, hy - 0.115, 0.04, 0.03)], n=6), 0.030, 0.012),
                          DHOTI_LIT if k % 2 else DHOTI, "shani_hem_tooth_edge_%d" % k))
    # Лучевые складки от пояса: по ним ткань и читается тканью.
    for k in range(7):
        t = (k - 3) / 3.0
        parts.append(part(stroke(line([(t * 0.30, 3.02, t * 0.10, -0.16),
                                       (t * 1.06, 2.62, t * 0.14, -0.14),
                                       (t * 1.40, 2.30, t * 0.08, -0.06)], n=12), 0.038, 0.075),
                          DHOTI_SHADE, "shani_dhoti_ray_%d" % k))
    for sx in [-1.0, 1.0]:
        fx = sx * 1.62
        parts.append(part(oval(fx, 2.58, 0.300, 0.185), SKIN, "shani_sole"))
        parts.append(part(oval(fx - sx * 0.06, 2.62, 0.190, 0.115), SKIN_LIT, "shani_sole_lit"))
        parts.append(part(stroke(arc(fx, 2.72, 0.280, 0.170, math.pi * 1.06, math.pi * 1.94, 12), 0.085),
                          GOLD, "shani_anklet"))
        for k in range(4):
            parts.append(part(oval(fx + sx * (0.10 + 0.10 * k), 2.46 + 0.02 * k, 0.055, 0.042),
                              SKIN_SHADE, "shani_toe_%d_%d" % (int(sx), k)))

    # Корпус: обнажённая синяя грудь, лак в три тона. Плечи широкие.
    parts.append(part(side([
        (-0.62, 3.02, 0.02, 0.26),
        (-0.56, 3.60, -0.04, 0.28),
        (-0.68, 4.06, 0.08, 0.24),
        (-0.92, 4.42, 0.26, 0.08),
        (-0.28, 4.66, 0.10, 0.06),
    ], n=13), SKIN, "shani_torso"))
    parts.append(part(oval(-0.20, 3.86, 0.400, 0.560), SKIN_LIT, "shani_torso_lit"))
    parts.append(part(oval(-0.30, 4.06, 0.135, 0.210), SKIN_SPEC, "shani_torso_spec"))
    parts.append(part(stroke(arc(0.0, 4.10, 0.760, 0.700, math.pi * 1.22, math.pi * 1.78, 12), 0.075),
                      SKIN_SHADE, "shani_belly"))
    # Пупок и складка живота — детали, которых у остальных фигур нет.
    parts.append(part(oval(0.0, 3.28, 0.070, 0.055), SKIN_DEEP, "shani_navel"))

    # Священный шнур и три ожерелья.
    # Священный шнур: через левое плечо к правому бедру и под пояс. Он должен
    # куда-то приходить, иначе это случайная золотая царапина по груди.
    thread = line([(-0.60, 4.56, 0.14, -0.10), (-0.10, 4.00, 0.26, -0.24),
                   (0.44, 3.34, 0.14, -0.18), (0.58, 3.06, 0.04, -0.08)], n=16)
    parts.append(part(stroke(thread, 0.062, 0.048), GOLD_DIM, "shani_thread"))
    parts.append(part(stroke([(px, py + 0.024) for px, py in thread], 0.024, 0.018),
                      GOLD_LIT, "shani_thread_lit"))
    # Три ожерелья с просветом между ними: близкое к шее, среднее, длинное.
    for k, (cy0, rx0, ry0, w, tone) in enumerate([(4.62, 0.400, 0.135, 0.100, GOLD_DIM),
                                                  (4.60, 0.510, 0.290, 0.078, GOLD),
                                                  (4.58, 0.610, 0.470, 0.062, GOLD_LIT)]):
        parts.append(part(stroke(arc(0.0, cy0, rx0, ry0, math.pi * 1.06, math.pi * 1.94, 18), w),
                          tone, "shani_necklace_%d" % k))
    for k in range(9):      # бусины на среднем ожерелье
        a = math.pi * (1.10 + 0.80 * k / 8.0)
        parts.append(part(oval(0.510 * math.cos(a), 4.60 + 0.290 * math.sin(a), 0.044, 0.044),
                          GOLD_LIT, "shani_bead_%d" % k))
    parts.append(part(oval(0.0, 4.09, 0.105, 0.125), GOLD_DIM, "shani_pendant"))
    parts.append(part(oval(0.0, 4.10, 0.062, 0.075), GOLD, "shani_pendant_lit"))
    parts.append(part(oval(-0.018, 4.13, 0.026, 0.030), GOLD_LIT, "shani_pendant_spec"))

    # Четыре руки. Верхние — стрела и лук, нижние — поднятая ладонь и рука
    # на колене. Порядок канонический, оружие тоже.
    def arm(sx: float, sh: tuple, el: tuple, hd: tuple, w0: float, w1: float, tag: str) -> None:
        a = line([(sh[0], sh[1], sx * 0.16, -0.06), (el[0], el[1], (hd[0] - sh[0]) * 0.24,
                                                     (hd[1] - sh[1]) * 0.24),
                  (hd[0], hd[1], (hd[0] - el[0]) * 0.22, (hd[1] - el[1]) * 0.22)], n=12)
        parts.append(part(stroke(a, w0, w1), SKIN, "shani_arm_" + tag))
        below = [(px, py - w0 * 0.30) for px, py in a]
        parts.append(part(stroke(below, w0 * 0.30, w1 * 0.26), SKIN_SHADE, "shani_arm_shade_" + tag))
        above = [(px, py + w0 * 0.26) for px, py in a]
        parts.append(part(stroke(above, w0 * 0.24, w1 * 0.20), SKIN_LIT, "shani_arm_lit_" + tag))
        # Сгиб локтя: короткая складка, а не шарнир.
        parts.append(part(stroke(arc(el[0], el[1] - w0 * 0.18, w0 * 0.42, w0 * 0.30,
                                     math.pi * 1.10, math.pi * 1.90, 10), w0 * 0.13),
                          SKIN_SHADE, "shani_elbow_" + tag))
        parts.append(part(oval(hd[0], hd[1], 0.225, 0.250), SKIN, "shani_hand_" + tag))
        parts.append(part(oval(hd[0] - sx * 0.05, hd[1] + 0.05, 0.135, 0.145), SKIN_LIT, "shani_hand_lit_" + tag))
        for f in range(3):
            parts.append(part(stroke(arc(hd[0] + sx * 0.02, hd[1] + 0.10 - 0.085 * f,
                                         0.185, 0.070,
                                         math.pi * 0.06, math.pi * 0.94, 10), 0.052),
                              SKIN_SHADE, "shani_knuckle_%s_%d" % (tag, f)))
        parts.append(part(stroke(arc(hd[0], hd[1] + 0.22, 0.205, 0.120,
                                     math.pi * 1.04, math.pi * 1.96, 12), 0.070),
                          GOLD, "shani_bracelet_" + tag))
        parts.append(part(oval(sh[0] + sx * 0.10, sh[1] - 0.10, 0.165, 0.135), GOLD_DIM, "shani_armlet_" + tag))
        parts.append(part(oval(sh[0] + sx * 0.08, sh[1] - 0.08, 0.080, 0.065), GOLD_LIT, "shani_armlet_lit_" + tag))

    arm(-1.0, (-0.86, 4.40), (-1.52, 4.68), (-2.02, 5.02), 0.380, 0.255, "ul")
    arm(1.0, (0.86, 4.40), (1.62, 4.62), (2.28, 4.86), 0.380, 0.255, "ur")
    arm(-1.0, (-0.80, 4.16), (-1.34, 3.86), (-1.20, 3.52), 0.390, 0.265, "ll")
    arm(1.0, (0.80, 4.16), (1.34, 3.68), (1.38, 3.06), 0.390, 0.265, "lr")

    # Стрела в верхней левой, лук в верхней правой.
    parts.append(part(stroke([(-1.96, 4.28), (-2.42, 6.02)], 0.072, 0.056), ARROW_WOOD, "shani_arrow"))
    parts.append(part(stroke([(-2.00, 4.30), (-2.44, 5.98)], 0.022, 0.016), GOLD_LIT, "shani_arrow_lit"))
    parts.append(part([(-2.47, 5.94), (-2.32, 6.02), (-2.53, 6.52), (-2.62, 6.12)],
                      IRON_LIT, "shani_arrow_head"))
    parts.append(part([(-2.53, 6.52), (-2.62, 6.12), (-2.68, 6.24)], IRON, "shani_arrow_head_shade"))
    for k in range(3):
        parts.append(part(stroke([(-1.99 - 0.035 * k, 4.35 + 0.13 * k),
                                  (-2.13 - 0.035 * k, 4.62 + 0.13 * k)], 0.115, 0.055),
                          CROW_EDGE, "shani_arrow_fletch_%d" % k))
    bow = arc(2.11, 4.86, 0.440, 1.198, math.pi * 1.42, math.pi * 0.58, 24)
    parts.append(part(stroke(bow, 0.190, 0.190), BOW_WOOD, "shani_bow"))
    parts.append(part(stroke(bow, 0.072, 0.072), GOLD_LIT, "shani_bow_lit"))
    parts.append(part(stroke([(2.00, 3.70), (1.985, 4.86), (2.00, 6.02)], 0.034, 0.034),
                      BOW_STRING, "shani_bowstring"))
    for sy in [-1.0, 1.0]:      # рога лука в золоте
        parts.append(part(oval(2.00, 4.86 + sy * 1.160, 0.100, 0.110), GOLD, "shani_bow_tip_%d" % int(sy)))

    # Поднятая ладонь: пальцы врозь. Это не приветствие, это «стой».
    for k in range(4):
        fx = -1.33 + 0.105 * k
        parts.append(part(stroke(line([(fx, 3.54, 0.0, 0.10), (fx - 0.03, 3.90, 0.0, 0.08)], n=8),
                                 0.078, 0.056), SKIN, "shani_finger_%d" % k))
        parts.append(part(stroke(line([(fx, 3.58, 0.0, 0.10), (fx - 0.03, 3.86, 0.0, 0.08)], n=8),
                                 0.026, 0.018), SKIN_LIT, "shani_finger_lit_%d" % k))
    parts.append(part(oval(-1.20, 3.58, 0.210, 0.185), SKIN, "shani_palm"))
    parts.append(part(oval(-1.24, 3.60, 0.115, 0.100), SKIN_LIT, "shani_palm_lit"))

    # Шея, лицо, корона.
    parts.append(part(shape([(-0.24, 4.58, 0.10, 0.02), (0.24, 4.60, 0.02, 0.08),
                             (0.21, 4.80, -0.09, 0.02), (-0.22, 4.79, -0.03, -0.08)], n=8),
                      SKIN_SHADE, "shani_neck"))
    parts.append(part(stroke(arc(0.0, 4.66, 0.230, 0.110, math.pi * 1.06, math.pi * 1.94, 12), 0.060),
                      SKIN_DEEP, "shani_neck_line"))
    parts += face(0.0, 5.06, 0.36)

    # Кирита-мукута: высокая золотая корона с навершием.
    parts.append(part(shape([(-0.42, 5.42, 0.14, 0.0), (0.42, 5.42, 0.02, 0.10),
                             (0.34, 5.62, -0.12, 0.0), (-0.34, 5.62, -0.02, -0.10)], n=9),
                      GOLD, "crown_band"))
    parts.append(part(stroke(line([(-0.40, 5.50, 0.14, 0.0), (0.0, 5.53, 0.14, 0.0),
                                   (0.40, 5.50, 0.12, 0.0)], n=10), 0.048), GOLD_LIT, "crown_band_lit"))
    parts.append(part(shape([(-0.34, 5.60, 0.12, 0.0), (0.34, 5.60, 0.0, 0.14),
                             (0.20, 6.02, -0.12, 0.04), (-0.20, 6.02, 0.0, -0.14)], n=10),
                      GOLD, "crown_body"))
    parts.append(part(shape([(-0.20, 5.64, 0.08, 0.0), (0.10, 5.66, 0.0, 0.12),
                             (0.02, 5.96, -0.08, 0.0), (-0.16, 5.94, 0.0, -0.12)], n=9),
                      GOLD_LIT, "crown_body_lit"))
    parts.append(part(oval(0.0, 6.10, 0.130, 0.130), GOLD, "crown_knob"))
    parts.append(part(shape([(-0.075, 6.16, 0.03, 0.0), (0.075, 6.16, 0.0, 0.05),
                             (0.0, 6.40, -0.05, 0.0)], n=8), GOLD, "crown_spire"))
    parts.append(part(oval(0.0, 6.44, 0.062, 0.062), GOLD_LIT, "crown_bead"))
    for sx in [-1.0, 1.0]:
        parts.append(part(shape([(sx * 0.36, 5.58, sx * 0.06, 0.02), (sx * 0.52, 5.74, sx * 0.02, 0.06),
                                 (sx * 0.42, 5.86, sx * -0.06, 0.0), (sx * 0.30, 5.70, 0.0, -0.06)], n=9),
                          GOLD_DIM, "crown_wing_%d" % int(sx)))
    return parts


# --- ЗАСТЫВШИЕ ЛЮДИ И ТВАРИ --------------------------------------------------
# Масштаб не читается без кого-то знакомого рядом. У Шани внизу сидит собака и
# воет — она же есть в вагоне (npc_dog), и в застывшем миге она тут.

def bystander(h: float = 1.72, seated: bool = False) -> list:
    if seated:
        body = side([(-0.19, 0.0, -0.02, 0.04), (-0.20, 0.10, 0.04, 0.06),
                     (-0.12, 0.24, 0.01, 0.06), (-0.10, 0.38, -0.01, 0.06),
                     (-0.13, 0.50, 0.03, 0.03), (-0.11, 0.55, 0.05, 0.01),
                     (-0.04, 0.58, 0.01, 0.02)], n=10)
        head_y, head_r = 0.64, 0.056
    else:
        body = side([(-0.055, 0.0, -0.005, 0.05), (-0.062, 0.22, 0.004, 0.08),
                     (-0.075, 0.40, 0.004, 0.06), (-0.095, 0.50, -0.004, 0.05),
                     (-0.085, 0.62, 0.006, 0.04), (-0.125, 0.72, 0.030, 0.010),
                     (-0.040, 0.775, 0.008, 0.015)], n=10)
        head_y, head_r = 0.845, 0.052
    body = [(x * h, y * h) for x, y in body]
    tone = [0.290, 0.288, 0.282]
    parts = [part(body, tone, "bystander_body"),
             part(oval(0.0, head_y * h, head_r * h, head_r * h * 1.16), tone, "bystander_head")]
    if not seated:      # ноги врозь и руки вдоль тела — иначе силуэт «пешка»
        for sx in [-1.0, 1.0]:
            parts.append(part(stroke(line([(sx * 0.030 * h, 0.42 * h, sx * 0.004 * h, -0.10 * h),
                                           (sx * 0.055 * h, 0.0, 0.0, -0.06 * h)], n=8),
                                     0.062 * h, 0.046 * h), tone, "bystander_leg"))
            parts.append(part(stroke(line([(sx * 0.100 * h, 0.70 * h, sx * 0.010 * h, -0.06 * h),
                                           (sx * 0.115 * h, 0.44 * h, 0.0, -0.05 * h)], n=8),
                                     0.050 * h, 0.036 * h), tone, "bystander_arm"))
    parts.append(part(oval(0.0, 0.012 * h, 0.15 * h, 0.030 * h), [0.175, 0.173, 0.168], "bystander_ground"))
    return parts


def howling_dog() -> list:
    """Собака сидит и воет вверх. Она же — мера всему, что над ней, поэтому
    силуэт должен читаться собакой с первого взгляда, а не тёмным пятном."""
    tone = [0.300, 0.296, 0.288]
    dark = [0.190, 0.188, 0.182]
    return [
        part(oval(0.0, 0.020, 0.330, 0.040), dark, "dog_ground"),
        # Задняя часть сидит, передние лапы прямые — посадка воющей собаки.
        part(shape([(-0.30, 0.05, 0.10, 0.12), (-0.24, 0.40, 0.12, 0.04),
                    (0.06, 0.44, 0.10, -0.06), (0.16, 0.12, -0.04, -0.10),
                    (-0.06, 0.03, -0.14, 0.0)], n=11), tone, "dog_haunch"),
        part(stroke(line([(0.08, 0.42, 0.02, -0.10), (0.14, 0.03, 0.0, -0.06)], n=8),
                    0.090, 0.070), tone, "dog_foreleg"),
        part(stroke(line([(-0.02, 0.40, 0.02, -0.10), (0.03, 0.03, 0.0, -0.06)], n=8),
                    0.085, 0.066), dark, "dog_foreleg_far"),
        # Шея вытянута вверх: он воет, а не сидит.
        part(stroke(line([(-0.10, 0.40, 0.04, 0.14), (0.00, 0.74, 0.02, 0.10)], n=8),
                    0.170, 0.135), tone, "dog_neck"),
        part(oval(0.02, 0.84, 0.105, 0.092), tone, "dog_head"),
        # Морда задрана: длинный клин вверх-назад.
        part(shape([(-0.05, 0.88, -0.05, 0.03), (-0.30, 1.02, -0.02, -0.04),
                    (-0.02, 0.79, 0.06, 0.02)], n=9), tone, "dog_muzzle"),
        part(stroke(line([(-0.06, 0.895, -0.06, 0.03), (-0.27, 1.005, -0.03, 0.01)], n=6),
                    0.030, 0.014), dark, "dog_muzzle_line"),
        part(shape([(0.06, 0.92, 0.02, 0.04), (0.15, 1.03, 0.02, -0.02),
                    (0.12, 0.87, -0.02, -0.05)], n=8), dark, "dog_ear"),
        part(stroke(line([(0.14, 0.16, 0.06, 0.04), (0.36, 0.30, 0.04, 0.06)], n=8),
                    0.075, 0.032), tone, "dog_tail"),
    ]


def small_crow() -> list:
    """Ворона на сухой ветке: та же птица, обычного размера. Ещё одна мера."""
    tone = [0.155, 0.153, 0.160]
    return [
        part(shape([(-0.13, 0.05, 0.05, 0.05), (-0.08, 0.20, 0.06, 0.02),
                    (0.14, 0.18, 0.06, -0.04), (0.20, 0.04, -0.03, -0.05),
                    (0.0, 0.0, -0.08, 0.0)], n=9), tone, "scrow_body"),
        part(oval(-0.16, 0.25, 0.070, 0.062), tone, "scrow_head"),
        part(shape([(-0.22, 0.26, -0.04, 0.02), (-0.36, 0.22, -0.01, -0.03),
                    (-0.20, 0.20, 0.05, 0.01)], n=7), tone, "scrow_beak"),
        part(stroke(line([(0.16, 0.10, 0.06, 0.0), (0.40, 0.16, 0.05, 0.03)], n=6), 0.060, 0.024),
             tone, "scrow_tail"),
    ]


def cast_shadow() -> list:
    """Тень присутствия на земле. Три пятна: от тела, от крыльев, у самых лап.

    Это самое важное в кадре после самой фигуры: без тени фигура не стоит в
    сцене, а лежит на ней, и всю работу видно сразу.
    """
    steps = [(5.40, 0.50, [0.734, 0.728, 0.706]),
             (4.10, 0.42, [0.672, 0.666, 0.644]),
             (2.85, 0.33, [0.588, 0.582, 0.562]),
             (1.65, 0.24, [0.452, 0.448, 0.432]),
             (0.78, 0.15, [0.268, 0.265, 0.258])]
    return [part(oval(0.08 * k, -0.02 * k, rx, ry), tone, "shadow_%d" % k)
            for k, (rx, ry, tone) in enumerate(steps)]


def mound(w: float = 7.2, h: float = 1.05) -> list:
    """Курган, на котором он стоит. Земля у Шани твёрдая и голая."""
    crest = line([(-w / 2, 0.02, w * 0.10, h * 0.20), (-w * 0.18, h * 0.94, w * 0.12, h * 0.10),
                  (w * 0.16, h * 0.98, w * 0.12, -h * 0.08), (w / 2, 0.02, w * 0.10, -h * 0.24)], n=18)
    body = crest + [(w / 2, -0.6), (-w / 2, -0.6)]
    return [
        part(body, MOUND, "mound"),
        part(stroke(crest, 0.085, 0.085), MOUND_LIT, "mound_crest"),
        part(stroke(line([(-w * 0.40, h * 0.34, w * 0.12, -h * 0.06),
                          (0.0, h * 0.22, w * 0.14, 0.0),
                          (w * 0.40, h * 0.32, w * 0.12, h * 0.05)], n=14), 0.060, 0.045),
             MOUND_LINE, "mound_break"),
        part(oval(0.0, -0.02, w * 0.54, h * 0.16), [0.395, 0.390, 0.375], "mound_foot"),
    ]


# --- МИР ШАНИ ----------------------------------------------------------------
# Белое поле, скалы, река, холодное кольцо. Всё это уйдёт в точки — и должно
# читаться плотностью точек, поэтому серые разведены по светлоте.

def ground_swell(w: float, h: float, seed: float, tone: list, name: str) -> list:
    """Пологая гряда земли: край кривой, а не прямой.

    Ступени тона по глубине нужны, а прямая граница во всю ширину кадра — нет.
    Поэтому глубина набирается такими наплывами, у каждого свой край.
    """
    nodes = []
    for i in range(7):
        t = i / 6.0
        nodes.append(smooth((-w / 2 + w * t, h * (0.42 + 0.58 * abs(math.sin(seed + t * 3.1)))),
                            w * 0.10, 0.0))
    crest = curve(nodes, n=10)
    return [part(crest + [(w / 2, -1.2), (-w / 2, -1.2)], tone, name)]


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
        {"id": "sky", "size": [300.0, 170.0], "pos": [0.0, 46.0, -78.0], "color": PAPER, "layer": 3},
        {"id": "valley", "size": [300.0, 230.0], "pos": [0.0, 0.0, -70.0],
         "rot": [-90.0, 0.0, 0.0], "color": GROUND, "layer": 3},
    ]

    world_props = [
        ("ridge_near", [part(ridge(46.0, 7.4, 1.1, 8), RIDGE_1, "ridge_1")]
         + ridge_facets(46.0, 7.4, 1.1, 8, [0.455, 0.455, 0.448]), [-4.0, 0.0, -16.0], None),
        ("ridge_mid", [part(ridge(78.0, 11.5, 2.7, 9), RIDGE_2, "ridge_2")]
         + ridge_facets(78.0, 11.5, 2.7, 9, [0.570, 0.572, 0.562]), [3.0, 0.0, -27.0], None),
        ("ridge_far", [part(ridge(120.0, 17.0, 4.3, 10), RIDGE_3, "ridge_3")]
         + ridge_facets(120.0, 17.0, 4.3, 10, [0.672, 0.674, 0.664]), [-6.0, 0.0, -44.0], None),
        ("ridge_last", [part(ridge(190.0, 25.0, 5.9, 11), RIDGE_4, "ridge_4")], [8.0, 0.0, -62.0], None),
        ("swell_far", ground_swell(200.0, 2.4, 0.7, GROUND_LINE, "swell_far"), [0.0, 0.0, -30.0], None),
        ("swell_mid", ground_swell(140.0, 1.7, 2.3, [0.812, 0.806, 0.782], "swell_mid"), [0.0, 0.0, -13.0], None),
        ("swell_near", ground_swell(80.0, 1.1, 4.1, GROUND_NEAR, "swell_near"), [0.0, 0.0, -4.4], None),
        ("mound", mound(6.8, 0.92), [0.0, 0.0, -0.4], None),
        ("cast_shadow", cast_shadow(), [0.15, 1.16, 0.62], None),
        ("saturn", saturn(), [9.8, 12.6, -46.0], None),
        ("wood_r", deadwood(5.6, -1.0), [6.05, 0.0, -3.6], None),
        ("small_crow", small_crow(), [5.30, 3.34, -3.5], None),
        ("wood_l", deadwood(4.2, 1.0), [-8.2, 0.0, -9.0], None),
        ("dog", howling_dog(), [-2.55, 0.0, 4.3], None),
        ("slab_l", slab(3.6, 0.70), [-8.6, 0.0, -6.4], None),
        ("slab_r", slab(2.8, 0.52), [8.2, 0.0, -6.0], None),
        ("witness", bystander(1.74, False), [-5.55, 0.0, 0.6], None),
        ("bystander_2", bystander(1.66, False), [4.55, 0.0, 1.4], None),
    ]
    return {
        "_comment": ("Встреча с присутствием: Шани в три человеческих роста на вороне, "
                     "камера снизу вверх. Мир (layer 3) уходит в точки, присутствие "
                     "(layer 2) остаётся цветным. Контуры рисует tools/draw_shani.py."),
        "camera": {"pos": [0.0, 1.30, 9.5], "rot": [9.0, 0.0, 0.0],
                   "projection": "perspective", "fov": 50.0, "near": 0.05, "far": 400.0},
        "layers": world_layers,
        "props": [{"id": pid, "pos": pos, "parts": parts, "layer": 3,
                   **({"rot": rot} if rot else {})}
                  for pid, parts, pos, rot in world_props],
        # Порядок по глубине: крылья позади, Шани, корпус и голова ворона
        # впереди — его клюв висит перед сложенными ногами бога, как в иконе.
        "presence": [
            {"id": "trishula", "pos": [0.0, 1.15, -0.70], "layer": 2,
             "parts": [part(oval(3.62, 0.05, 0.300, 0.105), MOUND_LINE, "trishula_bed")]
                      + trishula(3.62, 0.02, 3.20, 4.62)},
            {"id": "crow_wings", "pos": [0.0, 0.85, -0.55], "layer": 2,
             "parts": scaled(crow_wing(-1.0) + flipped(crow_wing(-1.0)), 0.78)},
            {"id": "shani", "pos": [0.0, 1.15, -0.15], "parts": shani(), "layer": 2},
            {"id": "crow", "pos": [0.0, 1.15, 0.30], "parts": scaled(crow(), 0.62), "layer": 2},
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
