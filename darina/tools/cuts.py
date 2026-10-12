#!/usr/bin/env python3
"""
Где в готовой нарезке начинаются куски — с точностью до кадра.

    python3 tools/cuts.py assets/films/kirill.mp4

Печатает строку для films.js:  cutTimes: [1.32, 2.56, …]  (начало кусков 1…28,
кусок 0 начинается с нуля). Нужна движку, чтобы менять кадрирование на вертикальном
экране ровно на стыке, а не «примерно»: после кодирования куски не делят файл на
равные доли — выходит сдвиг до двух кадров, и кадрирование переключалось бы
чуть раньше склейки.

Как ищет: ffmpeg считает, насколько каждый кадр отличается от предыдущего; склейка —
всплеск. Всплеск выбирается только рядом с ожидаемым местом (кусок = CUT_SEC / RATE
секунд), чтобы движение внутри куска не приняли за склейку. Слабые стыки (похожие
соседние планы) помечаются: их стоит глянуть глазами.
"""
import re, subprocess, sys, os, shutil, statistics

CUTS, RATE, CUT_SEC = 29, 1.28, 1.6
STEP = CUT_SEC / RATE          # длина куска в готовом файле, с


def scores(path):
    tmp = f'/tmp/.cuts-{os.getpid()}.txt'
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-an', '-vf',
                        f"select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file={tmp}",
                        '-f', 'null', '-'], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-600:])
    txt = open(tmp).read(); os.remove(tmp)
    return [(float(t), float(s)) for t, s in
            re.findall(r'pts_time:([\d.]+)\s*\nlavfi.scene_score=([\d.]+)', txt)]


def duration(fr):
    """Длина файла по последнему кадру (кадров мало, шаг — первый интервал)."""
    return fr[-1][0] + (fr[1][0] - fr[0][0] if len(fr) > 1 else 0)


def pick(fr, centre, half):
    """Всплеск у ожидаемого места. Если рядом два почти равных (в кусок иногда
    попадают пара кадров следующего плана), берём тот, что ближе к сетке."""
    cand = [(s, t) for t, s in fr if abs(t - centre) <= half]
    if not cand:
        return (0.0, centre)
    top = max(cand)[0]
    near = [(abs(t - centre), -s, t) for s, t in cand if s >= top * 0.5]
    _, ns, t = min(near)
    return (-ns, t)


def find(path):
    fr = scores(path)
    total = duration(fr)
    # готовая нарезка — CUTS кусков по STEP секунд; у другого файла сетка не сойдётся,
    # и скрипт напечатал бы выдуманные времена, похожие на настоящие
    if abs(total - CUTS * STEP) > 1.5:
        sys.exit(f'файл длится {total:.1f} с, а нарезка из {CUTS} кусков по {STEP:.2f} с — '
                 f'{CUTS * STEP:.1f} с. Это не готовая нарезка (tools/montage.py), cutTimes не считаю.')
    # проход 1: грубо, по сетке; из него — типичный сдвиг начала
    lead = statistics.median(pick(fr, i * STEP, 0.3)[1] - i * STEP for i in range(1, CUTS))
    # проход 2: узко, вокруг сетки со сдвигом
    out, weak = [], []
    for i in range(1, CUTS):
        s, t = pick(fr, i * STEP + lead, 0.12)
        out.append(round(t, 3))
        if s < 0.12:
            weak.append((i, t, s))
    return out, weak, lead


def main():
    if len(sys.argv) != 2 or not shutil.which('ffmpeg'):
        sys.exit(__doc__)
    cuts, weak, lead = find(sys.argv[1])
    if len(weak) > 5:
        sys.exit(f'слабых стыков {len(weak)} из {CUTS - 1} — файл не похож на нарезку этого вида, '
                 f'времена были бы догадкой. Проверьте файл глазами.')
    gaps = [b - a for a, b in zip([0] + cuts, cuts)]
    print(f'сдвиг сетки : {lead:+.3f} с;  длина кусков {min(gaps):.2f}–{max(gaps):.2f} с')
    for i, t, s in weak:
        print(f'  слабый стык #{i} на {t:.2f} с (всплеск {s:.2f}) — проверьте глазами')
    print('cutTimes: [' + ', '.join(f'{t:g}' for t in cuts) + '],')


if __name__ == '__main__':
    main()
