#!/usr/bin/env python3
"""draw_car_01.py — рисует вагон 01 и его население и пишет в данные.

Ориентир — Kentucky Route Zero, но конкретно: **освещённый изнутри разрез**.
Внутри вагона тепло и всё читается — стены, пол, полки, вещи; тёмное здесь
только конструкция (стойки, балки, рама) и передний план. Фон за окном не
чёрный. Люди видны людьми: у каждого цвет кожи, одежды и волос, поза и вещь
в руках. Лиц нет (docs/visual_direction.md §3) — человек узнаётся одеждой.

Всё, что рисует этот скрипт, — данные: `data/cars/car_01.json` (постановка) и
`data/npcs/*.json` (фигуры). Движок только рисует контуры (StageBuilder).

Запуск: python tools/draw_car_01.py
"""
from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda v: round(v, 4)

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
BRASS       = [0.72, 0.58, 0.24]
IRON        = [0.15, 0.145, 0.15]
PAPER       = [0.94, 0.90, 0.78]
SACK        = [0.66, 0.56, 0.38]
SACK_2      = [0.56, 0.47, 0.32]
CRATE       = [0.48, 0.34, 0.21]
CLOTH_RED   = [0.62, 0.20, 0.16]
CLOTH_BLUE  = [0.20, 0.28, 0.46]
EMBER       = [1.00, 0.55, 0.18]
LAMP_GLASS  = [1.00, 0.94, 0.74]
NIGHT_CITY  = [0.20, 0.26, 0.36]     # за окном не чёрное: город и небо
NIGHT_GLOW  = [0.42, 0.40, 0.34]

# --- цвета людей -------------------------------------------------------------
SKIN        = [0.52, 0.34, 0.22]
SKIN_DARK   = [0.40, 0.26, 0.17]
HAIR        = [0.09, 0.07, 0.07]
GREY_HAIR   = [0.80, 0.78, 0.74]
WHITE_CLOTH = [0.88, 0.85, 0.78]
KHAKI       = [0.58, 0.50, 0.32]
TURBAN_BLUE = [0.18, 0.26, 0.48]
INDIGO      = [0.115, 0.115, 0.175]
SARI_RED    = [0.70, 0.19, 0.17]
SARI_GOLD   = [0.78, 0.62, 0.24]
RAG_GREY    = [0.44, 0.42, 0.37]
DOG_TAN     = [0.46, 0.34, 0.22]


# --- примитивы ---------------------------------------------------------------

def circle(cx: float, cy: float, r: float, n: int = 22) -> list:
    return [[R(cx + r * math.cos(math.tau * i / n)), R(cy + r * math.sin(math.tau * i / n))] for i in range(n)]


def ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 26,
            a0: float = 0.0, a1: float = math.tau) -> list:
    return [[R(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1))),
             R(cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1)))] for i in range(n)]


def box(x0: float, y0: float, x1: float, y1: float) -> list:
    return [[R(x0), R(y0)], [R(x1), R(y0)], [R(x1), R(y1)], [R(x0), R(y1)]]


def taper(y0: float, w0: float, y1: float, w1: float, cx: float = 0.0) -> list:
    return [[R(cx - w0 / 2), R(y0)], [R(cx + w0 / 2), R(y0)], [R(cx + w1 / 2), R(y1)], [R(cx - w1 / 2), R(y1)]]


def limb(x0: float, y0: float, x1: float, y1: float, w: float) -> list:
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d * w / 2, dx / d * w / 2
    return [[R(x0 + nx), R(y0 + ny)], [R(x1 + nx), R(y1 + ny)], [R(x1 - nx), R(y1 - ny)], [R(x0 - nx), R(y0 - ny)]]


def part(points: list, color: list) -> dict:
    return {"points": points, "color": color}


# --- фигуры ------------------------------------------------------------------
# Пропорции: голова ≈ 1/7.5 роста. Одежда — единственный способ узнать человека,
# поэтому цвет и крой в очертании. Лиц нет; волосы и головной убор есть.

