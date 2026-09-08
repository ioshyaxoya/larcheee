#!/usr/bin/env python3
"""draw_car_01.py — рисует вагон 01 и его население и пишет в данные.

Ориентир — Kentucky Route Zero, но конкретно: **освещённый изнутри разрез**.
Внутри вагона тепло и всё читается — стены, пол, полки, вещи; тёмное здесь
только конструкция (стойки, балки, рама) и передний план. Фон за окном не
чёрный. Люди видны людьми: у каждого цвет кожи, одежды и волос, поза и вещь
в руках. Лиц нет (docs/visual_direction.md §3) — человек узнаётся одеждой.

Рисуется **линиями**, не набором примитивов: силуэт — одна непрерывная кривая
бока, отражённая (tools/draw_lib.mirror), поверх неё накладки и линии-обводки
(складка, кайма, шнур, снасть, спица). Кривые — кубические Безье, линия —
лента переменной толщины (draw_lib.stroke), а не прямоугольник.

Всё, что рисует этот скрипт, — данные: `data/cars/car_01.json` (постановка) и
`data/npcs/*.json` (фигуры). Движок только рисует контуры (StageBuilder).

Запуск: python tools/draw_car_01.py
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draw_lib import (bez, box, circle, curve, ellipse, mirror, part, smooth,
                      stroke, taper)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- палитра вагона ----------------------------------------------------------
# Тёплое дерево и латунь при керосиновом свете; конструкция — тёмный тик.
CEILING     = [0.56, 0.46, 0.33]
WALL_LIT    = [0.80, 0.68, 0.50]
WALL_MID    = [0.62, 0.51, 0.36]
WALL_DEEP   = [0.40, 0.33, 0.26]
FLOOR       = [0.50, 0.35, 0.22]
FLOOR_LINE  = [0.34, 0.23, 0.14]
TEAK        = [0.17, 0.115, 0.075]   # балки, стойки, рама — тёмный контур
TEAK_SOFT   = [0.24, 0.165, 0.105]
TEAK_LINE   = [0.13, 0.09, 0.06]
BRASS       = [0.72, 0.58, 0.24]
BRASS_DIM   = [0.48, 0.38, 0.16]
IRON        = [0.15, 0.145, 0.15]
IRON_LINE   = [0.09, 0.09, 0.10]
PAPER       = [0.94, 0.90, 0.78]
PAPER_LINE  = [0.66, 0.60, 0.50]
SACK        = [0.66, 0.56, 0.38]
SACK_2      = [0.56, 0.47, 0.32]
SACK_LINE   = [0.42, 0.34, 0.22]
CRATE       = [0.48, 0.34, 0.21]
CLOTH_RED   = [0.62, 0.20, 0.16]
CLOTH_BLUE  = [0.20, 0.28, 0.46]
EMBER       = [1.00, 0.55, 0.18]
EMBER_DEEP  = [0.86, 0.30, 0.10]
LAMP_GLASS  = [1.00, 0.94, 0.74]
NIGHT_SKY   = [0.20, 0.26, 0.36]     # за окном не чёрное: город и небо
NIGHT_ROOF  = [0.13, 0.16, 0.24]
NIGHT_GLOW  = [0.52, 0.48, 0.38]

# --- цвета людей -------------------------------------------------------------
SKIN        = [0.52, 0.34, 0.22]
SKIN_DARK   = [0.40, 0.26, 0.17]
SKIN_LINE   = [0.36, 0.22, 0.14]
HAIR        = [0.09, 0.07, 0.07]
GREY_HAIR   = [0.80, 0.78, 0.74]
WHITE_CLOTH = [0.88, 0.85, 0.78]
WHITE_FOLD  = [0.72, 0.68, 0.60]
KHAKI       = [0.58, 0.50, 0.32]
KHAKI_FOLD  = [0.44, 0.37, 0.23]
TURBAN_BLUE = [0.18, 0.26, 0.48]
INDIGO      = [0.115, 0.115, 0.175]
INDIGO_FOLD = [0.07, 0.07, 0.12]
SARI_RED    = [0.70, 0.19, 0.17]
SARI_DEEP   = [0.50, 0.13, 0.13]
SARI_GOLD   = [0.82, 0.66, 0.26]
RAG_GREY    = [0.44, 0.42, 0.37]
DOG_TAN     = [0.46, 0.34, 0.22]


DEEP = [0.036, 0.028, 0.024]      # цвет, в который уходит всё, что далеко


def dim(c: list, z: float) -> list:
    """Цвет на глубине z. Плоская заливка сама не гаснет — гасим её в данных.

    Свет в вагоне кончается там же, где кончается описание (§2: «в глубине
    теряются в темноте»). Это не туман движка: тьма нарисована, как в театре
    гасят задние планы, — и потому её возвращает фонарь, а не настройка.
    """
    t = min(max((0.8 - z) / 17.5, 0.0), 1.0)
    k = (1.0 - t) ** 1.55
    return [round(c[i] * k + DEEP[i] * (1.0 - k), 4) for i in range(3)]


def dimmed(parts: list, z: float) -> list:
    """Тот же реквизит, но стоящий в глубине."""
    return [{"points": p["points"], "color": dim(p["color"], z)} for p in parts]


# --- рисовальные ходы --------------------------------------------------------

def side(nodes: list, k: float = 1.0, n: int = 14) -> list:
    """Линия бока: узлы (x, y, dx, dy) в долях роста → замкнутый силуэт.

    Одна кривая снизу вверх по левой стороне, отражённая направо. Так рисуется
    человек: подол, бедро, талия, плечо, шея — одним движением.
    """
    return mirror(curve([smooth((x * k, y * k), dx * k, dy * k) for x, y, dx, dy in nodes], n=n))


def oval(cx: float, cy: float, rx: float, ry: float, squash: float = 0.94) -> list:
    """Голова, урна, чайник: не окружность, а яйцо — четыре узла с касательными."""
    kx, ky = rx * 0.5523, ry * 0.5523
    return curve([
        smooth((cx, cy + ry), rx * 0.92 / 0.5523 * 0.5523, 0.0),
        smooth((cx + rx, cy), 0.0, -ky * 1.02),
        smooth((cx, cy - ry * squash), -kx * 0.92, 0.0),
        smooth((cx - rx, cy), 0.0, ky * 1.02),
    ], n=9, closed=True)


def blob(cx: float, cy: float, rx: float, ry: float, jitter: float = 0.12,
         seed: float = 1.0, n: int = 7) -> list:
    """Мешок, узел, свёрток: мягкая замкнутая кривая с неровным радиусом."""
    k = (4.0 / 3.0) * math.tan(math.pi / (2 * n))
    nodes = []
    for i in range(n):
        a = math.tau * i / n
        r = 1.0 + jitter * math.sin(seed * 2.3 + i * 1.7)
        p = (cx + rx * r * math.cos(a), cy + ry * r * math.sin(a))
        nodes.append(smooth(p, -math.sin(a) * rx * r * k, math.cos(a) * ry * r * k))
    return curve(nodes, n=8, closed=True)


def panel(y0: float, y1: float, w0: float, w1: float, cx: float = 0.0, bow: float = 0.0) -> list:
    """Доска, полотнище, ящик — с чуть выгнутыми боками, а не строгий трапецоид."""
    dy = y1 - y0
    left = bez((cx - w0 / 2, y0), (cx - w0 / 2 - bow, y0 + dy * 0.35),
               (cx - w1 / 2 - bow, y0 + dy * 0.65), (cx - w1 / 2, y1), 10)
    left.append((cx - w1 / 2, y1))
    return left + [(2 * cx - x, y) for x, y in reversed(left)]


def arc(cx: float, cy: float, rx: float, ry: float, a0: float, a1: float, n: int = 16) -> list:
    """Дуга как ломаная — под линию-обводку (ручка, обод, прядь)."""
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
             cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def ring(cx: float, cy: float, r: float, w: float, n: int = 26) -> list:
    """Обод: кольцо, разрезанное узким швом, — иначе контур не триангулируется."""
    slit = 0.06
    outer = arc(cx, cy, r + w / 2, r + w / 2, slit, math.tau, n)
    inner = arc(cx, cy, r - w / 2, r - w / 2, math.tau, slit, n)
    return outer + inner


def ering(cx: float, cy: float, rx: float, ry: float, w: float, n: int = 28) -> list:
    """Овальный обод (устье ведра, кольцо люка): тоже со швом."""
    slit = 0.06
    outer = arc(cx, cy, rx + w / 2, ry + w / 2, slit, math.tau, n)
    inner = arc(cx, cy, rx - w / 2, ry - w / 2, math.tau, slit, n)
    return outer + inner


def cap(cx: float, cy: float, rx: float, ry: float, a0: float, a1: float) -> list:
    """Покрывало, крышка, тюрбан: дуга, замкнутая хордой, — заполненный купол."""
    return arc(cx, cy, rx, ry, a0, a1, 18)


def hair(cx: float, cy: float, rx: float, ry: float,
         a0: float = 0.05, a1: float = 0.95, lift: float = 0.0) -> list:
    """Волосы: заполненный купол ВНУТРИ овала головы.

    Радиус чуть меньше головы — иначе получается венчик вокруг черепа, а не
    причёска. Хорда поднимается `lift`, если волосы открывают лоб.
    """
    return cap(cx, cy + ry * lift, rx * 0.985, ry * 0.985, math.pi * a0, math.pi * a1)


# --- фигуры ------------------------------------------------------------------
# Голова ≈ 1/7.5 роста. Лиц нет; человек узнаётся одеждой, посадкой и вещью.

def ground(w: float, name: str = "ground") -> dict:
    """Тень под ногами. Без неё фигура висит в воздухе и сливается с полом."""
    return part(oval(0.0, 0.014, w / 2.0, 0.030), [0.135, 0.098, 0.076], name)

def shani(h: float = 1.74) -> list:
    """Присутствие: индиго до земли, повязка вместо лица, трость.
    Единственный, кто остаётся почти тенью, — он и есть тень этого вагона."""
    body = side([
        (-0.150, 0.000, -0.004, 0.060),
        (-0.166, 0.300,  0.004, 0.100),
        (-0.128, 0.560, -0.010, 0.080),
        (-0.150, 0.730,  0.002, 0.050),
        (-0.142, 0.800,  0.034, 0.022),
        (-0.052, 0.842,  0.010, 0.018),
    ], h)
    left_arm = curve([
        smooth((-0.128 * h, 0.790 * h), -0.02 * h, -0.06 * h),
        smooth((-0.172 * h, 0.610 * h),  0.00 * h, -0.09 * h),
        smooth((-0.150 * h, 0.430 * h),  0.03 * h, -0.03 * h),
    ], n=10)
    right_arm = curve([
        smooth((0.128 * h, 0.790 * h), 0.020 * h, -0.060 * h),
        smooth((0.176 * h, 0.620 * h), 0.006 * h, -0.090 * h),
        smooth((0.170 * h, 0.440 * h), -0.02 * h, -0.040 * h),
    ], n=10)
    cane = curve([
        smooth((0.196 * h, 0.470 * h), 0.004 * h, -0.10 * h),
        smooth((0.208 * h, 0.240 * h), 0.002 * h, -0.10 * h),
        smooth((0.206 * h, 0.000 * h), 0.000 * h, -0.06 * h),
    ], n=8)
    fold_a = curve([
        smooth((-0.040 * h, 0.780 * h), -0.02 * h, -0.06 * h),
        smooth((-0.072 * h, 0.520 * h),  0.01 * h, -0.10 * h),
        smooth((-0.050 * h, 0.180 * h),  0.02 * h, -0.06 * h),
    ], n=10)
    fold_b = curve([
        smooth((0.055 * h, 0.760 * h), 0.02 * h, -0.06 * h),
        smooth((0.086 * h, 0.480 * h), 0.00 * h, -0.10 * h),
        smooth((0.074 * h, 0.150 * h), -0.01 * h, -0.06 * h),
    ], n=10)
    return [
        ground(0.40 * h, "shani_ground"),
        part(body, INDIGO, "shani_robe"),
        part(stroke(fold_a, 0.010 * h, 0.020 * h), INDIGO_FOLD, "shani_fold_a"),
        part(stroke(fold_b, 0.008 * h, 0.017 * h), INDIGO_FOLD, "shani_fold_b"),
        part(stroke(cane, 0.019 * h, 0.013 * h), TEAK_SOFT, "shani_cane"),
        part(oval(0.0, 0.905 * h, 0.064 * h, 0.074 * h), [0.085, 0.085, 0.135], "shani_head"),
        part(stroke(arc(0.0, 0.884 * h, 0.062 * h, 0.062 * h, math.pi * 1.18, math.pi * 1.82), 0.016 * h), [0.30, 0.20, 0.14], "shani_jaw"),
        part(stroke(arc(0.0, 0.918 * h, 0.070 * h, 0.066 * h, math.pi * 0.06, math.pi * 0.94), 0.026 * h), [0.055, 0.055, 0.10], "shani_cowl"),
        part(stroke(left_arm, 0.050 * h, 0.036 * h), INDIGO, "shani_arm_l"),
        part(stroke(right_arm, 0.050 * h, 0.036 * h), INDIGO, "shani_arm_r"),
        part(oval(-0.150 * h, 0.424 * h, 0.026 * h, 0.030 * h), SKIN, "shani_hand_l"),
        part(oval(0.172 * h, 0.436 * h, 0.026 * h, 0.030 * h), SKIN, "shani_hand_r"),
    ]


def bir_singh(l: float = 1.72) -> list:
    """Спит на койке: тюрбан, форменная куртка. Горизонталь — он не встанет."""
    k = (4.0 / 3.0) * 0.28
    blanket = curve([
        smooth((-0.52 * l, 0.010), 0.10 * l, 0.00),
        smooth((-0.20 * l, 0.008), 0.14 * l, 0.00),
        smooth((0.16 * l, 0.010), 0.12 * l, 0.00),
        smooth((0.44 * l, 0.020), 0.03 * l, 0.05),
        smooth((0.46 * l, 0.150), -0.02 * l, 0.05),
        smooth((0.30 * l, 0.215), -0.09 * l, 0.01),
        smooth((0.04 * l, 0.165), -0.10 * l, 0.00),
        smooth((-0.24 * l, 0.220), -0.08 * l, -0.01),
        smooth((-0.50 * l, 0.120), -0.02 * l, -0.06),
    ], n=8, closed=True)
    fold = curve([
        smooth((0.28 * l, 0.190), -0.08 * l, -0.02),
        smooth((0.02 * l, 0.140), -0.09 * l, 0.00),
        smooth((-0.26 * l, 0.192), -0.07 * l, -0.01),
    ], n=10)
    arm = curve([
        smooth((-0.14 * l, 0.150), 0.08 * l, 0.02),
        smooth((0.06 * l, 0.170), 0.06 * l, -0.01),
        smooth((0.20 * l, 0.130), 0.04 * l, -0.02),
    ], n=10)
    beard = blob(0.318 * l, 0.108, 0.030 * l, 0.040, 0.10, 3.0, 7)
    return [
        part(blanket, KHAKI, "bir_blanket"),
        part(stroke(fold, 0.014, 0.010), KHAKI_FOLD, "bir_fold"),
        part(panel(0.010, 0.140, 0.075 * l, 0.060 * l, cx=-0.492 * l, bow=0.008), WHITE_CLOTH, "bir_leg"),
        part(oval(0.352 * l, 0.150, 0.072 * l, 0.070), SKIN, "bir_head"),
        part(beard, GREY_HAIR, "bir_beard"),
        part(cap(0.372 * l, 0.152, 0.096 * l, 0.098, -math.pi * 0.16, math.pi * 0.84), TURBAN_BLUE, "bir_turban"),
        part(stroke(arc(0.372 * l, 0.152, 0.074 * l, 0.076, -math.pi * 0.06, math.pi * 0.74), 0.018), [0.12, 0.18, 0.36], "bir_turban_line"),
        part(stroke(arm, 0.050, 0.038), KHAKI, "bir_arm"),
        part(oval(0.224 * l, 0.126, 0.030 * l, 0.028), SKIN, "bir_hand"),
    ]


def ratan(h: float = 1.60) -> list:
    """Сидит у печки, белое дхоти, бурый жилет, седая голова, руки к огню."""
    body = side([
        (-0.186, 0.000, -0.018, 0.048),
        (-0.202, 0.104,  0.038, 0.058),
        (-0.142, 0.244,  0.010, 0.068),
        (-0.145, 0.400, -0.006, 0.070),
        (-0.158, 0.520,  0.020, 0.035),
        (-0.140, 0.566,  0.056, 0.014),
        (-0.046, 0.598,  0.010, 0.016),
    ], h)
    def vest_half(sx: float) -> list:
        v = curve([
            smooth((sx * 0.150 * h, 0.562 * h), sx * 0.004 * h, -0.05 * h),
            smooth((sx * 0.144 * h, 0.430 * h), sx * -0.004 * h, -0.06 * h),
            smooth((sx * 0.152 * h, 0.312 * h), sx * 0.020 * h, -0.02 * h),
            smooth((sx * 0.058 * h, 0.296 * h), sx * 0.010 * h, 0.030 * h),
            smooth((sx * 0.048 * h, 0.430 * h), sx * 0.004 * h, 0.050 * h),
            smooth((sx * 0.062 * h, 0.556 * h), sx * 0.040 * h, 0.010 * h),
        ], n=10)
        v.append((sx * 0.150 * h, 0.562 * h))
        return v
    knee = curve([
        smooth((-0.190 * h, 0.150 * h), 0.05 * h, 0.03 * h),
        smooth((-0.060 * h, 0.196 * h), 0.05 * h, -0.01 * h),
        smooth((0.060 * h, 0.170 * h), 0.05 * h, -0.02 * h),
    ], n=10)
    arm_r = curve([
        smooth((0.128 * h, 0.500 * h), 0.03 * h, -0.05 * h),
        smooth((0.198 * h, 0.396 * h), 0.02 * h, -0.05 * h),
        smooth((0.232 * h, 0.296 * h), -0.01 * h, -0.04 * h),
    ], n=10)
    arm_l = curve([
        smooth((-0.130 * h, 0.492 * h), -0.02 * h, -0.05 * h),
        smooth((-0.178 * h, 0.396 * h), 0.00 * h, -0.05 * h),
        smooth((-0.168 * h, 0.312 * h), 0.02 * h, -0.03 * h),
    ], n=10)
    return [
        ground(0.44 * h, "ratan_ground"),
        part(body, WHITE_CLOTH, "ratan_dhoti"),
        part(stroke(knee, 0.011 * h, 0.008 * h), WHITE_FOLD, "ratan_knee_line"),
        part(vest_half(-1.0), [0.38, 0.26, 0.16], "ratan_vest_l"),
        part(vest_half(1.0), [0.34, 0.23, 0.14], "ratan_vest_r"),
        part(stroke(arm_l, 0.044 * h, 0.032 * h), SKIN, "ratan_arm_l"),
        part(stroke(arm_r, 0.044 * h, 0.032 * h), SKIN, "ratan_arm_r"),
        part(oval(-0.170 * h, 0.302 * h, 0.026 * h, 0.026 * h), SKIN, "ratan_hand_l"),
        part(oval(0.236 * h, 0.288 * h, 0.026 * h, 0.026 * h), SKIN, "ratan_hand_r"),
        part(panel(0.560 * h, 0.612 * h, 0.086 * h, 0.070 * h, bow=0.004 * h), SKIN, "ratan_neck"),
        part(oval(0.0, 0.658 * h, 0.058 * h, 0.066 * h), SKIN, "ratan_head"),
        part(hair(0.0, 0.658 * h, 0.058 * h, 0.066 * h, 0.06, 0.94, 0.06), GREY_HAIR, "ratan_hair"),
    ]


def hafiz(h: float = 1.54) -> list:
    """Паломник спит сидя: белая курта, топи, седая борода, чётки в руке."""
    body = side([
        (-0.240, 0.000, -0.020, 0.055),
        (-0.252, 0.120,  0.046, 0.070),
        (-0.166, 0.272,  0.008, 0.080),
        (-0.158, 0.420, -0.006, 0.070),
        (-0.172, 0.532,  0.022, 0.035),
        (-0.148, 0.578,  0.058, 0.014),
        (-0.048, 0.608,  0.010, 0.016),
    ], h)
    placket = curve([
        smooth((0.0, 0.576 * h), 0.01 * h, -0.06 * h),
        smooth((0.014 * h, 0.420 * h), 0.0, -0.07 * h),
        smooth((0.004 * h, 0.264 * h), -0.01 * h, -0.05 * h),
    ], n=10)
    hem = curve([
        smooth((-0.196 * h, 0.244 * h), 0.06 * h, 0.02 * h),
        smooth((0.0, 0.276 * h), 0.07 * h, 0.0),
        smooth((0.196 * h, 0.244 * h), 0.06 * h, -0.02 * h),
    ], n=10)
    arm = curve([
        smooth((-0.140 * h, 0.500 * h), -0.01 * h, -0.05 * h),
        smooth((-0.164 * h, 0.390 * h), 0.02 * h, -0.05 * h),
        smooth((-0.108 * h, 0.302 * h), 0.03 * h, -0.02 * h),
    ], n=10)
    beads = curve([
        smooth((-0.098 * h, 0.286 * h), 0.02 * h, -0.02 * h),
        smooth((-0.058 * h, 0.238 * h), 0.02 * h, -0.03 * h),
        smooth((-0.066 * h, 0.184 * h), -0.03 * h, -0.01 * h),
    ], n=10)
    return [
        ground(0.52 * h, "hafiz_ground"),
        part(body, WHITE_CLOTH, "hafiz_kurta"),
        part(stroke(hem, 0.010 * h), WHITE_FOLD, "hafiz_hem"),
        part(stroke(placket, 0.010 * h, 0.007 * h), WHITE_FOLD, "hafiz_placket"),
        part(stroke(arm, 0.042 * h, 0.030 * h), WHITE_CLOTH, "hafiz_arm"),
        part(stroke(beads, 0.013 * h, 0.010 * h), [0.32, 0.21, 0.12], "hafiz_beads"),
        part(oval(-0.104 * h, 0.296 * h, 0.026 * h, 0.026 * h), SKIN, "hafiz_hand"),
        part(panel(0.572 * h, 0.618 * h, 0.086 * h, 0.070 * h, bow=0.004 * h), SKIN, "hafiz_neck"),
        part(oval(0.0, 0.666 * h, 0.058 * h, 0.066 * h), SKIN, "hafiz_head"),
        part(blob(0.0, 0.628 * h, 0.042 * h, 0.040 * h, 0.10, 2.0, 7), GREY_HAIR, "hafiz_beard"),
        part(panel(0.712 * h, 0.744 * h, 0.108 * h, 0.094 * h, bow=0.005 * h), WHITE_CLOTH, "hafiz_topi"),
        part(stroke(arc(0.0, 0.712 * h, 0.056 * h, 0.012 * h, math.pi * 0.06, math.pi * 0.94), 0.009 * h), WHITE_FOLD, "hafiz_topi_line"),
    ]


def saraswati(h: float = 1.62) -> list:
    """Сари: красное с золотой каймой, паллу через плечо, судки в руке.
    Она — самое яркое пятно вагона: город цветной, и она из города."""
    body = side([
        (-0.205, 0.000, -0.006, 0.070),
        (-0.190, 0.220,  0.012, 0.110),
        (-0.132, 0.480,  0.004, 0.090),
        (-0.128, 0.660, -0.006, 0.070),
        (-0.140, 0.776,  0.006, 0.040),
        (-0.132, 0.826,  0.042, 0.020),
        (-0.050, 0.864,  0.010, 0.018),
    ], h)
    hem = curve([
        smooth((-0.204 * h, 0.016 * h), 0.07 * h, 0.010 * h),
        smooth((0.0, 0.036 * h), 0.08 * h, 0.0),
        smooth((0.204 * h, 0.016 * h), 0.07 * h, -0.010 * h),
    ], n=12)
    pallu = curve([
        smooth((-0.108 * h, 0.828 * h), 0.06 * h, -0.02 * h),
        smooth((0.062 * h, 0.782 * h), 0.05 * h, -0.05 * h),
        smooth((0.128 * h, 0.618 * h), -0.01 * h, -0.09 * h),
        smooth((0.078 * h, 0.404 * h), -0.04 * h, -0.06 * h),
        smooth((0.010 * h, 0.286 * h), -0.03 * h, -0.04 * h),
    ], n=12)
    fold = curve([
        smooth((-0.088 * h, 0.560 * h), -0.02 * h, -0.08 * h),
        smooth((-0.126 * h, 0.320 * h), 0.01 * h, -0.10 * h),
        smooth((-0.104 * h, 0.070 * h), 0.02 * h, -0.05 * h),
    ], n=12)
    arm = curve([
        smooth((-0.118 * h, 0.782 * h), -0.02 * h, -0.06 * h),
        smooth((-0.166 * h, 0.630 * h), 0.00 * h, -0.07 * h),
        smooth((-0.176 * h, 0.512 * h), 0.01 * h, -0.04 * h),
    ], n=10)
    return [
        ground(0.44 * h, "sar_ground"),
        part(body, SARI_RED, "sar_sari"),
        part(stroke(fold, 0.012 * h, 0.020 * h), SARI_DEEP, "sar_fold"),
        part(stroke(hem, 0.030 * h), SARI_GOLD, "sar_hem"),
        part(stroke(pallu, 0.062 * h, 0.030 * h), SARI_DEEP, "sar_pallu"),
        part(stroke(pallu, 0.016 * h, 0.010 * h), SARI_GOLD, "sar_pallu_edge"),
        part(stroke(arm, 0.046 * h, 0.034 * h), SKIN, "sar_arm"),
        part(panel(0.782 * h, 0.856 * h, 0.100 * h, 0.074 * h, bow=0.006 * h), SKIN, "sar_neck"),
        part(oval(0.0, 0.922 * h, 0.060 * h, 0.070 * h), SKIN, "sar_head"),
        part(hair(0.0, 0.922 * h, 0.060 * h, 0.070 * h, 0.05, 0.95, 0.05), HAIR, "sar_hair"),
        part(cap(0.0, 0.908 * h, 0.084 * h, 0.100 * h, math.pi * 0.02, math.pi * 0.98), SARI_RED, "sar_veil"),
        part(stroke(arc(0.0, 0.908 * h, 0.084 * h, 0.100 * h, math.pi * 0.02, math.pi * 0.98), 0.013 * h), SARI_GOLD, "sar_veil_edge"),
        part(oval(-0.180 * h, 0.500 * h, 0.026 * h, 0.026 * h), SKIN, "sar_hand"),
        part(stroke(arc(-0.174 * h, 0.524 * h, 0.028 * h, 0.020 * h, math.pi * 1.05, math.pi * 1.95), 0.010 * h), SARI_GOLD, "sar_bangles"),
        part(panel(0.398 * h, 0.478 * h, 0.098 * h, 0.104 * h, cx=-0.184 * h, bow=0.005 * h), BRASS, "sar_tiffin"),
        part(stroke(arc(-0.184 * h, 0.478 * h, 0.046 * h, 0.028 * h, 0.0, math.pi), 0.010 * h), BRASS_DIM, "sar_tiffin_handle"),
    ]


def monimala(h: float = 1.58) -> list:
    """Вдова: белое сари без каймы, глиняная урна в руках, взгляд вниз."""
    body = side([
        (-0.208, 0.000, -0.006, 0.070),
        (-0.194, 0.230,  0.012, 0.110),
        (-0.136, 0.492,  0.004, 0.090),
        (-0.134, 0.676, -0.006, 0.070),
        (-0.146, 0.790,  0.006, 0.040),
        (-0.138, 0.840,  0.042, 0.020),
        (-0.052, 0.878,  0.010, 0.018),
    ], h)
    fold_a = curve([
        smooth((-0.070 * h, 0.700 * h), -0.02 * h, -0.09 * h),
        smooth((-0.116 * h, 0.400 * h), 0.01 * h, -0.11 * h),
        smooth((-0.096 * h, 0.060 * h), 0.02 * h, -0.05 * h),
    ], n=12)
    fold_b = curve([
        smooth((0.062 * h, 0.680 * h), 0.02 * h, -0.09 * h),
        smooth((0.108 * h, 0.380 * h), -0.01 * h, -0.10 * h),
        smooth((0.092 * h, 0.070 * h), -0.02 * h, -0.05 * h),
    ], n=12)
    arm_l = curve([
        smooth((-0.112 * h, 0.740 * h), -0.01 * h, -0.05 * h),
        smooth((-0.140 * h, 0.630 * h), 0.02 * h, -0.05 * h),
        smooth((-0.072 * h, 0.548 * h), 0.03 * h, -0.01 * h),
    ], n=10)
    arm_r = curve([
        smooth((0.112 * h, 0.740 * h), 0.01 * h, -0.05 * h),
        smooth((0.140 * h, 0.630 * h), -0.02 * h, -0.05 * h),
        smooth((0.072 * h, 0.548 * h), -0.03 * h, -0.01 * h),
    ], n=10)
    return [
        ground(0.44 * h, "mon_ground"),
        part(body, WHITE_CLOTH, "mon_sari"),
        part(stroke(fold_a, 0.012 * h, 0.020 * h), WHITE_FOLD, "mon_fold_a"),
        part(stroke(fold_b, 0.010 * h, 0.018 * h), WHITE_FOLD, "mon_fold_b"),
        part(panel(0.796 * h, 0.868 * h, 0.100 * h, 0.074 * h, bow=0.006 * h), SKIN, "mon_neck"),
        part(oval(0.0, 0.934 * h, 0.060 * h, 0.070 * h), SKIN, "mon_head"),
        part(hair(0.0, 0.934 * h, 0.060 * h, 0.070 * h, 0.05, 0.95, 0.05), HAIR, "mon_hair"),
        part(cap(0.0, 0.920 * h, 0.086 * h, 0.102 * h, math.pi * 0.02, math.pi * 0.98), WHITE_CLOTH, "mon_veil"),
        part(stroke(arc(0.0, 0.920 * h, 0.086 * h, 0.102 * h, math.pi * 0.02, math.pi * 0.98), 0.012 * h), WHITE_FOLD, "mon_veil_edge"),
        part(oval(0.0, 0.506 * h, 0.084 * h, 0.100 * h, squash=0.86), [0.44, 0.27, 0.17], "mon_urn"),
        part(stroke(arc(0.0, 0.578 * h, 0.052 * h, 0.020 * h, math.pi * 0.05, math.pi * 0.95), 0.018 * h), WHITE_CLOTH, "mon_urn_cloth"),
        part(stroke(arc(0.0, 0.494 * h, 0.076 * h, 0.030 * h, math.pi * 1.10, math.pi * 1.90), 0.012 * h), [0.34, 0.20, 0.13], "mon_urn_line"),
        part(stroke(arm_l, 0.044 * h, 0.032 * h), SKIN, "mon_arm_l"),
        part(stroke(arm_r, 0.044 * h, 0.032 * h), SKIN, "mon_arm_r"),
    ]


def kanu(h: float = 1.26) -> list:
    """Мальчик-безбилетник: голый торс, серые штаны, латхи через плечо."""
    body = side([
        (-0.150, 0.000, -0.010, 0.060),
        (-0.176, 0.150,  0.014, 0.080),
        (-0.150, 0.330,  0.006, 0.075),
        (-0.156, 0.480,  0.004, 0.060),
        (-0.170, 0.576,  0.018, 0.030),
        (-0.150, 0.616,  0.052, 0.014),
        (-0.052, 0.652,  0.010, 0.016),
    ], h)
    arm_r = curve([
        smooth((0.136 * h, 0.588 * h), 0.03 * h, -0.05 * h),
        smooth((0.196 * h, 0.470 * h), 0.01 * h, -0.06 * h),
        smooth((0.190 * h, 0.348 * h), -0.02 * h, -0.04 * h),
    ], n=10)
    arm_l = curve([
        smooth((-0.136 * h, 0.588 * h), -0.02 * h, -0.05 * h),
        smooth((-0.186 * h, 0.470 * h), 0.00 * h, -0.06 * h),
        smooth((-0.176 * h, 0.336 * h), 0.02 * h, -0.04 * h),
    ], n=10)
    lathi = curve([
        smooth((0.212 * h, 0.660 * h), 0.006 * h, -0.14 * h),
        smooth((0.226 * h, 0.330 * h), 0.000 * h, -0.14 * h),
        smooth((0.216 * h, 0.020 * h), -0.006 * h, -0.10 * h),
    ], n=8)
    return [
        ground(0.38 * h, "kanu_ground"),
        part(body, SKIN, "kanu_body"),
        part(stroke(arc(0.0, 0.520 * h, 0.120 * h, 0.070 * h, math.pi * 1.15, math.pi * 1.85), 0.012 * h), SKIN_LINE, "kanu_ribs"),
        part(panel(0.230 * h, 0.400 * h, 0.316 * h, 0.300 * h, bow=0.010 * h), RAG_GREY, "kanu_shorts"),
        part(stroke(curve([
            smooth((-0.150 * h, 0.396 * h), 0.05 * h, 0.008 * h),
            smooth((0.0, 0.410 * h), 0.05 * h, 0.0),
            smooth((0.150 * h, 0.396 * h), 0.05 * h, -0.008 * h)], n=8), 0.014 * h), [0.32, 0.30, 0.26], "kanu_belt"),
        part(stroke(lathi, 0.016 * h, 0.012 * h), TEAK_SOFT, "kanu_lathi"),
        part(stroke(arm_l, 0.040 * h, 0.028 * h), SKIN, "kanu_arm_l"),
        part(stroke(arm_r, 0.040 * h, 0.028 * h), SKIN, "kanu_arm_r"),
        part(panel(0.612 * h, 0.664 * h, 0.086 * h, 0.072 * h, bow=0.004 * h), SKIN, "kanu_neck"),
        part(oval(0.0, 0.716 * h, 0.070 * h, 0.078 * h), SKIN, "kanu_head"),
        part(hair(0.0, 0.716 * h, 0.070 * h, 0.078 * h, 0.02, 0.98, 0.02), HAIR, "kanu_hair"),
        part(stroke(arc(-0.040 * h, 0.772 * h, 0.036 * h, 0.032 * h, math.pi * 0.30, math.pi * 1.00), 0.016 * h), HAIR, "kanu_cowlick"),
    ]


def dog_figure() -> list:
    """Пёс у печки: спина линией, лапы линиями, хвост линией."""
    body = curve([
        smooth((-0.30, 0.180), 0.06, 0.06),
        smooth((-0.20, 0.400), 0.09, 0.03),
        smooth((0.06, 0.452), 0.10, 0.00),
        smooth((0.28, 0.416), 0.06, -0.03),
        smooth((0.34, 0.260), -0.01, -0.06),
        smooth((0.24, 0.150), -0.07, -0.02),
        smooth((-0.06, 0.126), -0.09, 0.00),
    ], n=9, closed=True)
    head = oval(0.372, 0.474, 0.100, 0.088, squash=0.92)
    muzzle = curve([
        smooth((0.404, 0.500), 0.05, 0.006),
        smooth((0.512, 0.480), 0.02, -0.03),
        smooth((0.470, 0.424), -0.04, -0.01),
        smooth((0.396, 0.436), -0.02, 0.02),
    ], n=8, closed=True)
    ear = curve([
        smooth((0.300, 0.520), 0.03, 0.04),
        smooth((0.336, 0.626), 0.03, -0.01),
        smooth((0.372, 0.532), -0.01, -0.04),
    ], n=8)
    ear.append((0.300, 0.520))
    leg_f = curve([smooth((0.220, 0.230), 0.01, -0.08), smooth((0.234, 0.010), 0.02, -0.04)], n=8)
    leg_b = curve([smooth((-0.206, 0.240), -0.02, -0.08), smooth((-0.238, 0.010), -0.01, -0.05)], n=8)
    tail = curve([
        smooth((-0.290, 0.300), -0.04, 0.04),
        smooth((-0.406, 0.420), -0.02, 0.06),
        smooth((-0.428, 0.532), 0.04, 0.02),
    ], n=10)
    return [
        ground(0.62, "dog_ground"),
        part(body, DOG_TAN, "dog_body"),
        part(stroke(leg_b, 0.050, 0.038), [0.40, 0.29, 0.19], "dog_leg_b"),
        part(stroke(tail, 0.036, 0.016), DOG_TAN, "dog_tail"),
        part(stroke(leg_f, 0.052, 0.040), DOG_TAN, "dog_leg_f"),
        part(head, DOG_TAN, "dog_head"),
        part(muzzle, [0.40, 0.29, 0.19], "dog_muzzle"),
        part(ear, [0.34, 0.24, 0.15], "dog_ear"),
    ]


FIGURES = {
    # Кто где стоит — тоже рисунок: никто никого не заслоняет, у каждого свой
    # план по глубине, и Шани — единственный, кто стоит в темноте.
    "god_shani": ("indigo_robe", shani(), [0.72, 0.0, -3.9], None),
    "npc_bir_singh": ("sleeping_turban", bir_singh(), [-2.06, 0.665, -1.55], [0.0, 16.0, 0.0]),
    "npc_ratan": ("seated_dhoti", ratan(), [-1.06, 0.0, -0.55], None),
    "npc_hafiz": ("seated_topi", hafiz(), [-1.42, 0.0, -2.45], None),
    "npc_saraswati": ("sari_red", saraswati(), [1.24, 0.0, -0.35], None),
    "npc_monimala": ("widow_white", monimala(), [-0.24, 0.0, -1.75], None),
    "npc_kanu": ("boy_lathi", kanu(), [0.30, 0.0, -1.60], None),
    "npc_dog": ("dog", dog_figure(), [-0.46, 0.0, -1.05], [0.0, 28.0, 0.0]),
}


# --- реквизит ----------------------------------------------------------------
# Деталей должно быть много: по ним читается, где мы. Всё — от земли вверх.

def stove() -> list:
    """Пузатая чугунка: бок — кривая, труба и снасть — линии."""
    belly = side([
        (-0.200, 0.000, -0.03, 0.05),
        (-0.312, 0.260,  0.00, 0.12),
        (-0.268, 0.620, -0.03, 0.09),
        (-0.300, 0.840,  0.02, 0.02),
        (-0.318, 0.916,  0.00, 0.01),
    ], n=12)
    pipe = curve([
        smooth((0.0, 0.900), 0.004, 0.30),
        smooth((0.030, 1.700), 0.000, 0.30),
        smooth((0.010, 2.620), -0.004, 0.20),
    ], n=10)
    spout = curve([
        smooth((0.292, 1.082), 0.05, 0.010),
        smooth((0.384, 1.128), 0.03, 0.030),
    ], n=8)
    logs = [
        curve([smooth((-0.640, 0.062), 0.08, 0.006), smooth((-0.386, 0.078), 0.06, -0.004)], n=6),
        curve([smooth((-0.618, 0.160), 0.07, -0.006), smooth((-0.404, 0.142), 0.06, 0.006)], n=6),
        curve([smooth((-0.596, 0.244), 0.06, 0.010), smooth((-0.420, 0.258), 0.05, -0.004)], n=6),
    ]
    return [
        part(belly, IRON, "stove_belly"),
        part(panel(0.900, 0.972, 0.700, 0.660, bow=0.006), IRON, "stove_plate"),
        part(stroke(pipe, 0.064, 0.052), IRON, "stove_pipe"),
        part(stroke(pipe, 0.018, 0.014), [0.24, 0.23, 0.24], "stove_pipe_line"),
        part(oval(0.0, 0.430, 0.176, 0.164), EMBER_DEEP, "stove_door_rim"),
        part(oval(0.0, 0.430, 0.140, 0.130), EMBER, "stove_fire"),
        part(stroke(arc(0.0, 0.430, 0.176, 0.164, math.pi * 0.05, math.pi * 0.95), 0.026), IRON_LINE, "stove_door_arc"),
        part(stroke(arc(0.0, 0.700, 0.250, 0.090, math.pi * 1.10, math.pi * 1.90), 0.024), IRON_LINE, "stove_band"),
        part(oval(0.185, 1.070, 0.130, 0.102), BRASS, "stove_kettle"),
        part(stroke(spout, 0.040, 0.022), BRASS, "stove_spout"),
        part(stroke(arc(0.185, 1.112, 0.114, 0.104, math.pi * 0.10, math.pi * 0.90), 0.018), BRASS_DIM, "stove_kettle_handle"),
        *[part(stroke(g, 0.062, 0.052), CRATE if i % 2 else TEAK_SOFT, "stove_log_%d" % i) for i, g in enumerate(logs)],
    ]


def brake_wheel() -> list:
    """Тормозное колесо: обод — линия по окружности, спицы — линии."""
    spokes = []
    for i in range(4):
        a = math.pi * i / 4
        spokes.append(stroke([(-0.27 * math.cos(a), 1.02 - 0.27 * math.sin(a)),
                              (0.0, 1.02),
                              (0.27 * math.cos(a), 1.02 + 0.27 * math.sin(a))], 0.030, 0.030))
    column = curve([
        smooth((0.0, 0.000), 0.006, 0.20),
        smooth((0.014, 0.520), 0.000, 0.20),
        smooth((0.0, 1.000), -0.006, 0.10),
    ], n=8)
    return [
        part(stroke(column, 0.130, 0.086), IRON, "brake_column"),
        part(panel(0.0, 0.086, 0.360, 0.300, bow=0.010), IRON_LINE, "brake_base"),
        *[part(s, BRASS_DIM, "brake_spoke_%d" % i) for i, s in enumerate(spokes)],
        part(ring(0.0, 1.02, 0.290, 0.056), BRASS, "brake_rim"),
        part(oval(0.0, 1.02, 0.058, 0.058), BRASS, "brake_hub"),
    ]


def desk() -> list:
    """Столик кондуктора: ножки — линии, журнал — две выгнутые страницы."""
    leg_l = curve([smooth((-0.470, 0.010), -0.01, 0.20), smooth((-0.496, 0.660), 0.01, 0.10)], n=8)
    leg_r = curve([smooth((0.470, 0.010), 0.01, 0.20), smooth((0.496, 0.660), -0.01, 0.10)], n=8)
    brace = curve([smooth((-0.470, 0.150), 0.16, 0.010), smooth((0.0, 0.132), 0.16, 0.0), smooth((0.470, 0.150), 0.16, -0.010)], n=8)
    page_l = curve([
        smooth((-0.006, 0.788), -0.06, 0.006),
        smooth((-0.212, 0.802), -0.02, -0.02),
        smooth((-0.196, 0.782), 0.04, -0.006),
        smooth((-0.006, 0.772), 0.06, 0.004),
    ], n=8, closed=True)
    page_r = [(-x, y) for x, y in reversed(page_l)]
    quill = curve([smooth((0.336, 0.858), 0.02, 0.05), smooth((0.404, 1.002), 0.01, 0.04)], n=8)
    spike = curve([smooth((-0.450, 0.836), 0.004, 0.06), smooth((-0.444, 1.020), 0.0, 0.04)], n=6)
    return [
        part(stroke(leg_l, 0.070, 0.052), TEAK, "desk_leg_l"),
        part(stroke(leg_r, 0.070, 0.052), TEAK, "desk_leg_r"),
        part(stroke(brace, 0.038), TEAK_LINE, "desk_brace"),
        part(panel(0.678, 0.782, 1.140, 1.100, bow=0.008), TEAK_SOFT, "desk_top"),
        part(stroke(curve([smooth((-0.556, 0.694), 0.18, 0.004), smooth((0.0, 0.702), 0.18, 0.0), smooth((0.556, 0.694), 0.18, -0.004)], n=8), 0.016), TEAK_LINE, "desk_edge"),
        part(page_l, PAPER, "desk_page_l"),
        part(page_r, PAPER, "desk_page_r"),
        part(stroke(curve([smooth((0.0, 0.772), 0.004, 0.01), smooth((0.004, 0.800), 0.0, 0.01)], n=4), 0.014), PAPER_LINE, "desk_spine"),
        part(panel(0.782, 0.862, 0.120, 0.096, cx=0.348, bow=0.006), IRON, "desk_inkwell"),
        part(stroke(quill, 0.020, 0.010), PAPER, "desk_quill"),
        part(stroke(spike, 0.014), IRON_LINE, "desk_spike"),
        part(panel(0.930, 1.058, 0.170, 0.156, cx=-0.448, bow=0.010), PAPER, "desk_tickets"),
    ]


def regulator_clock() -> list:
    """Часы-регулятор: 20:30. Корпус и стрелки — линии."""
    return [
        part(stroke(curve([smooth((0.0, -0.400), 0.004, 0.10), smooth((0.006, -0.170), 0.0, 0.06)], n=6), 0.056), TEAK, "clock_stem"),
        part(oval(0.0, 0.0, 0.262, 0.268), TEAK, "clock_case"),
        part(oval(0.0, 0.0, 0.214, 0.218), [0.93, 0.89, 0.76], "clock_face"),
        part(ring(0.0, 0.0, 0.196, 0.014), [0.70, 0.64, 0.52], "clock_chapter"),
        part(stroke(curve([smooth((0.0, 0.0), 0.0, 0.05), smooth((-0.016, 0.152), 0.0, 0.04)], n=6), 0.026, 0.014), IRON, "clock_hour"),
        part(stroke(curve([smooth((0.0, 0.0), 0.04, -0.02), smooth((0.136, -0.078), 0.03, -0.02)], n=6), 0.020, 0.010), IRON, "clock_minute"),
        part(oval(0.0, 0.0, 0.024, 0.024), BRASS, "clock_pin"),
    ]


def hanging_lamp(drop: float = 0.62) -> list:
    """Лампа: шнур — линия, абажур — колокол из кривых."""
    cord = curve([smooth((0.0, drop), 0.004, -0.20), smooth((0.008, drop * 0.4), 0.0, -0.20), smooth((0.0, 0.0), -0.004, -0.10)], n=8)
    shade = curve([
        smooth((-0.196, -0.146), 0.02, 0.05),
        smooth((-0.104, -0.016), 0.06, 0.02),
        smooth((0.104, -0.016), 0.05, -0.02),
        smooth((0.196, -0.146), 0.02, -0.05),
    ], n=8)
    shade.append((-0.196, -0.146))
    return [
        part(stroke(cord, 0.016, 0.020), IRON, "lamp_cord"),
        part(shade, IRON, "lamp_shade"),
        part(stroke(arc(0.0, -0.150, 0.190, 0.028, math.pi * 1.02, math.pi * 1.98), 0.016), BRASS_DIM, "lamp_shade_edge"),
        part(oval(0.0, -0.206, 0.114, 0.100), LAMP_GLASS, "lamp_glass"),
        part(stroke(arc(0.0, -0.206, 0.062, 0.056, math.pi * 0.2, math.pi * 1.6), 0.020), [1.0, 0.82, 0.42], "lamp_flame"),
    ]


def shelf(tiers: int, w: float, h: float, load: list) -> list:
    """Стеллаж: стойки-линии, доски, мягкие мешки — светлый груз на светлой стене."""
    post_l = curve([smooth((-w / 2, 0.0), -0.006, h * 0.3), smooth((-w / 2 - 0.012, h), 0.004, h * 0.2)], n=8)
    post_r = [(-x, y) for x, y in post_l]
    parts = [part(stroke(post_l, 0.086, 0.070), TEAK, "shelf_post_l"),
             part(stroke(post_r, 0.086, 0.070), TEAK, "shelf_post_r")]
    for i in range(tiers):
        y = h * (i + 1) / (tiers + 1)
        parts.append(part(panel(y, y + 0.046, w + 0.02, w, bow=0.004), TEAK_SOFT, "shelf_board_%d" % i))
        c = load[i % len(load)]
        bw = w * (0.34 + 0.10 * (i % 3))
        cx = (-1) ** i * w * 0.16
        parts.append(part(blob(cx, y + 0.046 + h * 0.075, bw * 0.52, h * 0.078, 0.14, 1.0 + i, 7), c, "shelf_load_%d" % i))
        parts.append(part(stroke(arc(cx, y + 0.046 + h * 0.075, bw * 0.40, h * 0.050, math.pi * 1.1, math.pi * 1.9), 0.014), SACK_LINE, "shelf_load_line_%d" % i))
        parts.append(part(panel(y + 0.062, y + 0.116, 0.10, 0.092, cx=cx + bw * 0.26, bow=0.004), PAPER, "shelf_label_%d" % i))
    return parts


def mail_sacks() -> list:
    """Почтовые мешки: мягкие кривые, горловина перевязана линией."""
    return [
        part(blob(-0.300, 0.278, 0.300, 0.278, 0.14, 1.0, 8), SACK, "sack_a"),
        part(blob(0.340, 0.240, 0.262, 0.240, 0.12, 4.0, 8), SACK_2, "sack_b"),
        part(stroke(arc(-0.300, 0.278, 0.244, 0.204, math.pi * 1.05, math.pi * 1.95), 0.020), SACK_LINE, "sack_a_line"),
        part(stroke(arc(0.340, 0.240, 0.208, 0.176, math.pi * 1.05, math.pi * 1.95), 0.018), SACK_LINE, "sack_b_line"),
        part(blob(-0.244, 0.508, 0.126, 0.108, 0.16, 7.0, 7), SACK, "sack_a_neck"),
        part(stroke(arc(-0.244, 0.452, 0.100, 0.040, math.pi * 0.06, math.pi * 0.94), 0.026), [0.36, 0.28, 0.18], "sack_a_tie"),
        part(panel(0.300, 0.382, 0.106, 0.098, cx=-0.290, bow=0.004), PAPER, "sack_a_tag"),
        part(panel(0.256, 0.330, 0.100, 0.092, cx=0.330, bow=0.004), PAPER, "sack_b_tag"),
    ]


def crates() -> list:
    """Ящики: доски и обвязка — верёвка идёт линией через угол."""
    rope = curve([
        smooth((-0.220, 0.560), 0.12, 0.02),
        smooth((0.180, 0.600), 0.06, 0.04),
        smooth((0.300, 0.760), -0.01, 0.06),
    ], n=10)
    return [
        part(panel(0.0, 0.520, 0.920, 0.880, bow=0.010), CRATE, "crate_low"),
        part(stroke(curve([smooth((-0.450, 0.262), 0.15, 0.004), smooth((0.450, 0.270), 0.15, -0.004)], n=8), 0.046), TEAK_SOFT, "crate_low_band"),
        part(panel(0.520, 0.920, 0.640, 0.600, cx=0.090, bow=0.008), CRATE, "crate_high"),
        part(stroke(curve([smooth((-0.220, 0.716), 0.12, 0.004), smooth((0.400, 0.722), 0.12, -0.004)], n=8), 0.040), TEAK_SOFT, "crate_high_band"),
        part(stroke(rope, 0.024, 0.018), [0.62, 0.54, 0.36], "crate_rope"),
        part(panel(0.600, 0.686, 0.260, 0.244, cx=0.030, bow=0.004), PAPER, "crate_stencil"),
    ]


def trunk_stack() -> list:
    """Сундуки: крышка выгнута дугой, ремни — линии."""
    return [
        part(panel(0.0, 0.340, 0.960, 0.930, bow=0.012), [0.30, 0.26, 0.24], "trunk_low"),
        part(cap(0.0, 0.336, 0.470, 0.104, 0.0, math.pi), [0.35, 0.31, 0.29], "trunk_low_lid"),
        part(stroke(arc(0.0, 0.336, 0.470, 0.104, 0.0, math.pi), 0.024), [0.22, 0.19, 0.18], "trunk_low_lid_line"),
        part(stroke(curve([smooth((-0.462, 0.166), 0.16, 0.004), smooth((0.462, 0.172), 0.16, -0.004)], n=8), 0.044), BRASS_DIM, "trunk_low_strap"),
        part(panel(0.440, 0.700, 0.680, 0.650, bow=0.010), [0.24, 0.21, 0.20], "trunk_high"),
        part(cap(0.0, 0.698, 0.330, 0.072, 0.0, math.pi), [0.28, 0.25, 0.24], "trunk_high_lid"),
        part(stroke(curve([smooth((-0.320, 0.566), 0.11, 0.004), smooth((0.320, 0.572), 0.11, -0.004)], n=8), 0.036), BRASS, "trunk_high_strap"),
    ]


def coffin() -> list:
    """Гроб под пломбой: бока чуть выгнуты, сургуч — пятно."""
    body = curve([
        smooth((-0.860, 0.006), 0.28, 0.0),
        smooth((0.860, 0.006), 0.10, 0.02),
        smooth((0.724, 0.360), -0.24, 0.0),
        smooth((-0.724, 0.360), -0.10, -0.02),
    ], n=8, closed=True)
    return [
        part(body, TEAK, "coffin_body"),
        part(panel(0.352, 0.424, 1.540, 1.480, bow=0.010), TEAK_SOFT, "coffin_lid"),
        part(stroke(curve([smooth((-0.700, 0.180), 0.24, 0.010), smooth((0.700, 0.196), 0.24, -0.010)], n=8), 0.020), TEAK_LINE, "coffin_line"),
        part(oval(0.0, 0.446, 0.076, 0.044), [0.62, 0.16, 0.14], "coffin_seal"),
    ]


def broom() -> list:
    """Метла у стены: черенок — одна линия, прутья — веер линий."""
    stick = curve([
        smooth((0.010, 0.180), 0.020, 0.40),
        smooth((0.080, 0.860), 0.014, 0.30),
        smooth((0.104, 1.420), -0.006, 0.10),
    ], n=10)
    bristles = []
    for i in range(7):
        t = (i - 3) / 3.0
        bristles.append(curve([smooth((0.010 + t * 0.020, 0.200), t * 0.02, -0.06),
                               smooth((t * 0.110, 0.006), t * 0.03, -0.04)], n=6))
    return [
        *[part(stroke(b, 0.030, 0.016), [0.62, 0.52, 0.30] if i % 2 else [0.52, 0.43, 0.24], "broom_bristle_%d" % i)
          for i, b in enumerate(bristles)],
        part(stroke(stick, 0.034, 0.024), TEAK_SOFT, "broom_stick"),
        part(stroke(arc(0.012, 0.226, 0.070, 0.024, math.pi * 0.05, math.pi * 0.95), 0.024), [0.42, 0.34, 0.20], "broom_tie"),
    ]


def bucket() -> list:
    """Ведро: бок — кривая, дужка — дуга-линия."""
    body = side([
        (-0.118, 0.000, -0.014, 0.06),
        (-0.140, 0.140,  0.006, 0.06),
        (-0.152, 0.276,  0.000, 0.01),
    ], n=10)
    return [
        part(body, IRON, "bucket_body"),
        part(ering(0.0, 0.276, 0.152, 0.040, 0.024), [0.28, 0.28, 0.30], "bucket_rim"),
        part(stroke(arc(0.0, 0.286, 0.146, 0.140, math.pi * 0.06, math.pi * 0.94), 0.018), [0.30, 0.30, 0.32], "bucket_handle"),
        part(stroke(curve([smooth((-0.132, 0.140), 0.09, 0.004), smooth((0.132, 0.146), 0.09, -0.004)], n=8), 0.016), IRON_LINE, "bucket_band"),
    ]


def hooks_wall() -> list:
    """Крюки со снаряжением: чагул, куртка, виток верёвки, фонарь."""
    def hook(x: float) -> list:
        return curve([smooth((x, 1.720), 0.0, -0.04),
                      smooth((x + 0.026, 1.632), 0.02, -0.02),
                      smooth((x + 0.004, 1.588), -0.02, -0.01)], n=8)
    jacket = curve([
        smooth((-0.300, 1.196), 0.02, 0.10),
        smooth((-0.322, 1.480), 0.04, 0.06),
        smooth((-0.160, 1.632), 0.09, 0.00),
        smooth((0.002, 1.480), 0.01, -0.06),
        smooth((-0.020, 1.196), -0.06, -0.06),
    ], n=9, closed=True)
    return [
        part(panel(1.716, 1.784, 1.420, 1.400, bow=0.006), TEAK_SOFT, "hooks_rail"),
        *[part(stroke(hook(x), 0.022, 0.016), BRASS, "hooks_hook_%d" % i) for i, x in enumerate([-0.520, -0.160, 0.240, 0.600])],
        part(blob(-0.520, 1.452, 0.110, 0.158, 0.12, 5.0, 7), [0.46, 0.33, 0.20], "hooks_waterskin"),
        part(stroke(arc(-0.520, 1.586, 0.052, 0.030, math.pi * 0.05, math.pi * 0.95), 0.022), [0.34, 0.24, 0.14], "hooks_waterskin_neck"),
        part(jacket, KHAKI, "hooks_jacket"),
        part(stroke(curve([smooth((-0.162, 1.612), 0.004, -0.09), smooth((-0.152, 1.230), 0.0, -0.06)], n=8), 0.014), KHAKI_FOLD, "hooks_jacket_seam"),
        part(ring(0.240, 1.442, 0.108, 0.046), [0.52, 0.44, 0.29], "hooks_rope_1"),
        part(ring(0.240, 1.442, 0.062, 0.038), [0.44, 0.37, 0.24], "hooks_rope_2"),
        part(panel(1.352, 1.582, 0.170, 0.150, cx=0.600, bow=0.006), IRON, "hooks_lantern"),
        part(panel(1.396, 1.526, 0.116, 0.108, cx=0.600, bow=0.004), LAMP_GLASS, "hooks_lantern_glass"),
        part(stroke(arc(0.600, 1.586, 0.058, 0.036, math.pi * 0.08, math.pi * 0.92), 0.014), IRON_LINE, "hooks_lantern_bail"),
    ]


def notice_board() -> list:
    """Доска объявлений: бумаги приколоты чуть косо, кнопки — точки."""
    def sheet(cx, cy, w, hgt, tilt):
        c, s = math.cos(tilt), math.sin(tilt)
        raw = panel(-hgt / 2, hgt / 2, w, w * 0.96, bow=0.006)
        return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in raw]
    return [
        part(panel(0.0, 0.462, 0.700, 0.680, bow=0.008), TEAK_SOFT, "notice_board"),
        part(stroke(curve([smooth((-0.336, 0.436), 0.11, 0.004), smooth((0.336, 0.442), 0.11, -0.004)], n=8), 0.018), TEAK_LINE, "notice_edge"),
        part(sheet(-0.150, 0.238, 0.260, 0.330, 0.05), PAPER, "notice_sheet_a"),
        part(sheet(0.152, 0.232, 0.250, 0.210, -0.07), [0.86, 0.82, 0.70], "notice_sheet_b"),
        part(sheet(0.140, 0.386, 0.200, 0.080, 0.10), [0.78, 0.74, 0.62], "notice_sheet_c"),
        *[part(oval(x, y, 0.016, 0.016), BRASS, "notice_pin_%d" % i)
          for i, (x, y) in enumerate([(-0.150, 0.386), (0.152, 0.324), (0.140, 0.418)])],
        *[part(stroke(curve([smooth((-0.250, 0.300 - i * 0.048), 0.05, 0.002), smooth((-0.056, 0.302 - i * 0.048), 0.05, -0.002)], n=6), 0.010), PAPER_LINE, "notice_text_%d" % i)
          for i in range(4)],
    ]


def window_night() -> list:
    """Окно: за ним не чернота, а ночной город — крыши и купол линией."""
    skyline = curve([
        smooth((-0.620, 0.060), 0.06, 0.00),
        smooth((-0.470, 0.240), 0.05, 0.00),
        smooth((-0.330, 0.170), 0.05, 0.02),
        smooth((-0.170, 0.320), 0.04, 0.06),
        smooth((-0.050, 0.400), 0.06, 0.00),
        smooth((0.070, 0.300), 0.04, -0.04),
        smooth((0.200, 0.230), 0.05, 0.00),
        smooth((0.330, 0.480), 0.03, 0.00),
        smooth((0.440, 0.210), 0.04, -0.02),
        smooth((0.620, 0.150), 0.05, 0.00),
    ], n=10)
    skyline = skyline + [(0.620, 0.0), (-0.620, 0.0)]
    return [
        part(panel(0.0, 0.920, 1.240, 1.240), NIGHT_SKY, "win_sky"),
        part(oval(0.300, 0.700, 0.086, 0.086), [0.72, 0.72, 0.62], "win_moon"),
        part(skyline, NIGHT_ROOF, "win_skyline"),
        part(stroke(arc(0.330, 0.470, 0.070, 0.058, math.pi * 0.02, math.pi * 0.98), 0.024), [0.20, 0.22, 0.30], "win_dome"),
        *[part(panel(y, y + hh, w, w, cx=x), NIGHT_GLOW, "win_glow_%d" % i)
          for i, (x, y, w, hh) in enumerate([(-0.360, 0.100, 0.070, 0.090), (-0.062, 0.120, 0.060, 0.080),
                                             (0.196, 0.090, 0.056, 0.070), (0.430, 0.070, 0.050, 0.060)])],
        part(stroke(curve([smooth((-0.660, -0.020), 0.22, 0.0), smooth((0.660, -0.020), 0.22, 0.0)], n=6), 0.056), TEAK, "win_sill"),
        part(stroke(curve([smooth((-0.660, 0.940), 0.22, 0.0), smooth((0.660, 0.940), 0.22, 0.0)], n=6), 0.048), TEAK, "win_head"),
        part(stroke(curve([smooth((0.0, -0.010), 0.0, 0.30), smooth((0.0, 0.930), 0.0, 0.20)], n=6), 0.044), TEAK, "win_mullion"),
    ]


def roof_rib(w: float = 5.76, top: float = 3.58, rise: float = 0.34) -> list:
    """Ребро крыши: дуга от стены до стены. Ряд рёбер и даёт коридор."""
    a = arc(0.0, top - rise, w / 2, rise, math.pi, 0.0, 22)
    return [part(stroke(a, 0.115, 0.115), TEAK, "rib"),
            part(stroke(a, 0.032, 0.032), TEAK_LINE, "rib_line")]


def gallery_post(h: float = 2.02) -> list:
    """Стойка мостков: линия от пола до настила, с косынкой."""
    stem = curve([smooth((0.0, 0.0), 0.006, h * 0.35), smooth((0.024, h), -0.004, h * 0.2)], n=8)
    knee = curve([smooth((0.020, h - 0.34), 0.10, 0.06), smooth((0.300, h - 0.02), 0.06, 0.02)], n=8)
    return [part(stroke(stem, 0.088, 0.070), TEAK, "post_stem"),
            part(stroke(knee, 0.040, 0.026), TEAK, "post_knee")]


def berth() -> list:
    """Откидная койка: настил, кронштейны-линии, скатанная постель."""
    strut_a = curve([smooth((-0.760, 0.640), 0.10, -0.10), smooth((-0.560, 0.360), 0.06, -0.12)], n=8)
    strut_b = curve([smooth((0.760, 0.640), -0.10, -0.10), smooth((0.560, 0.360), -0.06, -0.12)], n=8)
    return [
        part(stroke(strut_a, 0.044, 0.034), TEAK, "berth_strut_a"),
        part(stroke(strut_b, 0.044, 0.034), TEAK, "berth_strut_b"),
        part(panel(0.600, 0.660, 1.900, 1.860, bow=0.010), TEAK_SOFT, "berth_deck"),
        part(stroke(curve([smooth((-0.940, 0.606), 0.30, 0.004), smooth((0.940, 0.612), 0.30, -0.004)], n=8), 0.018), TEAK_LINE, "berth_edge"),
        part(blob(-0.700, 0.760, 0.185, 0.105, 0.10, 6.0, 7), [0.70, 0.62, 0.48], "berth_roll"),
        part(stroke(arc(-0.700, 0.760, 0.150, 0.078, math.pi * 0.10, math.pi * 0.90), 0.020), [0.54, 0.46, 0.34], "berth_roll_line"),
    ]


PROPS = [
    # id, контуры, положение, поворот
    ("stove",        stove(),            [-2.05, 0.0, -0.4],   None),
    ("brake_wheel",  brake_wheel(),      [2.22, 0.0, -0.5],    None),
    ("desk",         desk(),             [1.72, 0.0, -1.9],    None),
    ("clock_face",   regulator_clock(),  [2.62, 1.80, -2.1],   [0.0, -34.0, 0.0]),
    ("berth",        berth(),            [-2.08, 0.0, -1.55],  [0.0, 16.0, 0.0]),
    ("lamp_1",       hanging_lamp(0.92), [0.30, 3.56, -0.5],   None),
    ("lamp_2",       hanging_lamp(0.74), [-0.20, 3.56, -4.4],  None),
    ("lamp_3",       hanging_lamp(0.62), [0.10, 3.56, -8.8],   None),
    # Пламя в топке и чайник на плите: топка дышит, чайник чуть дрожит.
    ("stove_fire",   [part(oval(0.0, 0.430, 0.150, 0.140), EMBER, "fire_core"),
                      part(oval(0.0, 0.430, 0.092, 0.086), [1.0, 0.80, 0.36], "fire_hot")],
                     [-2.05, 0.0, -0.38], None),
    ("hooks",        hooks_wall(),       [-2.82, 0.0, 0.1],    [0.0, 58.0, 0.0]),
    ("notice",       notice_board(),     [2.78, 1.46, -0.3],   [0.0, -52.0, 0.0]),
    ("window",       window_night(),     [2.80, 1.40, -4.6],   [0.0, -76.0, 0.0]),
    ("mail_sacks",   mail_sacks(),       [-1.58, 0.0, -0.1],   None),
    ("crates",       crates(),           [1.94, 0.0, -0.2],    None),
    ("trunks",       trunk_stack(),      [-2.30, 0.0, -3.1],   [0.0, 24.0, 0.0]),
    ("coffin",       coffin(),           [-1.62, 0.0, -5.4],   [0.0, 62.0, 0.0]),
    ("broom",        broom(),            [2.56, 0.0, -0.6],    None),
    ("bucket",       bucket(),           [-2.50, 0.0, -0.7],   None),
    ("shelf_l_1",    shelf(3, 1.4, 2.1, [SACK, CRATE, SACK_2]),        [-2.34, 0.0, -3.2],  [0.0, 80.0, 0.0]),
    ("shelf_r_1",    shelf(3, 1.4, 2.1, [CRATE, SACK_2, CLOTH_RED]),   [2.34, 0.0, -3.8],   [0.0, -80.0, 0.0]),
    ("shelf_l_2",    shelf(4, 1.5, 2.2, [SACK_2, CLOTH_BLUE, CRATE, SACK]),  [-2.34, 0.0, -5.8], [0.0, 80.0, 0.0]),
    ("shelf_r_2",    shelf(4, 1.5, 2.2, [SACK, CRATE, SACK_2, CLOTH_RED]),   [2.34, 0.0, -6.6],  [0.0, -80.0, 0.0]),
    ("shelf_l_3",    shelf(4, 1.6, 2.3, [SACK_2, CRATE, SACK, CRATE]),       [-2.34, 0.0, -8.6], [0.0, 80.0, 0.0]),
    ("shelf_r_3",    shelf(4, 1.6, 2.3, [CRATE, SACK, CRATE, SACK_2]),       [2.34, 0.0, -9.6],  [0.0, -80.0, 0.0]),
    ("shelf_l_4",    shelf(5, 1.7, 2.4, [SACK_2, CRATE, SACK_2, CRATE, SACK]), [-2.34, 0.0, -11.8], [0.0, 80.0, 0.0]),
    ("shelf_r_4",    shelf(5, 1.7, 2.4, [CRATE, SACK_2, CRATE, SACK_2, CRATE]), [2.34, 0.0, -12.8], [0.0, -80.0, 0.0]),
    ("shelf_l_5",    shelf(5, 1.7, 2.5, [SACK, CRATE, SACK_2, CRATE, SACK_2]),   [-2.34, 0.0, -15.0], [0.0, 80.0, 0.0]),
    ("shelf_r_5",    shelf(5, 1.7, 2.5, [CRATE, SACK, CRATE, SACK_2, CRATE]),    [2.34, 0.0, -16.2],  [0.0, -80.0, 0.0]),
] + [
    # Рёбра крыши: ряд дуг, уходящий в глубину. Именно они делают из коробки
    # коридор — и они же показывают, что вагон длиннее, чем бывает вагон.
    ("rib_%d" % i, roof_rib(), [0.0, 0.0, z], None)
    for i, z in enumerate([1.1, -0.5, -2.1, -3.7, -5.3, -6.9, -8.5, -10.1, -11.7,
                           -13.3, -14.9, -16.5, -18.1])
] + [
    ("post_%s" % sid, gallery_post(), [x, 0.0, z], None)
    for sid, x, z in [("l1", -1.94, -2.6), ("r1", 1.94, -3.2), ("l2", -1.94, -5.4),
                      ("r2", 1.94, -6.0), ("l3", -1.94, -8.6), ("r3", 1.94, -9.4),
                      ("l4", -1.94, -12.0), ("r4", 1.94, -12.8), ("l5", -1.94, -15.4),
                      ("r5", 1.94, -16.2)]
]


# --- вечное движение ---------------------------------------------------------
# Не анимация сцен, а то движение, которое идёт всегда и говорит «поезд едет».
# Лампы висят на крюках и отстают от качки вагона, поэтому у каждой своя фаза
# и свой период — синхронные лампы читаются механизмом, а не подвесом.
PROP_MOTION = {
    "lamp_1": {"kind": "sway", "amp": [0.014, 0.0, 0.0],
               "rot_amp": [0.0, 0.0, 2.4], "period": 3.4},
    "lamp_2": {"kind": "sway", "amp": [0.011, 0.0, 0.0],
               "rot_amp": [0.0, 0.0, 2.0], "period": 4.1, "phase": 0.37},
    "lamp_3": {"kind": "sway", "amp": [0.009, 0.0, 0.0],
               "rot_amp": [0.0, 0.0, 1.7], "period": 2.8, "phase": 0.71},
    "stove_fire": {"kind": "flicker", "min": 0.86, "max": 1.0, "period": 0.38},
    "broom": {"kind": "sway", "rot_amp": [0.0, 0.0, 0.7], "period": 5.2, "phase": 0.2},
    "hooks": {"kind": "sway", "amp": [0.006, 0.0, 0.0], "period": 3.9, "phase": 0.55},
    "notice": {"kind": "sway", "rot_amp": [0.0, 0.0, 0.5], "period": 4.6, "phase": 0.8},
}


# --- постановка --------------------------------------------------------------

def stage() -> dict:
    """Разрез вагона: внутри светло и подробно, тёмное — только конструкция."""
    layers = []
    # Коридор нарезан по глубине: каждый следующий отрезок пола, стен и потолка
    # темнее предыдущего. Ближний план читается весь, дальний тонет.
    cuts = [2.4, 0.6, -1.0, -2.6, -4.2, -6.0, -8.0, -10.2, -12.6, -15.2, -18.0, -21.0]
    for i in range(len(cuts) - 1):
        z0, z1 = cuts[i], cuts[i + 1]
        zc, ln = (z0 + z1) / 2.0, z0 - z1
        layers += [
            {"id": "floor_%d" % i, "size": [5.8, ln], "pos": [0.0, 0.0, zc],
             "rot": [-90.0, 0.0, 0.0], "color": dim(FLOOR, zc)},
            {"id": "ceiling_%d" % i, "size": [5.8, ln], "pos": [0.0, 3.6, zc],
             "rot": [90.0, 0.0, 0.0], "color": dim(CEILING, zc)},
            {"id": "wall_l_%d" % i, "size": [ln, 3.6], "pos": [-2.9, 1.8, zc],
             "rot": [0.0, 90.0, 0.0], "color": dim(WALL_LIT, zc)},
            {"id": "wall_r_%d" % i, "size": [ln, 3.6], "pos": [2.9, 1.8, zc],
             "rot": [0.0, -90.0, 0.0], "color": dim(WALL_MID, zc)},
            {"id": "skirt_l_%d" % i, "size": [ln, 0.72], "pos": [-2.885, 0.36, zc],
             "rot": [0.0, 90.0, 0.0], "color": dim(WALL_DEEP, zc)},
            {"id": "skirt_r_%d" % i, "size": [ln, 0.72], "pos": [2.885, 0.36, zc],
             "rot": [0.0, -90.0, 0.0], "color": dim([0.34, 0.28, 0.21], zc)},
        ]
        if i < 6:   # обшивка и половицы — только там, где их видно
            for y in [1.04, 1.98, 2.86]:
                layers.append({"id": "board_l_%d_%d" % (i, int(y * 100)), "size": [ln, 0.045],
                               "pos": [-2.878, y, zc], "rot": [0.0, 90.0, 0.0],
                               "color": dim([0.57, 0.47, 0.33], zc)})
                layers.append({"id": "board_r_%d_%d" % (i, int(y * 100)), "size": [ln, 0.045],
                               "pos": [2.878, y, zc], "rot": [0.0, -90.0, 0.0],
                               "color": dim([0.45, 0.37, 0.26], zc)})
            for x in [-2.25, -1.5, -0.75, 0.0, 0.75, 1.5, 2.25]:
                layers.append({"id": "plank_%d_%d" % (i, int(x * 100)), "size": [0.045, ln],
                               "pos": [x, 0.012, zc], "rot": [-90.0, 0.0, 0.0],
                               "color": dim(FLOOR_LINE, zc)})
    layers += [
        # Замыкающая тьма и мостки второго уровня.
        {"id": "depth_far", "size": [11.0, 5.6], "pos": [0.0, 2.8, -21.2], "color": DEEP},
        {"id": "gallery_l", "size": [0.95, 13.0], "pos": [-2.40, 2.06, -8.6],
         "rot": [-90.0, 0.0, 0.0], "color": dim(TEAK_SOFT, -8.6)},
        {"id": "gallery_r", "size": [0.95, 13.0], "pos": [2.40, 2.06, -8.6],
         "rot": [-90.0, 0.0, 0.0], "color": dim(TEAK_SOFT, -8.6)},
        {"id": "gallery_beam_l", "size": [13.0, 0.13], "pos": [-1.92, 2.02, -8.6],
         "rot": [0.0, 90.0, 0.0], "color": dim(TEAK, -8.6)},
        {"id": "gallery_beam_r", "size": [13.0, 0.13], "pos": [1.92, 2.02, -8.6],
         "rot": [0.0, -90.0, 0.0], "color": dim(TEAK, -8.6)},
        {"id": "gallery_rail_l", "size": [13.0, 0.06], "pos": [-1.94, 2.72, -8.6],
         "rot": [0.0, 90.0, 0.0], "color": dim(TEAK, -8.6)},
        {"id": "gallery_rail_r", "size": [13.0, 0.06], "pos": [1.94, 2.72, -8.6],
         "rot": [0.0, -90.0, 0.0], "color": dim(TEAK, -8.6)},
    ]
    return {
        "_comment": ("Освещённый разрез вагона (ориентир — интерьер дома в Kentucky Route Zero): "
                     "внутри тепло и всё читается, тёмное — только конструкция и передний план. "
                     "Контуры рисует tools/draw_car_01.py кривыми и линиями; править форму — там, не в коде."),
        # Камера качается на рельсах: 1,2 см вверх-вниз и четверть градуса
        # крена. Этого хватает, чтобы кадр перестал быть картинкой, — и мало,
        # чтобы не мешать читать. Поезд идёт всегда (visual_direction §3).
        "camera": {"pos": [0.0, 1.66, 4.55], "rot": [-3.5, 0.0, 0.0],
                   "projection": "perspective", "fov": 38.0, "size": 4.2,
                   "motion": [{"kind": "bob", "amp": [0.0, 0.012, 0.0],
                               "rot_amp": [0.10, 0.0, 0.26], "period": 1.9},
                              {"kind": "bob", "amp": [0.004, 0.003, 0.0],
                               "period": 0.61, "phase": 0.3}]},
        "layers": layers,
        "props": [{"id": pid, "pos": pos, "parts": dimmed(parts, pos[2]),
                    **({"rot": rot} if rot else {}),
                    **({"motion": PROP_MOTION[pid]} if pid in PROP_MOTION else {})}
                  for pid, parts, pos, rot in PROPS],
        "pools": [
            {"id": "stove_pool", "size": [5.0, 5.0], "pos": [-1.4, 0.03, 0.6], "rot": [-90.0, 0.0, 0.0],
             "color": [1.0, 0.45, 0.16], "strength": 0.34,
             "motion": {"kind": "flicker", "min": 0.72, "max": 1.0, "period": 0.44}},
            {"id": "lamp_pool", "size": [7.0, 7.0], "pos": [0.0, 0.04, 0.4], "rot": [-90.0, 0.0, 0.0],
             "color": [1.0, 0.86, 0.60], "strength": 0.30,
             "motion": {"kind": "flicker", "min": 0.88, "max": 1.0, "period": 1.7}},
            {"id": "lamp_pool_ceiling", "size": [4.0, 4.0], "pos": [0.0, 3.54, 0.4], "rot": [90.0, 0.0, 0.0],
             "color": [1.0, 0.88, 0.64], "strength": 0.22,
             "motion": {"kind": "flicker", "min": 0.86, "max": 1.0, "period": 2.3, "phase": 0.4}},
        ],
    }


def lantern_pools() -> list:
    """Фонарь в руках: тёплое пятно, которое игрок носит с собой."""
    return [
        {"id": "lantern_pool", "size": [8.0, 8.0], "pos": [0.0, 0.05, 1.0], "rot": [-90.0, 0.0, 0.0],
         "color": [1.0, 0.80, 0.46], "strength": 0.42, "visible": False},
        {"id": "lantern_pool_left", "size": [5.0, 4.2], "pos": [-2.85, 1.5, 0.4], "rot": [0.0, 90.0, 0.0],
         "color": [1.0, 0.78, 0.44], "strength": 0.30, "visible": False},
        {"id": "lantern_pool_right", "size": [5.0, 4.2], "pos": [2.85, 1.5, -0.4], "rot": [0.0, -90.0, 0.0],
         "color": [1.0, 0.76, 0.42], "strength": 0.26, "visible": False},
        {"id": "lantern_pool_deep", "size": [7.0, 7.0], "pos": [0.0, 0.05, -5.2], "rot": [-90.0, 0.0, 0.0],
         "color": [1.0, 0.74, 0.40], "strength": 0.22, "visible": False},
    ]


def main() -> int:
    for npc_id, (shape, parts, pos, rot) in FIGURES.items():
        path = os.path.join(ROOT, "data", "npcs", npc_id + ".json")
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["silhouette"] = shape
        doc["position"] = pos
        # Человек в глубине вагона тоже гаснет: он не подсвечен отдельно от
        # воздуха, в котором стоит. Вернёт его фонарь, а не исключение в коде.
        doc["figure"] = {"id": npc_id + "_figure", "parts": dimmed(parts, pos[2])}
        if rot:
            doc["figure"]["rot"] = rot
        doc.pop("color", None)
        doc.pop("silhouette_parts", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)

    card_path = os.path.join(ROOT, "data", "cars", "car_01.json")
    with open(card_path, encoding="utf-8") as fh:
        card = json.load(fh)
    card["stage"] = stage()
    card["stage_lantern_pools"] = lantern_pools()
    with open(card_path, "w", encoding="utf-8") as fh:
        json.dump(card, fh, ensure_ascii=False, indent=2)

    figure_parts = sum(len(f[1]) for f in FIGURES.values())
    prop_parts = sum(len(p[1]) for p in PROPS)
    print("draw_car_01: фигур %d (%d контуров), реквизита %d (%d контуров), кулис %d"
          % (len(FIGURES), figure_parts, len(PROPS), prop_parts, len(card["stage"]["layers"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
