#!/usr/bin/env python3
"""
Где в готовой нарезке начинаются куски — с точностью до кадра.

    python3 tools/cuts.py assets/films/kirill.mp4
    python3 tools/cuts.py assets/films/kirill.mp4 --durations 1.85,1.5,…   # куски разной длины

Печатает строку для films.js:  cutTimes: [1.32, 2.56, …]  (начало кусков 1…28,
кусок 0 начинается с нуля). Нужна движку, чтобы менять кадрирование на вертикальном
экране ровно на стыке, а не «примерно»: после кодирования куски не делят файл на
равные доли — выходит сдвиг до двух кадров, и кадрирование переключалось бы
чуть раньше склейки.

Как ищет: ffmpeg считает, насколько каждый кадр отличается от предыдущего; склейка —
всплеск. Всплеск выбирается только рядом с ожидаемым местом (кусок = CUT_SEC / RATE
секунд, а если куски разной длины — по --durations, их печатает tools/montage.py),
чтобы движение внутри куска не приняли за склейку. montage.py вызывает это сам. Слабые стыки (похожие
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


def find(path, durations=None):
    """
    durations — задуманная длина каждого из CUTS кусков (с). Нет — куски равные,
    по STEP секунд (прежняя нарезка). Возвращает (времена начала кусков 1…CUTS-1,
    слабые стыки, 0.0).

    Границы ищутся не по одной, а все сразу: из всплесков разницы кадров выбирается
    цепочка из CUTS-1 стыков, в которой и стыки сильные, и расстояния между ними
    близки к задуманным длинам. Поодиночке по плану искать нельзя: у переменной
    частоты кадров исходника куски выходят чуть длиннее/короче плана, ошибка
    копится, и к концу плановые места уходят от настоящих на десятые доли секунды.
    """
    fr = scores(path)
    total = duration(fr)
    dur = list(durations) if durations else [STEP] * CUTS
    want = sum(dur)
    # готовая нарезка — CUTS кусков известной длины; у другого файла сетка не сойдётся,
    # и скрипт напечатал бы выдуманные времена, похожие на настоящие
    if len(dur) != CUTS or abs(total - want) > 1.5:
        sys.exit(f'файл длится {total:.1f} с, а нарезка из {CUTS} кусков должна идти {want:.1f} с. '
                 f'Это не готовая нарезка (tools/montage.py), cutTimes не считаю.')
    ts = [t for t, _ in fr]
    sc = [s for _, s in fr]
    plan, acc = [], 0.0
    for d in dur[:-1]:
        acc += d
        plan.append(acc)
    INF = float('inf')
    # кандидаты каждого стыка: кадры не дальше slack от плана; slack растёт вместе с накопленной ошибкой
    cands = []
    for i, e in enumerate(plan):
        slack = 0.3 + 0.03 * i
        cands.append([k for k, t in enumerate(ts) if abs(t - e) <= slack and t > 0.1])
    best = [{k: (-3 * sc[k] + 8 * (ts[k] - dur[0]) ** 2, None) for k in cands[0]}]
    for i in range(1, len(plan)):
        layer = {}
        for k in cands[i]:
            top, arg = INF, None
            for p, (c, _) in best[i - 1].items():
                gap = ts[k] - ts[p]
                if gap < 0.15:
                    continue
                v = c + 8 * (gap - dur[i]) ** 2
                if v < top:
                    top, arg = v, p
            if arg is not None:
                layer[k] = (top - 3 * sc[k], arg)
        best.append(layer)
    k = min(best[-1], key=lambda x: best[-1][x][0])
    chain = [k]
    for i in range(len(plan) - 1, 0, -1):
        k = best[i][k][1]
        chain.append(k)
    chain.reverse()
    out = [round(ts[k], 3) for k in chain]
    weak = [(i, ts[k], sc[k]) for i, k in enumerate(chain, 1) if sc[k] < 0.12]
    return out, weak, 0.0


def main():
    args = sys.argv[1:]
    durs = None
    if '--durations' in args:
        k = args.index('--durations')
        try:
            durs = [float(x) for x in args[k + 1].split(',')]
        except (IndexError, ValueError):
            sys.exit(__doc__)
        del args[k:k + 2]
    if len(args) != 1 or not shutil.which('ffmpeg'):
        sys.exit(__doc__)
    cuts, weak, lead = find(args[0], durs)
    if len(weak) > 5:
        sys.exit(f'слабых стыков {len(weak)} из {CUTS - 1} — файл не похож на нарезку этого вида, '
                 f'времена были бы догадкой. Проверьте файл глазами.')
    gaps = [b - a for a, b in zip([0] + cuts, cuts)]
    print(f'длина кусков {min(gaps):.2f}–{max(gaps):.2f} с')
    for i, t, s in weak:
        print(f'  слабый стык #{i} на {t:.2f} с (всплеск {s:.2f}) — проверьте глазами')
    print('cutTimes: [' + ', '.join(f'{t:g}' for t in cuts) + '],')


if __name__ == '__main__':
    main()