def head(cy: float, r: float, skin: list = SKIN, hair: list | None = HAIR) -> list:
    parts = [part(circle(0.0, cy, r), skin)]
    if hair:
        parts.append(part(ellipse(0.0, cy + r * 0.32, r * 1.02, r * 0.72, 20, math.pi * 0.02, math.pi * 0.98), hair))
    return parts


def shani(h: float = 1.74) -> list:
    """Присутствие: тёмное индиго до земли, тень вместо лица, трость.
    Единственный, кто остаётся почти чёрным — он и есть тень в этом вагоне."""
    return [
        part(taper(0.0, 0.26 * h, 0.58 * h, 0.22 * h), INDIGO),
        part(taper(0.56 * h, 0.23 * h, 0.79 * h, 0.26 * h), INDIGO),
        part(taper(0.78 * h, 0.30 * h, 0.86 * h, 0.135 * h), INDIGO),
        *head(0.915 * h, 0.062 * h, SKIN_DARK, None),
        part(ellipse(0.0, 0.945 * h, 0.082 * h, 0.052 * h), [0.09, 0.09, 0.14]),   # повязка
        part(limb(0.125 * h, 0.78 * h, 0.165 * h, 0.40 * h, 0.052 * h), INDIGO),
        part(limb(-0.125 * h, 0.78 * h, -0.155 * h, 0.42 * h, 0.052 * h), INDIGO),
        part(limb(0.185 * h, 0.44 * h, 0.205 * h, 0.0, 0.020 * h), TEAK),          # трость
        part(circle(0.168 * h, 0.415 * h, 0.028 * h), SKIN),                       # кисть на трости
        part(circle(-0.158 * h, 0.425 * h, 0.026 * h), SKIN),
    ]


def bir_singh(l: float = 1.72) -> list:
    """Спит на койке: тюрбан, форменная куртка. Горизонталь — он не встанет."""
    return [
        part(box(-0.46 * l, 0.02, 0.30 * l, 0.19), KHAKI),        # тело под курткой
        part(box(-0.50 * l, 0.02, -0.44 * l, 0.15), WHITE_CLOTH), # штанина
        part(ellipse(0.36 * l, 0.16, 0.075 * l, 0.075), SKIN),    # голова
        part(ellipse(0.42 * l, 0.20, 0.070 * l, 0.062), TURBAN_BLUE),
        part(ellipse(0.30 * l, 0.13, 0.035 * l, 0.045), GREY_HAIR),  # борода
        part(limb(-0.10 * l, 0.19, 0.10 * l, 0.14, 0.055), KHAKI),
    ]


def ratan(h: float = 1.60) -> list:
    """Сидит у печки, белое дхоти, бурый жилет, седая голова."""
    return [
        part(taper(0.0, 0.34 * h, 0.24 * h, 0.30 * h), WHITE_CLOTH),             # подобранные ноги
        part(taper(0.23 * h, 0.28 * h, 0.50 * h, 0.26 * h), WHITE_CLOTH),        # дхоти
        part(taper(0.36 * h, 0.27 * h, 0.56 * h, 0.24 * h), [0.36, 0.25, 0.16]), # жилет на корпусе
        part(taper(0.55 * h, 0.16 * h, 0.61 * h, 0.10 * h), SKIN),               # шея
        *head(0.665 * h, 0.058 * h, SKIN, GREY_HAIR),
        part(limb(0.12 * h, 0.50 * h, 0.24 * h, 0.30 * h, 0.044 * h), SKIN),     # рука к огню
        part(limb(-0.12 * h, 0.48 * h, -0.17 * h, 0.32 * h, 0.044 * h), SKIN),
    ]


