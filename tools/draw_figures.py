#!/usr/bin/env python3
"""draw_figures.py — рисует силуэты и реквизит контурами и пишет их в данные.

Фигуры BOMBAY MAIL — плоские сплошные силуэты («вырезанные из бумаги»,
docs/visual_direction.md §3, ориентир Kentucky Route Zero). Человек читается
очертанием и одеждой: тюрбан, топи, сари, шинель, чалма. Лиц нет.

Контур — замкнутый простой полигон в метрах, начало координат у земли по центру
фигуры. Фигура собирается из нескольких частей (голова, корпус, подол, руки):
части одного цвета сливаются в один силуэт, как склеенная бумага.

Запуск: python tools/draw_figures.py   (перезаписывает контуры в data/)
"""
from __future__ import annotations

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R2 = lambda v: round(v, 4)


def circle(cx: float, cy: float, r: float, n: int = 22) -> list:
    return [[R2(cx + r * math.cos(2 * math.pi * i / n)), R2(cy + r * math.sin(2 * math.pi * i / n))] for i in range(n)]


def ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 26, a0: float = 0.0, a1: float = math.tau) -> list:
    return [[R2(cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1))), R2(cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1)))]
            for i in range(n)]


def taper(y0: float, w0: float, y1: float, w1: float, cx: float = 0.0) -> list:
    """Трапеция: ширина w0 на высоте y0, w1 на высоте y1. Плечи, корпус, подол."""
    return [[R2(cx - w0 / 2), R2(y0)], [R2(cx + w0 / 2), R2(y0)], [R2(cx + w1 / 2), R2(y1)], [R2(cx - w1 / 2), R2(y1)]]


