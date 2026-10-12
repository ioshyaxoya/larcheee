#!/usr/bin/env python3
"""
Готовая нарезка для сайта: режет мастер на CUTS кусков, ускоряет и склеивает.

    python3 tools/montage.py master.mov --name kirill
    python3 tools/montage.py master.mov --name kirill --start 19 --end 182.5

Без --start/--end границы подбираются сами: blackdetect находит чёрные поля
по краям. Возрастную плашку и заставку студии он не видит — их нужно
отсечь руками, иначе они попадут в нарезку и будут бить вспышкой на тёмном
фоне сайта. Скрипт показывает, что получилось, и предупреждает, если первый
кусок слишком светлый.

Если у мастера чёрные полосы (scope в кадре 16:9), срежьте их: рамку
подскажет `ffmpeg -ss 120 -t 20 -i master.mov -vf cropdetect -f null -`,
а дальше `--crop 1920:816:0:132`. Иначе полосы попадут в файл и на сайте
кадр будет не во весь экран.

Результат: <name>.mp4, <name>.webm, <name>-poster.jpg в assets/films/.
В films.js такому файлу ставится prerendered: true.
"""
import argparse, json, os, re, shutil, subprocess, sys

CUTS, RATE, CUT_SEC = 29, 1.28, 1.6
HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.normpath(os.path.join(HERE, '..', 'assets', 'films'))


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


def build_filter(start, end, path, crop=None, width=None):
    """crop — 'W:H:X:Y' для мастеров с чёрными полосами (letterbox)."""
    seg = (end - start) / CUTS
    pre = []
    if crop:  pre.append(f'crop={crop}')
    if width: pre.append(f'scale={width}:-2')
    head = '[0:v]' + (','.join(pre) + ',' if pre else '')
    parts = [head + 'split=%d' % CUTS + ''.join(f'[s{i}]' for i in range(CUTS)) + ';']
    for i in range(CUTS):
        parts.append(f'[s{i}]trim=start={start + i * seg:.4f}:duration={CUT_SEC},'
                     f'setpts=(PTS-STARTPTS)/{RATE}[v{i}];')
    parts.append(''.join(f'[v{i}]' for i in range(CUTS)) +
                 f'concat=n={CUTS}:v=1:a=0,format=yuv420p[out]')
    open(path, 'w').write(''.join(parts))
    return seg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('master')
    ap.add_argument('--name', required=True, help='имя файлов на выходе')
    ap.add_argument('--start', type=float)
    ap.add_argument('--end', type=float)
    ap.add_argument('--crf', type=int, default=25)
    ap.add_argument('--crop', help='W:H:X:Y — срезать letterbox; подсказку даёт cropdetect')
    ap.add_argument('--width', type=int, default=1280, help='ширина на выходе')
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
    seg = build_filter(start, end, flt, a.crop, a.width)
    print(f'шаг         : {seg:.3f} с, итог {CUTS * CUT_SEC / RATE:.2f} с')
    if a.crop:  print(f'кадрирую    : {a.crop}')
    if a.width: print(f'ширина      : {a.width}')

    bad = cuts_in_black(start, seg, spans)
    if bad:
        print('ВНИМАНИЕ: в чёрное попадают куски ' +
              ', '.join(f'#{i} ({t} с)' for i, t in bad) +
              ' — подвиньте --end на пару секунд и перезапустите')

    lum = brightness(a.master, start + 0.3)
    if lum > 170:
        print(f'ВНИМАНИЕ: первый кадр очень светлый ({lum:.0f}/255) — похоже на '
              f'заставку. Задайте --start вручную.')

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

    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '1.0', '-i', mp4,
         '-frames:v', '1', '-vf', 'scale=1280:-1', '-q:v', '4', poster])
    os.remove(flt)

    for f in (mp4, webm, poster):
        print(f'  {os.path.basename(f):<22}{os.path.getsize(f) / 1048576:6.1f} МБ')
    print(f'\nв films.js: prerendered: true, src: [\'assets/films/{a.name}.webm\', '
          f'\'assets/films/{a.name}.mp4\']')


if __name__ == '__main__':
    main()