def hafiz(h: float = 1.54) -> list:
    """Паломник спит сидя: белая курта, топи, седая борода, чётки."""
    return [
        part(taper(0.0, 0.40 * h, 0.26 * h, 0.34 * h), WHITE_CLOTH),
        part(taper(0.25 * h, 0.32 * h, 0.56 * h, 0.28 * h), WHITE_CLOTH),
        part(taper(0.55 * h, 0.15 * h, 0.61 * h, 0.10 * h), SKIN),
        *head(0.668 * h, 0.058 * h, SKIN, None),
        part(ellipse(0.0, 0.626 * h, 0.050 * h, 0.048 * h), GREY_HAIR),          # борода
        part(taper(0.715 * h, 0.128 * h, 0.755 * h, 0.112 * h), WHITE_CLOTH),    # топи
        part(limb(-0.13 * h, 0.50 * h, -0.09 * h, 0.30 * h, 0.042 * h), SKIN),
        part(circle(-0.09 * h, 0.28 * h, 0.026 * h), [0.30, 0.20, 0.12]),        # чётки
    ]


def saraswati(h: float = 1.62) -> list:
    """Сари: красное с золотой каймой, паллу через плечо, судки в руке.
    Она — самое яркое пятно вагона: город цветной, и она из города."""
    return [
        part(taper(0.0, 0.42 * h, 0.52 * h, 0.25 * h), SARI_RED),
        part(taper(0.0, 0.42 * h, 0.045 * h, 0.415 * h), SARI_GOLD),             # кайма подола
        part(taper(0.50 * h, 0.25 * h, 0.78 * h, 0.24 * h), SARI_RED),
        part(taper(0.77 * h, 0.25 * h, 0.85 * h, 0.115 * h), SKIN),
        *head(0.915 * h, 0.060 * h, SKIN, HAIR),
        part(ellipse(0.0, 0.945 * h, 0.098 * h, 0.052 * h), SARI_RED),           # покрытая голова
        part([[R(0.095 * h), R(0.84 * h)], [R(0.215 * h), R(0.56 * h)],
              [R(0.125 * h), R(0.22 * h)], [R(0.02 * h), R(0.24 * h)],
              [R(0.055 * h), R(0.60 * h)]], SARI_GOLD),                          # паллу
        part(limb(-0.115 * h, 0.78 * h, -0.165 * h, 0.50 * h, 0.046 * h), SKIN),
        part(taper(0.42 * h, 0.105 * h, 0.50 * h, 0.10 * h, cx=-0.185 * h), BRASS),   # судки
    ]


def monimala(h: float = 1.58) -> list:
    """Вдова: белое сари без каймы, глиняная урна в руках."""
    return [
        part(taper(0.0, 0.42 * h, 0.54 * h, 0.25 * h), WHITE_CLOTH),
        part(taper(0.52 * h, 0.25 * h, 0.80 * h, 0.25 * h), WHITE_CLOTH),
        part(taper(0.79 * h, 0.26 * h, 0.86 * h, 0.115 * h), SKIN),
        *head(0.925 * h, 0.060 * h, SKIN, HAIR),
        part(ellipse(0.0, 0.955 * h, 0.10 * h, 0.056 * h), WHITE_CLOTH),
        part(ellipse(0.0, 0.50 * h, 0.082 * h, 0.098 * h), [0.42, 0.26, 0.16]),  # урна
        part(ellipse(0.0, 0.585 * h, 0.048 * h, 0.024 * h), WHITE_CLOTH),        # белая ткань на урне
        part(limb(-0.10 * h, 0.72 * h, -0.055 * h, 0.53 * h, 0.044 * h), SKIN),
        part(limb(0.10 * h, 0.72 * h, 0.055 * h, 0.53 * h, 0.044 * h), SKIN),
    ]


