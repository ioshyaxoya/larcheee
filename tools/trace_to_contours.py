#!/usr/bin/env python3
"""trace_to_contours.py — растр → наши контуры.

Зачем это есть. Сгенерированный PNG нельзя положить в вагон как есть: у нас
цвет каждого контура живёт в данных, и на этом держатся две механики —
затухание с глубиной (`dim()` в draw_car_01) и закон цвета A10, по которому
цвет есть накопленное время (`colour_return` в испытании). Запечённая текстура
свой цвет несёт с собой и закону цвета больше не подчиняется; лужи света,
которые складываются аддитивно с плоским полем, по текстуре читаются мутью.

Поэтому генератор изображений у нас даёт **референс**, а не ассет. Этот скрипт
превращает референс в контуры, которые движок уже умеет рисовать: форму больше
не выдумывает кодер, но конвейер остаётся один.

Что делает:
  1. читает PNG, при необходимости снимает фон (по альфе или по цвету угла);
  2. сводит цвета к палитре проекта (или к N цветам медианным срезом);
  3. для каждого цвета ищет связные области, обходит границу, упрощает
     ломаную (Рамер—Дуглас—Пойкер);
  4. отбрасывает самопересекающиеся и мелкие контуры;
  5. переводит в метры по заданной высоте фигуры и пишет JSON,
     который StageBuilder читает без изменений.

Наружные контуры берутся без дырок: области рисуются от больших к малым, и
внутренний цвет ложится поверх внешнего — так же, как в рисовальных скриптах.

Запуск:
  python3 tools/trace_to_contours.py ref.png -o data/traced/shani.json \\
      --height 5.2 --colors 14 --min-area 0.0004 --simplify 1.4
  python3 tools/trace_to_contours.py ref.png -o out.json --palette shani
  python3 tools/trace_to_contours.py ref.png -o out.json --preview out_preview.png
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover - зависимость ставится отдельно
    sys.exit("trace_to_contours: нужны pillow и numpy — "
             "pip install -r tools/requirements.txt")

from draw_lib import is_simple


# --- палитры проекта ---------------------------------------------------------
# Трассировка в произвольные цвета ломает стиль так же, как генерация без
# стилевого префикса. Поэтому цвета сводятся к палитре того, что рисуем.

def project_palette(name: str) -> list:
    """Палитра из рисовального скрипта: сводим референс к нашим же цветам."""
    if name == "none":
        return []
    mod_name = {"shani": "draw_shani", "car_01": "draw_car_01"}.get(name)
    if mod_name is None:
        raise SystemExit("trace_to_contours: неизвестная палитра «%s» "
                         "(есть: shani, car_01, none)" % name)
    mod = __import__(mod_name)
    out = []
    for key in dir(mod):
        if key.isupper():
            val = getattr(mod, key)
            if isinstance(val, list) and len(val) == 3 and all(
                    isinstance(v, float) for v in val):
                out.append(tuple(val))
    return sorted(set(out))


# --- сведение цветов ---------------------------------------------------------

def median_cut(pixels: np.ndarray, count: int) -> list:
    """Медианный срез: N характерных цветов картинки без внешних зависимостей."""
    boxes = [pixels]
    while len(boxes) < count:
        boxes.sort(key=lambda b: -(len(b) * float(np.ptp(b, axis=0).max()) if len(b) else 0.0))
        box = boxes.pop(0)
        if len(box) < 2:
            boxes.append(box)
            break
        axis = int(np.argmax(np.ptp(box, axis=0)))
        order = np.argsort(box[:, axis], kind="stable")
        box = box[order]
        mid = len(box) // 2
        boxes.append(box[:mid])
        boxes.append(box[mid:])
    return [tuple(np.mean(b, axis=0) / 255.0) for b in boxes if len(b)]


def snap(colours: list, palette: list) -> list:
    """Каждый найденный цвет — к ближайшему цвету палитры."""
    if not palette:
        return colours
    pal = np.array(palette, dtype=np.float64)
    out = []
    for c in colours:
        d = np.sum((pal - np.array(c)) ** 2, axis=1)
        out.append(tuple(pal[int(np.argmin(d))]))
    return out


def quantise(rgb: np.ndarray, mask: np.ndarray, colours: list) -> np.ndarray:
    """Индексная карта: каждому пикселю — номер ближайшего цвета."""
    pal = np.array(colours, dtype=np.float32) * 255.0
    flat = rgb.reshape(-1, 3).astype(np.float32)
    idx = np.zeros(len(flat), dtype=np.int32)
    step = 200000
    for i in range(0, len(flat), step):
        chunk = flat[i:i + step]
        d = ((chunk[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        idx[i:i + step] = np.argmin(d, axis=1)
    idx = idx.reshape(rgb.shape[:2])
    idx[~mask] = -1
    return idx


def denoise(idx: np.ndarray, count: int, passes: int) -> np.ndarray:
    """Фильтр большинства по индексной карте.

    Сглаженные края растра дают промежуточные цвета, а те — тонкие осколки на
    каждой границе. Без этого шага поля рассыпаются на щепки, и трассировка
    выдаёт сотню контуров там, где нужен один.
    """
    for _ in range(max(0, passes)):
        votes = np.zeros((count,) + idx.shape, dtype=np.int16)
        for ci in range(count):
            m = (idx == ci).astype(np.int16)
            acc = np.zeros_like(m)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    acc += np.roll(np.roll(m, dy, axis=0), dx, axis=1)
            votes[ci] = acc
        best = np.argmax(votes, axis=0).astype(np.int32)
        keep = idx < 0
        idx = np.where(keep, -1, best)
    return idx


# --- области и границы -------------------------------------------------------

def components(mask: np.ndarray, min_px: int) -> list:
    """Связные области маски (4-связность), мелкие отброшены."""
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]
        seen[y0, x0] = True
        cells = []
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(cells) >= min_px:
            comp = np.zeros((h, w), dtype=bool)
            for y, x in cells:
                comp[y, x] = True
            out.append((len(cells), comp))
    out.sort(key=lambda p: -p[0])
    return out


# Соседи по часовой стрелке, начиная с левого верхнего.
_NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]


def trace_boundary(comp: np.ndarray) -> list:
    """Обход границы области по Муру с явным backtrack.

    Считать направление «откуда пришли» через арифметику по модулю — верный
    способ получить вырожденный контур из трёх точек: обход разворачивается на
    первом же шаге. Поэтому backtrack хранится как пиксель, а не как индекс.
    """
    h, w = comp.shape
    ys, xs = np.nonzero(comp)
    y0 = int(ys.min())
    x0 = int(xs[ys == y0].min())
    start = (y0, x0)

    def solid(p):
        return 0 <= p[0] < h and 0 <= p[1] < w and comp[p[0], p[1]]

    back = (y0, x0 - 1)      # входим слева: там пусто по построению start
    cur = start
    contour = [start]
    for _ in range(int(comp.sum()) * 8 + 32):
        delta = (back[0] - cur[0], back[1] - cur[1])
        try:
            i0 = _NEIGHBOURS.index(delta)
        except ValueError:
            i0 = 7
        nxt = None
        for k in range(1, 9):
            j0 = (i0 + k) % 8
            cand = (cur[0] + _NEIGHBOURS[j0][0], cur[1] + _NEIGHBOURS[j0][1])
            if solid(cand):
                prev = (cur[0] + _NEIGHBOURS[(j0 - 1) % 8][0],
                        cur[1] + _NEIGHBOURS[(j0 - 1) % 8][1])
                nxt = (cand, prev)
                break
        if nxt is None:
            break
        cand, prev = nxt
        if cand == start and len(contour) > 2:
            break
        contour.append(cand)
        back = prev
        cur = cand
    return contour


def rdp(points: list, eps: float) -> list:
    """Упрощение ломаной: убираем точки, которые ничего не решают."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i0, i1 = stack.pop()
        ax, ay = points[i0]
        bx, by = points[i1]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy) or 1.0
        best, best_d = -1, 0.0
        for i in range(i0 + 1, i1):
            px, py = points[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / norm
            if d > best_d:
                best, best_d = i, d
        if best > 0 and best_d > eps:
            keep[best] = True
            stack.append((i0, best))
            stack.append((best, i1))
    return [p for p, k in zip(points, keep) if k]


# --- сборка ------------------------------------------------------------------

def trace(path: str, height: float, colour_count: int, palette: list,
          min_area: float, simplify: float, work: int, bg_tol: float,
          anchor: str, denoise_passes: int = 2) -> list:
    img = Image.open(path).convert("RGBA")
    if max(img.size) > work:
        k = work / float(max(img.size))
        img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))),
                         Image.LANCZOS)
    arr = np.asarray(img)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    mask = alpha > 24
    if mask.all():
        # Нет альфы — снимаем фон по цвету углов. Генераторы просят сплошной
        # фон именно для этого (никогда не просить у них «прозрачный»).
        h, w = mask.shape
        corners = np.array([rgb[0, 0], rgb[0, w - 1], rgb[h - 1, 0], rgb[h - 1, w - 1]],
                           dtype=np.float32)
        bg = corners.mean(axis=0)
        dist = np.sqrt(((rgb.astype(np.float32) - bg) ** 2).sum(axis=2))
        mask = dist > bg_tol * 255.0

    if not mask.any():
        raise SystemExit("trace_to_contours: после снятия фона не осталось пикселей — "
                         "поднимите --bg-tol или дайте PNG с альфой")

    px = rgb[mask]
    colours = median_cut(px.astype(np.float64), colour_count)
    colours = snap(colours, palette)
    idx = quantise(rgb, mask, colours)
    idx = denoise(idx, len(colours), denoise_passes)

    total = int(mask.sum())
    min_px = max(8, int(min_area * total))

    ys, xs = np.nonzero(mask)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    span_y = max(1, y1 - y0 + 1)
    scale = height / float(span_y)
    cx = (x0 + x1) / 2.0

    found = []
    for ci, colour in enumerate(colours):
        cmask = idx == ci
        if not cmask.any():
            continue
        for area, comp in components(cmask, min_px):
            raw = trace_boundary(comp)
            pts = [(float(x), float(y)) for y, x in raw]
            pts = rdp(pts, simplify)
            if len(pts) > 3 and pts[0] == pts[-1]:
                pts = pts[:-1]
            if len(pts) < 3:
                continue
            metres = []
            for x, y in pts:
                mx = (x - cx) * scale
                my = (y1 - y) * scale if anchor == "feet" else ((y1 + y0) / 2.0 - y) * scale
                metres.append((mx, my))
            if not is_simple(metres):
                metres = [(mx, my) for mx, my in rdp(metres, simplify * scale * 1.8)]
                if len(metres) < 3 or not is_simple(metres):
                    continue
            found.append((area, [[round(mx, 4), round(my, 4)] for mx, my in metres],
                          [round(float(c), 4) for c in colour]))
    # От больших к малым: внутренний цвет ложится поверх внешнего, как в
    # рисовальных скриптах. Дырки в контурах поэтому не нужны.
    found.sort(key=lambda t: -t[0])
    return [{"points": pts, "color": col} for _, pts, col in found]


