#!/usr/bin/env python3
"""
Готовая нарезка для сайта: режет мастер на CUTS кусков и склеивает их в короткий ролик.

    python3 tools/montage.py master.mov --name kirill
    python3 tools/montage.py master.mov --name kirill --start 19 --end 182.5
    python3 tools/montage.py master.mov --name kirill --order chrono --pace even   # как раньше

Без --start/--end границы подбираются сами: blackdetect находит чёрные поля
по краям. Возрастную плашку и заставку студии он не видит — их нужно
отсечь руками, иначе они попадут в нарезку и будут бить вспышкой на тёмном
фоне сайта. Скрипт показывает, что получилось, и предупреждает, если первый
кусок слишком светлый. Заставка студии (красно-зелёно-голубой логотип) и чёрное по краям
окна кусков вырезаются сами; если заставка нашлась посередине куска, скрипт скажет, а
срезать начало куска вручную можно через --skip (см. ниже).

Если у мастера чёрные полосы (scope в кадре 16:9), срежьте их: рамку
подскажет `ffmpeg -ss 120 -t 20 -i master.mov -vf cropdetect -f null -`,
а дальше `--crop 1920:816:0:132`. Иначе полосы попадут в файл и на сайте
кадр будет не во весь экран.

ПОРЯДОК кусков (--order). По умолчанию куски идут МИКСОМ, как в трейлере: начало,
вторая половина, конец, снова начало и так далее, а не по ходу фильма. Фильм делится
на три зоны (начало / середина / конец); куски берутся из зон по кругу, а порядок
внутри зоны подбирается так, чтобы соседние куски были непохожи (другие люди, место,
свет), два тёмных не шли подряд, а кадры без движения попадали на долгие куски.
Первым всегда стоит самый первый кусок фильма.
  --order mix      (по умолчанию) микс; --seed N даёт другой вариант
  --order chrono   по порядку фильма
  --order 0,10,20,1,…   свой порядок: номера кусков фильма в том порядке, как они
                        пойдут в нарезке (29 разных чисел)

ДИНАМИКА (--pace). По умолчанию склейки идут с разным ритмом, как в трейлере: три
«волны» — кусок за куском всё короче, потом долгий кадр-вдох, и снова разгон; в
конце долгий кадр, который зацикливается на начало. Куски от ~0.4 с (вспышки) до
~1.85 с (удержание). Короткий кусок — это середина прежнего окна в 1.6 с (при том
же ×1.28), долгий — всё окно, чуть замедленное (не медленнее ×0.85, иначе кадры
дёргаются). Куски обрезаются по чёрному на краях.
  --pace trailer   (по умолчанию)
  --pace even      все куски по 1.25 с, как было
  --skip 0=0.75    у куска 0 пропустить первые 0.75 с окна (например, заставку студии;
                   несколько: --skip 0=0.75,12=0.3)

После нарезки скрипт сам находит, где в готовом файле начинаются куски (cutTimes), и
печатает cutOrder и cutTimes для films.js. Если у фильма есть focus (кадрирование
вертикального экрана), он задан по месту в нарезке — после смены порядка его нужно
перенести по куску фильма: focus_новый[j] = focus_старый[p], где
cutOrder_старый[p] == cutOrder_новый[j] (у хронологической нарезки cutOrder[p] = p).

Результат: <name>.mp4, <name>.webm, <name>-poster.jpg в assets/films/.
В films.js такому файлу ставится prerendered: true.
"""
import argparse, os, random, re, shutil, subprocess, sys

CUTS, RATE, CUT_SEC = 29, 1.28, 1.6
HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.normpath(os.path.join(HERE, '..', 'assets', 'films'))
sys.path.insert(0, HERE)

FAST_MAX = CUT_SEC / RATE      # 1.25 с: до этой длины кусок — середина окна при ×RATE
MIN_RATE = 0.85                # медленнее долгий кусок не тянем: кадры начнут дёргаться
SAMPLE_FPS = 10                # миниатюры окна для анализа — раз в 0.1 с
TW, TH = 24, 14                # размер миниатюры
BLACK_LUMA = 6                 # средняя яркость, ниже которой кадр считается чёрным