def kanu(h: float = 1.26) -> list:
    """Мальчик-безбилетник: серые штаны, голый торс, латхи."""
    return [
        part(taper(0.0, 0.38 * h, 0.30 * h, 0.32 * h), RAG_GREY),
        part(taper(0.29 * h, 0.30 * h, 0.60 * h, 0.26 * h), SKIN),
        part(taper(0.59 * h, 0.26 * h, 0.66 * h, 0.10 * h), SKIN),
        *head(0.735 * h, 0.072 * h, SKIN, HAIR),
        part(limb(0.12 * h, 0.58 * h, 0.19 * h, 0.30 * h, 0.042 * h), SKIN),
        part(limb(-0.12 * h, 0.58 * h, -0.17 * h, 0.32 * h, 0.042 * h), SKIN),
        part(limb(0.20 * h, 0.66 * h, 0.22 * h, 0.02 * h, 0.016 * h), TEAK_SOFT),   # латхи
    ]


def dog_figure() -> list:
    return [
        part(taper(0.24, 0.60, 0.44, 0.52), DOG_TAN),
        part(ellipse(0.32, 0.50, 0.098, 0.082), DOG_TAN),
        part([[0.40, 0.50], [0.51, 0.47], [0.42, 0.42]], DOG_TAN),
        part([[0.26, 0.58], [0.32, 0.66], [0.34, 0.56]], [0.34, 0.24, 0.15]),
        part(limb(0.20, 0.24, 0.20, 0.0, 0.048), DOG_TAN),
        part(limb(-0.20, 0.24, -0.22, 0.0, 0.048), DOG_TAN),
        part(limb(-0.28, 0.40, -0.42, 0.52, 0.032), DOG_TAN),
    ]


FIGURES = {
    "god_shani": ("indigo_robe", shani(), [0.95, 0.0, -2.2], None),
    "npc_bir_singh": ("sleeping_turban", bir_singh(), [-1.86, 0.62, -1.8], [0.0, 90.0, 0.0]),
    "npc_ratan": ("seated_dhoti", ratan(), [-1.05, 0.0, 1.25], None),
    "npc_hafiz": ("seated_topi", hafiz(), [-2.15, 0.0, -2.6], None),
    "npc_saraswati": ("sari_red", saraswati(), [1.35, 0.0, 1.1], None),
    "npc_monimala": ("widow_white", monimala(), [-0.5, 0.0, 1.9], None),
    "npc_kanu": ("boy_lathi", kanu(), [1.62, 0.0, -2.4], None),
    "npc_dog": ("dog", dog_figure(), [-0.55, 0.0, 0.4], None),
}


# --- реквизит ----------------------------------------------------------------
# Деталей должно быть много: по ним читается, где мы. Всё — от земли вверх.

def stove() -> list:
    return [
        part(box(-0.31, 0.0, 0.31, 0.86), IRON),
        part(box(-0.34, 0.84, 0.34, 0.94), IRON),
        part(circle(0.0, 0.42, 0.155, 18), EMBER),                 # открытая топка
        part(circle(0.0, 0.42, 0.175, 18), [0.55, 0.22, 0.08]),    # обод топки
        part(box(-0.06, 0.94, 0.06, 2.62), IRON),                  # труба
        part(box(-0.20, 0.94, 0.20, 1.02), IRON),                  # плита
        part(ellipse(0.0, 1.12, 0.13, 0.10), BRASS),               # чайник
        part(box(0.10, 1.12, 0.20, 1.16), BRASS),                  # носик
        part(box(-0.62, 0.0, -0.38, 0.34), CRATE),                 # дрова
        part(box(-0.60, 0.34, -0.40, 0.40), TEAK_SOFT),
    ]


def brake_wheel() -> list:
    ring = ellipse(0.0, 1.02, 0.30, 0.30, 26)
    return [
        part(ring, BRASS),
        part(circle(0.0, 1.02, 0.20, 20), WALL_LIT),                # просвет колеса
        part(limb(-0.28, 1.02, 0.28, 1.02, 0.045), BRASS),          # спицы
        part(limb(0.0, 0.74, 0.0, 1.30, 0.045), BRASS),
        part(limb(0.0, 0.0, 0.0, 1.02, 0.10), IRON),                # колонка
        part(box(-0.16, 0.0, 0.16, 0.08), IRON),                    # основание
    ]