def limb(x0: float, y0: float, x1: float, y1: float, w: float) -> list:
    """Рука или нога: полоса ширины w от точки к точке."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length * w / 2, dx / length * w / 2
    return [[R2(x0 + nx), R2(y0 + ny)], [R2(x1 + nx), R2(y1 + ny)], [R2(x1 - nx), R2(y1 - ny)], [R2(x0 - nx), R2(y0 - ny)]]


def part(points: list, color: list | None = None) -> dict:
    d = {"points": points}
    if color:
        d["color"] = color
    return d


# --- фигуры ------------------------------------------------------------------
# Пропорции взрослого ≈ 1.65–1.75 м; ребёнок 1.25 м. Одежда — единственный
# способ узнать человека, поэтому она в очертании, а не в детали.

def standing_coat(h: float = 1.72) -> list:
    """Прямая фигура в длинном тёмном платье-шинели: Шани."""
    return [
        part(taper(0.10 * h, 0.30 * h, 0.60 * h, 0.26 * h)),     # подол до земли
        part(taper(0.58 * h, 0.27 * h, 0.80 * h, 0.30 * h)),     # корпус
        part(taper(0.79 * h, 0.30 * h, 0.86 * h, 0.13 * h)),     # плечи к шее
        part(circle(0.0, 0.92 * h, 0.072 * h)),                  # голова
        part(ellipse(0.0, 0.965 * h, 0.085 * h, 0.045 * h)),     # чалма-повязка
        part(limb(0.13 * h, 0.79 * h, 0.17 * h, 0.40 * h, 0.055 * h)),   # рука
        part(limb(-0.13 * h, 0.79 * h, -0.16 * h, 0.42 * h, 0.055 * h)),
        part(limb(0.18 * h, 0.44 * h, 0.20 * h, 0.02 * h, 0.022 * h)),   # трость
    ]


def seated_old(h: float = 1.62) -> list:
    """Сидит у печки, круглая спина: Ратан."""
    return [
        part(taper(0.02 * h, 0.46 * h, 0.20 * h, 0.40 * h)),     # ноги, подобранные
        part(taper(0.19 * h, 0.40 * h, 0.46 * h, 0.36 * h)),     # бёдра и спина
        part(ellipse(0.0, 0.50 * h, 0.19 * h, 0.15 * h)),        # согнутая спина
        part(taper(0.55 * h, 0.24 * h, 0.62 * h, 0.12 * h)),     # шея
        part(circle(0.02 * h, 0.68 * h, 0.065 * h)),             # голова
        part(limb(0.16 * h, 0.48 * h, 0.26 * h, 0.26 * h, 0.05 * h)),   # рука к печке
    ]


def sleeping_turban(l: float = 1.68) -> list:
    """Лежит на койке: горизонталь, тюрбан у изголовья. Бир Сингх."""
    return [
        part(taper(0.06, 0.90 * l, 0.20, 0.86 * l)),             # тело под одеялом
        part(ellipse(0.34 * l, 0.30, 0.10 * l, 0.09)),           # голова
        part(ellipse(0.40 * l, 0.34, 0.075 * l, 0.075)),         # тюрбан
        part(limb(-0.30 * l, 0.20, -0.42 * l, 0.10, 0.09)),      # свесившаяся стопа
    ]


def seated_topi(h: float = 1.55) -> list:
    """Спит сидя, топи и чётки: Хафиз-сахиб."""
    return [
        part(taper(0.02 * h, 0.50 * h, 0.22 * h, 0.42 * h)),
        part(taper(0.21 * h, 0.42 * h, 0.52 * h, 0.34 * h)),
        part(taper(0.51 * h, 0.30 * h, 0.60 * h, 0.13 * h)),
        part(circle(0.0, 0.67 * h, 0.066 * h)),
        part(taper(0.70 * h, 0.13 * h, 0.745 * h, 0.115 * h)),   # топи — плоская шапочка
        part(limb(-0.14 * h, 0.50 * h, -0.10 * h, 0.28 * h, 0.045 * h)),
    ]


def sari(h: float = 1.63) -> list:
    """Сари: узкий силуэт, широкий подол, драпировка через плечо. Сарасвати."""
    return [
        part(taper(0.0, 0.40 * h, 0.52 * h, 0.24 * h)),          # подол
        part(taper(0.50 * h, 0.24 * h, 0.78 * h, 0.24 * h)),     # корпус
        part(taper(0.77 * h, 0.25 * h, 0.85 * h, 0.12 * h)),     # плечи
        part(circle(0.0, 0.915 * h, 0.068 * h)),                 # голова
        part(ellipse(0.0, 0.95 * h, 0.10 * h, 0.055 * h)),       # покрытая голова
        part([[R2(0.10 * h), R2(0.84 * h)], [R2(0.22 * h), R2(0.55 * h)],
              [R2(0.13 * h), R2(0.20 * h)], [R2(0.02 * h), R2(0.22 * h)],
              [R2(0.06 * h), R2(0.60 * h)]]),                    # паллу через плечо
        part(limb(-0.12 * h, 0.78 * h, -0.17 * h, 0.50 * h, 0.05 * h)),
        part(taper(0.44 * h, 0.11 * h, 0.50 * h, 0.10 * h, cx=-0.20 * h)),  # судки в руке
    ]


def widow_urn(h: float = 1.60) -> list:
    """Вдова в белом с урной: единственная светлая фигура. Монимала."""
    pale = [0.46, 0.45, 0.43]
    dark = [0.22, 0.215, 0.205]
    return [
        part(taper(0.0, 0.42 * h, 0.54 * h, 0.25 * h), pale),
        part(taper(0.52 * h, 0.25 * h, 0.80 * h, 0.25 * h), pale),
        part(taper(0.79 * h, 0.26 * h, 0.86 * h, 0.12 * h), pale),
        part(circle(0.0, 0.925 * h, 0.068 * h), dark),
        part(ellipse(0.0, 0.955 * h, 0.105 * h, 0.06 * h), pale),   # покрывало
        part(ellipse(0.0, 0.50 * h, 0.085 * h, 0.10 * h), dark),    # урна в руках
        part(limb(-0.10 * h, 0.72 * h, -0.05 * h, 0.52 * h, 0.05 * h), pale),
        part(limb(0.10 * h, 0.72 * h, 0.05 * h, 0.52 * h, 0.05 * h), pale),
    ]


def boy(h: float = 1.24) -> list:
    """Мальчик на корточках среди стеллажей: Кану."""
    return [
        part(taper(0.0, 0.40 * h, 0.26 * h, 0.34 * h)),
        part(taper(0.25 * h, 0.32 * h, 0.60 * h, 0.28 * h)),
        part(taper(0.59 * h, 0.28 * h, 0.66 * h, 0.12 * h)),
        part(circle(0.0, 0.735 * h, 0.075 * h)),
        part(limb(0.13 * h, 0.58 * h, 0.20 * h, 0.30 * h, 0.045 * h)),
        part(limb(0.21 * h, 0.62 * h, 0.23 * h, 0.04 * h, 0.018 * h)),   # латхи
    ]


def dog() -> list:
    """Пёс: корпус, лапы, морда, хвост."""
    return [
        part(taper(0.22, 0.62, 0.42, 0.54)),                     # корпус
        part(ellipse(0.34, 0.50, 0.10, 0.085)),                  # голова
        part([[0.42, 0.50], [0.52, 0.47], [0.44, 0.42]]),        # морда
        part([[0.28, 0.58], [0.34, 0.66], [0.36, 0.56]]),        # ухо
        part(limb(0.22, 0.24, 0.22, 0.0, 0.05)),
        part(limb(-0.22, 0.24, -0.24, 0.0, 0.05)),
        part(limb(-0.30, 0.40, -0.44, 0.52, 0.035)),             # хвост
    ]


FIGURES = {
    "god_shani": ("standing_coat", standing_coat()),
    "npc_ratan": ("seated_old", seated_old()),
    "npc_bir_singh": ("sleeping_turban", sleeping_turban()),
    "npc_hafiz": ("seated_topi", seated_topi()),
    "npc_saraswati": ("sari", sari()),
    "npc_monimala": ("widow_urn", widow_urn()),
    "npc_kanu": ("boy", boy()),
    "npc_dog": ("dog", dog()),
}


# --- реквизит ----------------------------------------------------------------

def stove() -> list:
    """Печка: корпус, топка, труба до потолка."""
    body = [0.030, 0.028, 0.034]
    return [
        part(taper(0.0, 0.62, 0.86, 0.54), body),
        part(taper(0.85, 0.58, 0.92, 0.50), body),
        part(circle(0.0, 0.40, 0.15, 18), [1.0, 0.44, 0.13]),    # открытая топка
        part(taper(0.92, 0.14, 2.6, 0.12), body),                # труба
    ]


def brake_wheel() -> list:
    brass = [0.36, 0.30, 0.17]
    dark = [0.014, 0.015, 0.022]
    ring = ellipse(0.0, 0.0, 0.30, 0.30, 26)
    return [
        part([[R2(p[0]), R2(p[1] + 1.02)] for p in ring], brass),
        part(circle(0.0, 1.02, 0.19, 20), dark),                 # ступица-вырез
        part(limb(0.0, 0.02, 0.0, 1.02, 0.11), dark),            # колонка
    ]


def desk_ledger() -> list:
    wood = [0.070, 0.064, 0.058]
    paper = [0.66, 0.64, 0.54]
    return [
        part(taper(0.0, 0.16, 0.68, 0.14, cx=-0.45), wood),
        part(taper(0.0, 0.16, 0.68, 0.14, cx=0.45), wood),
        part(taper(0.68, 1.10, 0.76, 1.10), wood),               # столешница
        part([[-0.18, 0.77], [0.18, 0.77], [0.16, 0.88], [-0.20, 0.88]], paper),  # раскрытый журнал
    ]


def clock() -> list:
    return [
        part(circle(0.0, 0.0, 0.25, 26), [0.014, 0.015, 0.022]),
        part(circle(0.0, 0.0, 0.20, 26), [0.60, 0.55, 0.35]),
        part(limb(0.0, 0.0, 0.0, 0.15, 0.022), [0.10, 0.09, 0.07]),      # часовая на 20:30
        part(limb(0.0, 0.0, 0.13, -0.07, 0.018), [0.10, 0.09, 0.07]),    # минутная
    ]


def shelf(tiers: int, w: float, h: float, color: list) -> list:
    """Стеллаж: стойки и ярусы. Читается ритмом, а не текстурой."""
    parts = [part(limb(-w / 2, 0.0, -w / 2, h, 0.05), color),
             part(limb(w / 2, 0.0, w / 2, h, 0.05), color)]
    for i in range(tiers):
        y = h * (i + 1) / (tiers + 1)
        parts.append(part(taper(y, w, y + 0.045, w, 0.0), color))
    for i in range(tiers):     # тюки и ящики на ярусах
        y = h * (i + 1) / (tiers + 1)
        bw = w * (0.30 + 0.12 * (i % 3))
        parts.append(part(taper(y + 0.045, bw, y + 0.045 + h * 0.11, bw * 0.9,
                                cx=(-1) ** i * w * 0.18), color))
    return parts


def coffin() -> list:
    dark = [0.014, 0.015, 0.022]
    return [part([[-0.85, 0.0], [0.85, 0.0], [0.72, 0.34], [-0.72, 0.34]], dark),
            part(taper(0.34, 1.5, 0.40, 1.3), dark)]


def bales() -> list:
    dark = [0.014, 0.015, 0.022]
    return [part(taper(0.0, 1.30, 0.62, 1.16), dark),
            part(taper(0.60, 0.90, 0.95, 0.80, cx=-0.12), dark),
            part(taper(0.0, 0.60, 0.44, 0.54, cx=0.78), dark)]


def trunk() -> list:
    dark = [0.014, 0.015, 0.022]
    return [part(taper(0.0, 0.98, 0.50, 0.94), dark),
            part(ellipse(0.0, 0.50, 0.49, 0.14, 18, 0.0, math.pi), dark)]


PROPS = {
    "stove": stove(),
    "brake_wheel": brake_wheel(),
    "desk": desk_ledger(),
    "clock_face": clock(),
    "coffin": coffin(),
    "bales": bales(),
    "trunk": trunk(),
    "shelf_l_1": shelf(3, 1.4, 2.1, [0.115, 0.120, 0.158]),
    "shelf_r_1": shelf(3, 1.4, 2.1, [0.104, 0.109, 0.146]),
    "shelf_l_2": shelf(4, 1.5, 2.2, [0.070, 0.074, 0.104]),
    "shelf_r_2": shelf(4, 1.5, 2.2, [0.062, 0.066, 0.094]),
    "shelf_l_3": shelf(4, 1.6, 2.3, [0.038, 0.040, 0.060]),
    "shelf_r_3": shelf(4, 1.6, 2.3, [0.032, 0.034, 0.052]),
    "shelf_l_4": shelf(5, 1.7, 2.4, [0.020, 0.021, 0.032]),
    "shelf_r_4": shelf(5, 1.7, 2.4, [0.017, 0.018, 0.028]),
}
DROP_PROPS = {"stove_mouth", "stove_pipe", "brake_column", "ledger", "clock_rim", "sack"}


def main() -> int:
    written = 0
    for npc_id, (shape, parts) in FIGURES.items():
        path = os.path.join(ROOT, "data", "npcs", npc_id + ".json")
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["silhouette"] = shape
        doc["figure"] = {"id": npc_id + "_figure", "parts": parts}
        doc.pop("silhouette_parts", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
        written += 1

    card_path = os.path.join(ROOT, "data", "cars", "car_01.json")
    with open(card_path, encoding="utf-8") as fh:
        card = json.load(fh)
    props = []
    for prop in card["stage"]["props"]:
        pid = prop["id"]
        if pid in DROP_PROPS:
            continue          # вошло в контур соседнего предмета
        if pid in PROPS:
            prop = {k: v for k, v in prop.items() if k not in ("size", "color")}
            prop["parts"] = PROPS[pid]
        props.append(prop)
    card["stage"]["props"] = props
    with open(card_path, "w", encoding="utf-8") as fh:
        json.dump(card, fh, ensure_ascii=False, indent=2)
    print("draw_figures: фигур %d, реквизита %d" % (written, len(PROPS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