# Ритм «трейлер»: длительность куска на месте j, секунды. Три волны разгона; долгие
# кадры (≈1.8 с) стоят в начале, посередине и в конце. Всего ≈ 26 с на 29 кусков.
PACE_TRAILER = [1.85, 1.5, 1.3, 1.1, 0.9, 0.8, 0.7, 0.6, 0.55,
                1.8, 1.1, 0.85, 0.7, 0.6, 0.5, 0.5, 0.45, 0.4,
                1.85, 1.3, 0.95, 0.75, 0.6, 0.5, 0.45, 0.4, 0.4, 0.5, 1.8]
assert len(PACE_TRAILER) == CUTS


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(tool):
    if not shutil.which(tool):
        sys.exit(f'нет {tool} — поставьте ffmpeg')


def duration(path):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', path])
    return float(r.stdout.strip())


def black_spans(path):
    """Все чёрные промежутки: и поля по краям, и паузы внутри фильма."""
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', path,
             '-vf', 'blackdetect=d=0.5:pix_th=0.06', '-an', '-f', 'null', '-'])
    return [(float(a), float(b)) for a, b in
            re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', r.stderr)]


def black_edges(spans, total):
    """Границы содержания: отбрасываем чёрное, прилипшее к краям."""
    start, end = 0.0, total
    for a, b in spans:
        if a < 1.0:
            start = max(start, b)
    for a, b in spans:
        if b > total - 1.0:
            end = min(end, a)
    return start, end


def cuts_in_black(start, seg, spans):
    """Куски, которые попадут в чёрную паузу: на сайте это читается как сбой."""
    bad = []
    for i in range(CUTS):
        a, b = start + i * seg, start + i * seg + CUT_SEC
        for s0, s1 in spans:
            if a < s1 and b > s0:
                bad.append((i, round(a, 1)))
                break
    return bad


def brightness(path, t):
    """Средняя яркость кадра в момент t — чтобы поймать белую заставку."""
    data = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path,
                           '-frames:v', '1', '-vf', 'scale=64:36,format=gray',
                           '-f', 'rawvideo', '-'], capture_output=True).stdout
    return (sum(data) / len(data)) if data else 0.0


# ── анализ окон ───────────────────────────────────────────────────────────────

def luma(px):
    n = len(px) // 3
    return (sum(px[0::3]) * 0.299 + sum(px[1::3]) * 0.587 + sum(px[2::3]) * 0.114) / n


def dist(a, b):
    """Насколько два кадра непохожи: средняя разница по цвету, 0…255."""
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def is_ident(px):
    """
    Заставка студии: красный, зелёный и голубой сразу и помногу (логотип института
    крутится в первых кадрах мастера). Ночной кадр с красной машиной или синей
    толстовкой этим не проходит: цветов там по одному.
    """
    r = g = b = 0
    for i in range(0, len(px), 3):
        R, G, B = px[i], px[i + 1], px[i + 2]
        if R > 150 and G < 80 and B < 100: r += 1
        if G > 130 and R < 140 and B < 140 and G > R + 30: g += 1
        if B > 140 and R < 100 and G > 90 and B > G + 20: b += 1
    n = len(px) // 3
    return r / n > 0.06 and g / n > 0.04 and b / n > 0.04