def desk() -> list:
    return [
        part(box(-0.56, 0.68, 0.56, 0.78), TEAK_SOFT),              # столешница
        part(box(-0.52, 0.0, -0.44, 0.68), TEAK),
        part(box(0.44, 0.0, 0.52, 0.68), TEAK),
        part(box(-0.44, 0.10, 0.44, 0.18), TEAK),
        part([[-0.20, 0.78], [0.20, 0.78], [0.22, 0.90], [-0.18, 0.90]], PAPER),   # раскрытый журнал
        part([[0.0, 0.79], [0.02, 0.89]], PAPER) if False else part(box(-0.005, 0.79, 0.01, 0.895), [0.72, 0.68, 0.58]),
        part(box(0.30, 0.78, 0.40, 0.86), IRON),                    # чернильница
        part(limb(0.34, 0.86, 0.40, 1.00, 0.014), PAPER),           # перо
        part(box(-0.50, 0.78, -0.40, 0.84), BRASS),                 # штырь с билетами
        part(limb(-0.45, 0.84, -0.45, 1.02, 0.012), IRON),
        part(box(-0.53, 0.94, -0.37, 1.06), PAPER),
    ]


def regulator_clock() -> list:
    return [
        part(circle(0.0, 0.0, 0.26, 26), TEAK),
        part(circle(0.0, 0.0, 0.215, 26), [0.93, 0.89, 0.76]),
        part(limb(0.0, 0.0, 0.0, 0.155, 0.024), IRON),              # часовая — 20:30
        part(limb(0.0, 0.0, 0.135, -0.075, 0.020), IRON),
        part(circle(0.0, 0.0, 0.022, 12), BRASS),
        part(box(-0.03, -0.42, 0.03, -0.16), TEAK),                 # подвес
    ]


def hanging_lamp(drop: float = 0.62) -> list:
    return [
        part(box(-0.012, 0.0, 0.012, drop), IRON),                          # шнур
        part([[-0.20, -0.14], [0.20, -0.14], [0.10, 0.0], [-0.10, 0.0]], IRON),   # абажур
        part(ellipse(0.0, -0.20, 0.115, 0.10), LAMP_GLASS),                 # стекло
    ]


def shelf(tiers: int, w: float, h: float, load: list) -> list:
    """Стеллаж: тёмная конструкция, светлый груз — читается на светлой стене."""
    parts = [part(box(-w / 2 - 0.04, 0.0, -w / 2 + 0.04, h), TEAK),
             part(box(w / 2 - 0.04, 0.0, w / 2 + 0.04, h), TEAK)]
    for i in range(tiers):
        y = h * (i + 1) / (tiers + 1)
        parts.append(part(box(-w / 2, y, w / 2, y + 0.045), TEAK_SOFT))
        c = load[i % len(load)]
        bw = w * (0.34 + 0.10 * (i % 3))
        cx = (-1) ** i * w * 0.16
        parts.append(part(taper(y + 0.045, bw, y + 0.045 + h * 0.13, bw * 0.86, cx=cx), c))
        parts.append(part(box(cx + bw * 0.2, y + 0.06, cx + bw * 0.3, y + 0.11), PAPER))   # ярлык
    return parts


def mail_sacks() -> list:
    return [
        part(ellipse(-0.30, 0.28, 0.30, 0.28, 22), SACK),
        part(ellipse(-0.24, 0.52, 0.14, 0.12, 18), SACK),           # горло мешка
        part(ellipse(0.34, 0.24, 0.26, 0.24, 22), SACK_2),
        part(box(-0.34, 0.30, -0.24, 0.38), PAPER),                 # пломба-ярлык
        part(box(0.28, 0.26, 0.38, 0.33), PAPER),
    ]


def crates() -> list:
    return [
        part(box(-0.45, 0.0, 0.45, 0.52), CRATE),
        part(box(-0.45, 0.24, 0.45, 0.29), TEAK_SOFT),
        part(box(-0.22, 0.52, 0.40, 0.92), CRATE),
        part(box(-0.22, 0.70, 0.40, 0.75), TEAK_SOFT),
        part(box(-0.10, 0.60, 0.16, 0.68), PAPER),                  # трафарет
    ]


