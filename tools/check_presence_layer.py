#!/usr/bin/env python3
"""check_presence_layer.py — проверка, что присутствие не дизерится вместе с миром.

Правило (docs/visual_direction.md §4 и §3.1): в испытании точки — только у
мира; присутствие остаётся единственным полностью цветным элементом кадра.
Если эффект применяется одним полноэкранным проходом, а не послойно, точки
лягут и на бога — и правило нарушено.

Проверяется измерением, а не на глаз: кадр со сбоем и кадр без сбоя обязаны
совпасть пиксель в пиксель внутри силуэта присутствия. Силуэт берётся из
альфы кадра присутствия, снятого отдельным подвьюпортом.

Кадры снимает `tests/drive_ui.gd ++ --scenario=glitchcheck`.

Запуск: python3 tools/check_presence_layer.py <папка с кадрами>
"""
from __future__ import annotations

import os
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("check_presence_layer: нужны pillow и numpy — pip install -r tools/requirements.txt")


def main() -> int:
    shots = sys.argv[1] if len(sys.argv) > 1 else "."
    need = ["chk_presence_alpha.png", "chk_no_glitch.png", "chk_glitch.png"]
    for n in need:
        if not os.path.exists(os.path.join(shots, n)):
            sys.exit("check_presence_layer: нет %s — снимите кадры сценарием glitchcheck" % n)

    alpha = np.asarray(Image.open(os.path.join(shots, need[0])).convert("RGBA"))[:, :, 3]
    a = np.asarray(Image.open(os.path.join(shots, need[1])).convert("RGB")).astype(np.int16)
    b = np.asarray(Image.open(os.path.join(shots, need[2])).convert("RGB")).astype(np.int16)
    if a.shape != b.shape or alpha.shape != a.shape[:2]:
        sys.exit("check_presence_layer: размеры кадров не совпадают")

    # Внутренние пиксели силуэта: край сглажен, там разница законна.
    solid = alpha > 250
    eroded = solid.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        eroded &= np.roll(np.roll(solid, dy, axis=0), dx, axis=1)

    total = int(eroded.sum())
    if total < 2000:
        sys.exit("check_presence_layer: силуэт присутствия слишком мал (%d px) — "
                 "кадр снят не в испытании?" % total)

    diff = np.abs(a - b).max(axis=2)
    changed = int((diff[eroded] > 6).sum())
    share = changed / float(total)
    world = ~solid
    world_changed = int((diff[world] > 6).sum()) / float(max(1, int(world.sum())))

    print("присутствие: %d px, изменилось от сбоя %d px (%.3f%%)"
          % (total, changed, share * 100.0))
    print("мир: изменилось %.1f%% — сбой вообще сработал"
          % (world_changed * 100.0))
    if world_changed < 0.02:
        sys.exit("ПРОВАЛ: сбой не изменил и мир — проверка ничего не проверяет")
    if share > 0.005:
        sys.exit("ПРОВАЛ: точки легли на присутствие (%.2f%% силуэта). "
                 "Эффект применяется полноэкранным проходом, а не послойно."
                 % (share * 100.0))
    print("ОК: присутствие идёт отдельным слоем поверх дизеринга и им не задето.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