def analyze(master, start, seg, crop):
    """По окну каждого куска фильма — миниатюры раз в 1/SAMPLE_FPS с: [(t от начала окна, RGB)]."""
    vf = (f'crop={crop},' if crop else '') + f'fps={SAMPLE_FPS},scale={TW}:{TH},format=rgb24'
    size = TW * TH * 3
    out = []
    for i in range(CUTS):
        data = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{start + i * seg:.3f}',
                               '-t', f'{CUT_SEC:.3f}', '-i', master, '-an', '-vf', vf,
                               '-f', 'rawvideo', '-'], capture_output=True).stdout
        out.append([(k / SAMPLE_FPS, data[k * size:(k + 1) * size]) for k in range(len(data) // size)])
    return out


def plan_window(frames, skip=0.0):
    """
    Пригодная часть окна (с от его начала): самый длинный ряд подряд идущих кадров,
    где нет чёрного и нет заставки студии, после пропущенного через --skip. У обычного
    куска это всё окно 0…CUT_SEC; у куска, который начинается с заставки, а за ней
    чёрная пауза — только сам кадр после паузы (одиночные остатки заставки до паузы
    не в счёт).
    """
    good = [t >= skip - 1e-6 and luma(px) >= BLACK_LUMA and not is_ident(px) for t, px in frames]
    runs, k = [], 0
    while k < len(good):
        if good[k]:
            j = k
            while j + 1 < len(good) and good[j + 1]:
                j += 1
            runs.append((k, j))
            k = j + 1
        else:
            k += 1
    if not runs:
        return skip, CUT_SEC
    k0, k1 = max(runs, key=lambda r: (r[1] - r[0], -r[0]))
    return frames[k0][0], min(CUT_SEC, frames[k1][0] + 1.0 / SAMPLE_FPS)


def motion(frames, lo, hi):
    """Сколько в окне движения: средняя разница соседних миниатюр. Чем меньше, тем спокойнее кадр."""
    fs = [px for t, px in frames if lo - 1e-6 <= t <= hi]
    if len(fs) < 2:
        return 0.0
    return sum(dist(a, b) for a, b in zip(fs, fs[1:])) / (len(fs) - 1)


def mid_frame(frames, lo, hi):
    mid = (lo + hi) / 2
    return min(frames, key=lambda f: abs(f[0] - mid))[1] if frames else bytes(TW * TH * 3)


def plan_cut(D, lo, hi):
    """
    Из пригодной части окна [lo, hi] делает кусок нужной длины D (с в готовом файле).
    Возвращает (начало от начала окна, длина исходника W, скорость, итоговая длина).
    Короткий (D ≤ 1.25 с): середина окна при обычных ×RATE. Долгий: всё окно, замедленное.
    """
    avail = hi - lo
    if D <= FAST_MAX:
        W = min(avail, D * RATE)
        return lo + (avail - W) / 2, W, RATE, W / RATE
    W = avail
    rate = W / D
    if rate < MIN_RATE:
        rate, D = MIN_RATE, W / MIN_RATE
    elif rate > RATE:
        rate, D = RATE, W / RATE
    return lo, W, rate, D


# ── порядок кусков ────────────────────────────────────────────────────────────

def zones():
    """Три зоны фильма: начало, середина, конец (куски 0…9, 10…19, 20…28)."""
    k = -(-CUTS // 3)
    return [list(range(z * k, min(CUTS, (z + 1) * k))) for z in range(3)]


def zscore(xs):
    m = sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5 or 1.0
    return [(x - m) / sd for x in xs]


def mix_order(thumb, lum, calm, pace, seed=1, tries=40000):
    """
    Микс как в трейлере: из зон по кругу (начало, середина, конец, снова начало …),
    внутри зоны порядок свободный. Из случайных вариантов выбирается тот, у которого
    соседние куски (и конец с началом, ведь нарезка идёт по кругу) самые непохожие,
    два тёмных не стоят рядом, куски, лежащие в фильме рядом, не соседствуют, спокойные
    кадры попадают на долгие места ритма, а тёмные на долгие не попадают.
    Первым всегда кусок 0 — начало фильма.
    """
    rnd = random.Random(seed)
    zs = zones()
    dm = [[dist(thumb[a], thumb[b]) for b in range(CUTS)] for a in range(CUTS)]
    zp, zc = zscore(pace), zscore(calm)
    best, best_score = None, -1e9
    for _ in range(tries):
        pools = [z[:] for z in zs]
        for p in pools:
            rnd.shuffle(p)
        pools[0].remove(0)
        pools[0].insert(0, 0)
        seq = [pools[j % 3].pop(0) for j in range(CUTS)]
        score, worst = 0.0, 1e9
        for a, b in zip(seq, seq[1:] + seq[:1]):
            d = dm[a][b]
            score += d
            worst = min(worst, d)
            if abs(a - b) <= 2:
                score -= 40                      # соседи по фильму — это уже не микс
            if lum[a] < 28 and lum[b] < 28:
                score -= 25                      # два тёмных подряд — провал ритма
        score += worst * 3                       # и пара почти одинаковых тоже плоха
        for j, i in enumerate(seq):
            score += 5 * zp[j] * zc[i]           # спокойное — на долгое, движение — на короткое
            if pace[j] >= 1.4 and lum[i] < 20:
                score -= 40                      # на долгом куске тёмный кадр скучен
        if score > best_score:
            best, best_score = seq, score
    return best


def parse_order(spec, thumb, lum, calm, pace, seed):
    if spec == 'chrono':
        return list(range(CUTS))
    if spec == 'mix':
        return mix_order(thumb, lum, calm, pace, seed)
    try:
        order = [int(x) for x in spec.split(',')]
    except ValueError:
        order = []
    if sorted(order) != list(range(CUTS)):
        sys.exit(f'--order: нужно mix, chrono или {CUTS} разных номеров от 0 до {CUTS - 1} через запятую')
    return order


def parse_skip(spec):
    out = {}
    for part in filter(None, (spec or '').split(',')):
        try:
            i, s = part.split('=')
            out[int(i)] = float(s)
        except ValueError:
            sys.exit('--skip: нужно вида 0=0.75 или 0=0.75,12=0.3')
    return out


# ── фильтр ffmpeg ─────────────────────────────────────────────────────────────

def build_filter(start, seg, path, crop, width, order, plans):
    """
    crop — 'W:H:X:Y' для мастеров с чёрными полосами (letterbox).
    order[j] — какой по счёту кусок фильма встанет в нарезке на место j;
    plans[j] — (начало от начала окна, длина исходника, скорость, итоговая длина).
    """
    pre = []
    if crop:  pre.append(f'crop={crop}')
    if width: pre.append(f'scale={width}:-2')
    head = '[0:v]' + (','.join(pre) + ',' if pre else '')
    parts = [head + 'split=%d' % CUTS + ''.join(f'[s{j}]' for j in range(CUTS)) + ';']
    for j, i in enumerate(order):
        off, W, rate, _ = plans[j]
        parts.append(f'[s{j}]trim=start={start + i * seg + off:.4f}:duration={W:.4f},'
                     f'setpts=(PTS-STARTPTS)/{rate:.5f}[v{j}];')
    parts.append(''.join(f'[v{j}]' for j in range(CUTS)) +
                 f'concat=n={CUTS}:v=1:a=0,format=yuv420p[out]')
    open(path, 'w').write(''.join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('master')
    ap.add_argument('--name', required=True, help='имя файлов на выходе')
    ap.add_argument('--start', type=float)
    ap.add_argument('--end', type=float)
    ap.add_argument('--crf', type=int, default=25)
    ap.add_argument('--crop', help='W:H:X:Y — срезать letterbox; подсказку даёт cropdetect')
    ap.add_argument('--width', type=int, default=1280, help='ширина на выходе')
    ap.add_argument('--order', default='mix', help='mix (по умолчанию) | chrono | 0,10,20,…')
    ap.add_argument('--pace', default='trailer', choices=['trailer', 'even'], help='ритм склеек')
    ap.add_argument('--skip', help='пропустить начало окна у кусков: 0=0.75,12=0.3')
    ap.add_argument('--seed', type=int, default=1, help='другой вариант микса')
    ap.add_argument('--out', default=FILMS)
    a = ap.parse_args()

    need('ffmpeg'); need('ffprobe')
    total = duration(a.master)
    spans = black_spans(a.master)
    auto_s, auto_e = black_edges(spans, total)
    start = a.start if a.start is not None else auto_s
    end = a.end if a.end is not None else auto_e

    print(f'мастер      : {total:.1f} с')
    print(f'чёрные поля : до {auto_s:.2f} и после {auto_e:.2f}')
    print(f'режем       : {start:.2f} – {end:.2f} ({end - start:.1f} с)')
    if end - start < CUTS * CUT_SEC:
        sys.exit(f'диапазон короче {CUTS * CUT_SEC:.0f} с — куски перекроются')

    os.makedirs(a.out, exist_ok=True)
    flt = os.path.join(a.out, f'.{a.name}-filter.txt')
    seg = (end - start) / CUTS
    skip = parse_skip(a.skip)

    print('анализирую куски …')
    frames = analyze(a.master, start, seg, a.crop)
    wins = [plan_window(frames[i], skip.get(i, 0.0)) for i in range(CUTS)]
    thumb = [mid_frame(frames[i], *wins[i]) for i in range(CUTS)]
    lum = [luma(t) for t in thumb]
    calm = [-motion(frames[i], *wins[i]) for i in range(CUTS)]

    pace = PACE_TRAILER if a.pace == 'trailer' else [FAST_MAX] * CUTS
    order = parse_order(a.order, thumb, lum, calm, pace, a.seed)
    plans = [plan_cut(pace[j], *wins[order[j]]) for j in range(CUTS)]
    durs = [p[3] for p in plans]
    build_filter(start, seg, flt, a.crop, a.width, order, plans)

    print(f'порядок     : {a.order}' + (f' (seed {a.seed})' if a.order == 'mix' else ''))
    print(f'ритм        : {a.pace}, куски {min(durs):.2f}–{max(durs):.2f} с, итог {sum(durs):.1f} с')
    print('cutOrder: [' + ', '.join(map(str, order)) + '],')
    inner = [(i, t) for i in range(CUTS) for t, px in frames[i] if wins[i][0] < t < wins[i][1] and is_ident(px)]
    if inner:
        print('ВНИМАНИЕ: заставка студии внутри кусков: ' + ', '.join(f'#{i} на {t:.1f} с окна' for i, t in inner) +
              ' — срежьте начало через --skip')
    trimmed = [(i, round(lo, 2), round(hi, 2)) for i, (lo, hi) in enumerate(wins) if lo > 0.05 or hi < CUT_SEC - 0.05]
    if trimmed:
        print('обрезано по чёрному/skip (кусок, от, до в окне): ' + ', '.join(f'#{i} {lo}–{hi}' for i, lo, hi in trimmed))
    if a.crop:  print(f'кадрирую    : {a.crop}')
    if a.width: print(f'ширина      : {a.width}')

    bad = cuts_in_black(start, seg, spans)
    if bad:
        print('ВНИМАНИЕ: в чёрное попадают куски ' +
              ', '.join(f'#{i} ({t} с)' for i, t in bad) +
              ' — подвиньте --end на пару секунд и перезапустите')

    lum0 = brightness(a.master, start + 0.3)
    if lum0 > 170:
        print(f'ВНИМАНИЕ: первый кадр очень светлый ({lum0:.0f}/255) — похоже на '
              f'заставку. Задайте --start вручную или срежьте её через --skip.')

    mp4 = os.path.join(a.out, f'{a.name}.mp4')
    webm = os.path.join(a.out, f'{a.name}.webm')
    poster = os.path.join(a.out, f'{a.name}-poster.jpg')

    print('кодирую mp4 …')
    r = run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.master,
             '-filter_complex_script', flt, '-map', '[out]', '-an',
             '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf),
             '-g', '50', '-movflags', '+faststart', mp4])
    if r.returncode: sys.exit(r.stderr[-800:])

    print('кодирую webm …')
    r = run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4,
             '-c:v', 'libvpx-vp9', '-crf', str(a.crf + 9), '-b:v', '0',
             '-deadline', 'good', '-cpu-used', '4', '-row-mt', '1', '-an', webm])
    if r.returncode: sys.exit(r.stderr[-800:])

    os.remove(flt)

    # где в готовом файле на самом деле начинаются куски
    import cuts
    found, weak, lead = cuts.find(mp4, durs)

    # постер — кадр из середины куска 0 (не позже 1.0 с): сайт ставит на него окно куска 0
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{min(1.0, found[0] / 2):.3f}', '-i', mp4,
         '-frames:v', '1', '-vf', 'scale=1280:-1', '-q:v', '4', poster])

    for f in (mp4, webm, poster):
        print(f'  {os.path.basename(f):<22}{os.path.getsize(f) / 1048576:6.1f} МБ')
    gaps = [b - a for a, b in zip([0.0] + found, found)]
    off = [(j, round(g, 2), round(durs[j], 2)) for j, g in enumerate(gaps) if abs(g - durs[j]) > 0.12]
    print(f'\ncutDurations: [{", ".join(f"{d:.2f}" for d in durs)}],')
    print('cutTimes: [' + ', '.join(f'{t:g}' for t in found) + '],')
    if weak:
        print('слабые стыки (проверьте глазами): ' + ', '.join(f'#{i} на {t:.2f} с' for i, t, s in weak))
    if off:
        print('ВНИМАНИЕ: длина кусков в файле расходится с планом больше чем на 0.12 с: ' +
              ', '.join(f'#{j}: {g} вместо {d}' for j, g, d in off))
    print(f'\nв films.js: prerendered: true, src: [\'assets/films/{a.name}.webm\', '
          f'\'assets/films/{a.name}.mp4\']')


if __name__ == '__main__':
    main()