def trunk_stack() -> list:
    return [
        part(box(-0.48, 0.0, 0.48, 0.34), [0.30, 0.26, 0.24]),
        part(ellipse(0.0, 0.34, 0.48, 0.10, 18, 0.0, math.pi), [0.34, 0.30, 0.28]),
        part(box(-0.46, 0.14, 0.46, 0.19), BRASS),
        part(box(-0.34, 0.44, 0.34, 0.70), [0.24, 0.21, 0.20]),
        part(box(-0.32, 0.55, 0.32, 0.59), BRASS),
    ]


def coffin() -> list:
    return [
        part([[-0.86, 0.0], [0.86, 0.0], [0.72, 0.36], [-0.72, 0.36]], TEAK),
        part(box(-0.76, 0.36, 0.76, 0.42), TEAK_SOFT),
        part(box(-0.24, 0.42, 0.24, 0.47), [0.62, 0.16, 0.14]),     # сургучная пломба
    ]


def broom() -> list:
    return [
        part(limb(0.0, 0.18, 0.10, 1.42, 0.026), TEAK_SOFT),
        part(taper(0.0, 0.22, 0.20, 0.14), [0.62, 0.52, 0.30]),
    ]


def bucket() -> list:
    return [
        part(taper(0.0, 0.24, 0.28, 0.30), IRON),
        part(ellipse(0.0, 0.28, 0.15, 0.04, 16), [0.28, 0.28, 0.30]),
        part(ellipse(0.0, 0.40, 0.14, 0.12, 16, 0.0, math.pi), IRON),
    ]


def hooks_wall() -> list:
    """Крюки со снаряжением: чагул, куртка, свёрнутая верёвка, фонарь на крюке."""
    return [
        part(box(-0.70, 1.72, 0.70, 1.78), TEAK_SOFT),              # рейка
        part(limb(-0.52, 1.72, -0.52, 1.62, 0.02), BRASS),
        part(ellipse(-0.52, 1.46, 0.11, 0.16, 20), [0.44, 0.32, 0.20]),   # чагул
        part(limb(-0.16, 1.72, -0.16, 1.64, 0.02), BRASS),
        part(taper(1.20, 0.30, 1.64, 0.24, cx=-0.16), KHAKI),        # куртка
        part(limb(0.24, 1.72, 0.24, 1.62, 0.02), BRASS),
        part(ellipse(0.24, 1.44, 0.14, 0.13, 20), [0.50, 0.42, 0.28]),
        part(ellipse(0.24, 1.44, 0.07, 0.065, 16), WALL_MID),        # виток верёвки
        part(limb(0.60, 1.72, 0.60, 1.60, 0.02), BRASS),
        part(box(0.52, 1.36, 0.68, 1.58), IRON),                     # фонарь кондуктора
        part(box(0.545, 1.40, 0.655, 1.52), LAMP_GLASS),
    ]


def notice_board() -> list:
    return [
        part(box(-0.34, 0.0, 0.34, 0.46), TEAK_SOFT),
        part(box(-0.28, 0.06, -0.02, 0.40), PAPER),
        part(box(0.02, 0.12, 0.28, 0.34), [0.86, 0.82, 0.70]),
        part(box(0.04, 0.36, 0.24, 0.42), [0.78, 0.74, 0.62]),
    ]


def window_night() -> list:
    """Окно: за ним не чернота, а ночной город и небо."""
    return [
        part(box(-0.62, 0.0, 0.62, 0.92), NIGHT_CITY),
        part(box(-0.62, 0.0, 0.62, 0.14), [0.26, 0.22, 0.20]),      # земля за окном
        part(box(-0.40, 0.10, -0.28, 0.34), NIGHT_GLOW),            # огни
        part(box(-0.10, 0.10, 0.02, 0.28), NIGHT_GLOW),
        part(box(0.26, 0.10, 0.36, 0.40), NIGHT_GLOW),
        part(box(-0.66, -0.04, 0.66, 0.0), TEAK),                   # рама
        part(box(-0.66, 0.92, 0.66, 0.96), TEAK),
        part(box(-0.03, 0.0, 0.03, 0.92), TEAK),                    # переплёт
    ]