def preview(parts: list, path: str, size: int = 720) -> None:
    """Как это выглядит уже контурами — чтобы сверять с референсом глазами."""
    from PIL import ImageDraw
    xs = [p[0] for pt in parts for p in pt["points"]]
    ys = [p[1] for pt in parts for p in pt["points"]]
    if not xs:
        return
    w_m, h_m = max(xs) - min(xs), max(ys) - min(ys)
    k = (size * 0.92) / max(w_m, h_m, 1e-6)
    img = Image.new("RGB", (int(w_m * k) + 40, int(h_m * k) + 40), (246, 244, 238))
    d = ImageDraw.Draw(img)
    for pt in parts:
        poly = [((p[0] - min(xs)) * k + 20, (max(ys) - p[1]) * k + 20) for p in pt["points"]]
        col = tuple(int(max(0.0, min(1.0, c)) * 255) for c in pt["color"])
        if len(poly) >= 3:
            d.polygon(poly, fill=col)
    img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Растр → контуры для StageBuilder")
    ap.add_argument("image")
    ap.add_argument("-o", "--output", required=True, help="куда писать JSON")
    ap.add_argument("--id", default=None, help="id фигуры в данных")
    ap.add_argument("--height", type=float, default=1.74, help="высота фигуры в метрах")
    ap.add_argument("--colors", type=int, default=12, help="сколько цветов оставить")
    ap.add_argument("--palette", default="none", help="палитра проекта: shani, car_01, none")
    ap.add_argument("--min-area", type=float, default=0.0006,
                    help="доля площади, меньше которой контур отбрасывается")
    ap.add_argument("--simplify", type=float, default=1.4, help="допуск упрощения, пиксели")
    ap.add_argument("--work", type=int, default=420, help="рабочий размер по большей стороне")
    ap.add_argument("--bg-tol", type=float, default=0.16,
                    help="порог отличия от цвета фона (доля), если нет альфы")
    ap.add_argument("--anchor", choices=["feet", "centre"], default="feet")
    ap.add_argument("--denoise", type=int, default=2,
                    help="проходов фильтра большинства: без них поля рассыпаются на осколки")
    ap.add_argument("--preview", default=None, help="PNG для сверки глазами")
    args = ap.parse_args()

    palette = project_palette(args.palette)
    parts = trace(args.image, args.height, args.colors, palette, args.min_area,
                  args.simplify, args.work, args.bg_tol, args.anchor, args.denoise)
    if not parts:
        raise SystemExit("trace_to_contours: контуров не нашлось — "
                         "попробуйте больше --colors или меньше --min-area")
    doc = {
        "_comment": ("Контуры получены трассировкой референса "
                     "(tools/trace_to_contours.py), а не выдуманы кодером. "
                     "Референс: %s. Править форму — перетрассировкой, "
                     "не руками в JSON." % os.path.basename(args.image)),
        "source": os.path.basename(args.image),
        "id": args.id or os.path.splitext(os.path.basename(args.output))[0],
        "parts": parts,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    if args.preview:
        preview(parts, args.preview)
    pts = sum(len(p["points"]) for p in parts)
    cols = len({tuple(p["color"]) for p in parts})
    print("trace_to_contours: %d контуров, %d точек, %d цветов → %s"
          % (len(parts), pts, cols, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
