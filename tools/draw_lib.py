#!/usr/bin/env python3
"""draw_lib.py — рисовальные примитивы для контуров BOMBAY MAIL.

Фигуры и реквизит рисуются **кривыми**, а не набором окружностей и трапеций:
силуэт — один непрерывный контур из кубических Безье, поверх него накладки
(голова, одежда, вещь) и линии-обводки (складка, шнур, кайма, снасть).

Контур — замкнутый простой полигон в метрах; начало координат у земли по центру
фигуры. Проверка `is_simple` ловит самопересечения до того, как контур попадёт
в данные: движок такой полигон не триангулирует.

Используется из tools/draw_car_01.py и других рисовальных скриптов.
"""
from __future__ import annotations

import math

R = lambda v: round(v, 4)
Pt = tuple[float, float]


# --- кривые ------------------------------------------------------------------

def bez(p0: Pt, c0: Pt, c1: Pt, p1: Pt, n: int = 12) -> list:
    """Кубическая Безье: точки без последней, чтобы сегменты стыковались."""
    out = []
    for i in range(n):
        t = i / n
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * c0[0] + 3 * u * t * t * c1[0] + t * t * t * p1[0]
        y = u * u * u * p0[1] + 3 * u * u * t * c0[1] + 3 * u * t * t * c1[1] + t * t * t * p1[1]
        out.append((x, y))
    return out


def curve(nodes: list, n: int = 12, closed: bool = False) -> list:
    """Гладкая кривая через узлы: [(точка, вход, выход), ...].

    Каждый узел — (p, c_in, c_out), где контроли заданы относительно точки.
    Так рисуется линия плеча, падение сари, изгиб спины: одним движением.
    """
    pts: list = []
    count = len(nodes)
    last = count if closed else count - 1
    for i in range(last):
        p0, _, out0 = nodes[i]
        p1, in1, _ = nodes[(i + 1) % count]
        c0 = (p0[0] + out0[0], p0[1] + out0[1])
        c1 = (p1[0] + in1[0], p1[1] + in1[1])
        pts += bez(p0, c0, c1, p1, n)
    if not closed:
        pts.append(nodes[-1][0])
    return pts


def node(p: Pt, c_in: Pt = (0.0, 0.0), c_out: Pt | None = None) -> tuple:
    """Узел кривой. По умолчанию выход зеркалит вход — гладкий стык."""
    if c_out is None:
        c_out = (-c_in[0], -c_in[1])
    return (p, c_in, c_out)


def smooth(p: Pt, dx: float, dy: float) -> tuple:
    """Узел с касательной по направлению (dx, dy): вход и выход зеркальны."""
    return (p, (-dx, -dy), (dx, dy))


# --- контуры -----------------------------------------------------------------

def closed(pts: list) -> list:
    """Список точек → контур для данных, с округлением."""
    return [[R(x), R(y)] for x, y in pts]


def mirror(half: list) -> list:
    """Симметричный контур из левой половины: снизу вверх, потом вниз зеркально.

    Половина задаётся от нижней точки к верхней при x ≤ 0. Так рисуется
    фигура: одна линия бока, и она же с другой стороны.
    """
    right = [(-x, y) for x, y in reversed(half)]
    return half + right


def stroke(pts: list, w0: float, w1: float | None = None) -> list:
    """Линия толщиной: лента вдоль ломаной, ширина от w0 к w1.

    Так рисуются складка, шнур лампы, кайма сари, снасть, стойка перил —
    линия, а не прямоугольник.
    """
    if w1 is None:
        w1 = w0
    n = len(pts)
    if n < 2:
        return []
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        d = math.hypot(dx, dy) or 1.0
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2.0
        nx, ny = -dy / d * w, dx / d * w
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return left + list(reversed(right))


def circle(cx: float, cy: float, r: float, n: int = 24) -> list:
    return [(cx + r * math.cos(math.tau * i / n), cy + r * math.sin(math.tau * i / n)) for i in range(n)]


def ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 28,
            a0: float = 0.0, a1: float = math.tau, tilt: float = 0.0) -> list:
    out = []
    ct, st = math.cos(tilt), math.sin(tilt)
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1 if a1 - a0 < math.tau else n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * ct - y * st, cy + x * st + y * ct))
    return out


def box(x0: float, y0: float, x1: float, y1: float) -> list:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def taper(y0: float, w0: float, y1: float, w1: float, cx: float = 0.0) -> list:
    return [(cx - w0 / 2, y0), (cx + w0 / 2, y0), (cx + w1 / 2, y1), (cx - w1 / 2, y1)]


# --- проверка ----------------------------------------------------------------

def _crosses(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    def side(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 1e-12) - (v < -1e-12)
    d1, d2 = side(c, d, a), side(c, d, b)
    d3, d4 = side(a, b, c), side(a, b, d)
    return d1 * d2 < 0 and d3 * d4 < 0


def is_simple(pts: list) -> bool:
    """Контур без самопересечений? Иначе движок его не триангулирует."""
    n = len(pts)
    if n < 3:
        return False
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 1, n):
            if j == i or (j + 1) % n == i or j == (i + 1) % n:
                continue
            if _crosses(a, b, pts[j], pts[(j + 1) % n]):
                return False
    return True


def part(points: list, color: list, name: str = "") -> dict:
    """Часть фигуры: контур и плоский цвет. Падает на кривом контуре сразу."""
    if not is_simple(points):
        raise ValueError("контур «%s» самопересекается (%d точек)" % (name or "?", len(points)))
    return {"points": closed(points), "color": color}