PROPS = [
    # id, контуры, положение, поворот
    ("stove",        stove(),            [-1.88, 0.0, 0.6],    None),
    ("brake_wheel",  brake_wheel(),      [1.88, 0.0, 0.2],     None),
    ("desk",         desk(),             [1.80, 0.0, -1.5],    None),
    ("clock_face",   regulator_clock(),  [2.02, 1.92, -2.2],   None),
    ("lamp_1",       hanging_lamp(0.85), [0.0, 3.55, 0.6],     None),
    ("lamp_2",       hanging_lamp(0.70), [0.0, 3.55, -3.6],    None),
    ("hooks",        hooks_wall(),       [-2.86, 0.0, 1.6],    [0.0, 90.0, 0.0]),
    ("notice",       notice_board(),     [2.30, 1.40, -0.4],   [0.0, -80.0, 0.0]),
    ("window",       window_night(),     [2.86, 1.30, -2.6],   [0.0, -90.0, 0.0]),
    ("mail_sacks",   mail_sacks(),       [-1.30, 0.0, 2.5],    None),
    ("crates",       crates(),           [1.45, 0.0, 2.9],     None),
    ("trunks",       trunk_stack(),      [-2.05, 0.0, -0.6],   None),
    ("coffin",       coffin(),           [-1.70, 0.0, -4.6],   [0.0, 74.0, 0.0]),
    ("broom",        broom(),            [2.20, 0.0, 1.6],     None),
    ("bucket",       bucket(),           [-2.10, 0.0, 1.9],    None),
    ("shelf_l_1",    shelf(3, 1.4, 2.1, [SACK, CRATE, SACK_2]),        [-2.34, 0.0, -3.2],  [0.0, 80.0, 0.0]),
    ("shelf_r_1",    shelf(3, 1.4, 2.1, [CRATE, SACK_2, CLOTH_RED]),   [2.34, 0.0, -3.8],   [0.0, -80.0, 0.0]),
    ("shelf_l_2",    shelf(4, 1.5, 2.2, [SACK_2, CLOTH_BLUE, CRATE, SACK]),  [-2.34, 0.0, -5.8], [0.0, 80.0, 0.0]),
    ("shelf_r_2",    shelf(4, 1.5, 2.2, [SACK, CRATE, SACK_2, CLOTH_RED]),   [2.34, 0.0, -6.6],  [0.0, -80.0, 0.0]),
    ("shelf_l_3",    shelf(4, 1.6, 2.3, [SACK_2, CRATE, SACK, CRATE]),       [-2.34, 0.0, -8.6], [0.0, 80.0, 0.0]),
    ("shelf_r_3",    shelf(4, 1.6, 2.3, [CRATE, SACK, CRATE, SACK_2]),       [2.34, 0.0, -9.6],  [0.0, -80.0, 0.0]),
    ("shelf_l_4",    shelf(5, 1.7, 2.4, [SACK_2, CRATE, SACK_2, CRATE, SACK]), [-2.34, 0.0, -11.8], [0.0, 80.0, 0.0]),
    ("shelf_r_4",    shelf(5, 1.7, 2.4, [CRATE, SACK_2, CRATE, SACK_2, CRATE]), [2.34, 0.0, -12.8], [0.0, -80.0, 0.0]),
]


# --- постановка --------------------------------------------------------------

