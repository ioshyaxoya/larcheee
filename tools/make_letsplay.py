#!/usr/bin/env python3
"""make_letsplay.py — кадры прохода → видео, которое можно смотреть.

Игра диалоговая: кадр статичен, а читать в нём надо текст. Поэтому это не
съёмка в реальном времени, а слайд-шоу с длительностью по объёму текста в
кадре — чем больше написано, тем дольше кадр держится. Иначе зритель либо не
успевает прочесть, либо ждёт на пустых кадрах.

Кадры снимает `tests/drive_ui.gd ++ --scenario=letsplay`, порядок — по номеру
в имени файла. Разбор к кадрам берётся из `log.txt`, который пишет драйвер.

Запуск:
  python3 tools/make_letsplay.py <папка с кадрами> -o build/letsplay.mp4
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("make_letsplay: нужны pillow и numpy — pip install -r tools/requirements.txt")

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"


def text_load(path: str) -> float:
    """Сколько в кадре «текста»: доля пикселей нижней панели, отличных от фона.

    Грубая, но честная мера: панель диалога занимает низ кадра, и чем плотнее
    она заполнена, тем дольше кадр надо держать.
    """
    img = Image.open(path).convert("L")
    a = np.asarray(img)
    strip = a[int(a.shape[0] * 0.78):, :]
    if strip.size == 0:
        return 0.0
    base = float(np.median(strip))
    return float((np.abs(strip.astype(np.int16) - base) > 30).mean())


def main() -> int:
    ap = argparse.ArgumentParser(description="Кадры прохода → mp4")
    ap.add_argument("shots", help="папка с PNG-кадрами прохода")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--min", type=float, default=1.6, help="минимум секунд на кадр")
    ap.add_argument("--max", type=float, default=6.5, help="максимум секунд на кадр")
    ap.add_argument("--fps", type=int, default=12)
    args = ap.parse_args()

    film = sorted(f for f in os.listdir(args.shots) if re.match(r"^film_\d+\.jpg$", f))
    if film:
        # Непрерывная запись: длительность кадра постоянна, движение уже в них.
        plan = [(os.path.join(args.shots, f), round(1.0 / args.fps, 4)) for f in film]
    else:
        files = sorted(f for f in os.listdir(args.shots)
                       if f.endswith(".png") and re.match(r"^\d+_", f))
        if not files:
            sys.exit("make_letsplay: в %s нет кадров прохода" % args.shots)
        plan = []
        for f in files:
            path = os.path.join(args.shots, f)
            load = text_load(path)
            secs = args.min + (args.max - args.min) * min(1.0, load / 0.09)
            plan.append((path, round(secs, 2)))

    total = sum(s for _, s in plan)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for path, secs in plan:
            fh.write("file '%s'\nduration %.2f\n" % (os.path.abspath(path), secs))
        fh.write("file '%s'\n" % os.path.abspath(plan[-1][0]))   # ffmpeg ждёт повтор последнего
        listing = fh.name

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listing,
           "-fps_mode", "cfr", "-r", str(args.fps),
           "-vf", "scale=1280:720:flags=lanczos,format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-movflags", "+faststart", args.output]
    res = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(listing)
    if res.returncode != 0:
        sys.exit("make_letsplay: ffmpeg упал\n" + res.stderr[-1500:])
    size = os.path.getsize(args.output) / 1e6
    print("make_letsplay: %d кадров, %.0f с, %.1f МБ → %s"
          % (len(plan), total, size, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