def stage() -> dict:
    """Разрез вагона: внутри светло и подробно, тёмное — только конструкция."""
    layers = [
        {"id": "floor", "size": [11.0, 44.0], "pos": [0.0, 0.0, -14.0], "rot": [-90.0, 0.0, 0.0], "color": FLOOR},
        {"id": "wall_left", "size": [44.0, 5.6], "pos": [-2.9, 2.8, -14.0], "rot": [0.0, 90.0, 0.0], "color": WALL_LIT},
        {"id": "wall_right", "size": [44.0, 5.6], "pos": [2.9, 2.8, -14.0], "rot": [0.0, -90.0, 0.0], "color": WALL_MID},
        {"id": "ceiling", "size": [11.0, 44.0], "pos": [0.0, 3.6, -14.0], "rot": [90.0, 0.0, 0.0], "color": CEILING},
        {"id": "wall_shadow_l", "size": [44.0, 0.9], "pos": [-2.88, 0.45, -14.0], "rot": [0.0, 90.0, 0.0], "color": WALL_MID},
        {"id": "wall_shadow_r", "size": [44.0, 0.9], "pos": [2.88, 0.45, -14.0], "rot": [0.0, -90.0, 0.0], "color": WALL_DEEP},
        {"id": "depth_haze", "size": [11.0, 4.6], "pos": [0.0, 2.3, -16.0], "color": [0.38, 0.31, 0.24]},
        {"id": "front_door", "size": [1.15, 2.15], "pos": [0.0, 1.08, -15.6], "color": TEAK_SOFT},
        {"id": "front_door_glass", "size": [0.66, 0.62], "pos": [0.0, 1.66, -15.55], "color": [0.86, 0.80, 0.62]},
        {"id": "front_door_seam", "size": [1.25, 0.06], "pos": [0.0, 0.03, -15.5], "color": [0.92, 0.86, 0.68]},
        {"id": "gallery", "size": [8.6, 0.14], "pos": [0.0, 2.04, -7.5], "rot": [-90.0, 0.0, 0.0], "color": TEAK_SOFT},
    ]
    # Балки потолка и половицы: ритм конструкции, тёмное по светлому.
    for i, z in enumerate([1.4, -0.6, -2.6, -4.6, -6.6, -8.6, -10.6]):
        layers.append({"id": "beam_%d" % (i + 1), "size": [11.0, 0.13], "pos": [0.0, 3.56, z],
                       "rot": [90.0, 0.0, 0.0], "color": TEAK})
    for i, x in enumerate([-1.7, -0.55, 0.55, 1.7]):
        layers.append({"id": "plank_%d" % (i + 1), "size": [0.05, 44.0], "pos": [x, 0.01, -14.0],
                       "rot": [-90.0, 0.0, 0.0], "color": FLOOR_LINE})
    return {
        "_comment": ("Освещённый разрез вагона (ориентир — интерьер дома в Kentucky Route Zero): "
                     "внутри тепло и всё читается, тёмное — только конструкция и передний план. "
                     "Контуры рисует tools/draw_car_01.py; править форму — там, не в коде."),
        "camera": {"pos": [0.0, 1.78, 4.0], "rot": [-8.0, 0.0, 0.0], "size": 4.2},
        "layers": layers,
        "props": [{"id": pid, "pos": pos, "parts": parts, **({"rot": rot} if rot else {})}
                  for pid, parts, pos, rot in PROPS],
        "pools": [
            {"id": "stove_pool", "size": [5.0, 5.0], "pos": [-1.4, 0.03, 0.6], "rot": [-90.0, 0.0, 0.0],
             "color": [1.0, 0.45, 0.16], "strength": 0.34},
            {"id": "lamp_pool", "size": [7.0, 7.0], "pos": [0.0, 0.04, 0.4], "rot": [-90.0, 0.0, 0.0],
             "color": [1.0, 0.86, 0.60], "strength": 0.30},
            {"id": "lamp_pool_ceiling", "size": [4.0, 4.0], "pos": [0.0, 3.54, 0.4], "rot": [90.0, 0.0, 0.0],
             "color": [1.0, 0.88, 0.64], "strength": 0.22},
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
        doc["figure"] = {"id": npc_id + "_figure", "parts": parts}
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
