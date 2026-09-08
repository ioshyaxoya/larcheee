# BOMBAY MAIL — шаблон промпта для генерации референсов

*Приложение к `docs/visual_direction.md`. Версия 1.0.*

Этот файл — **источник истины** для `tools/asset_gen.py`: инструмент читает
блоки ниже по якорям и склеивает промпт сам. Править промпты — здесь, не в
скрипте, и не в чате при каждом вызове.

---

## 0. Что генератор нам даёт, а что нет

Генератор изображений даёт **референс**, а не ассет. Причина не в стиле, а в
механике: у нас цвет каждого контура живёт в данных, и на этом держатся два
закона игры.

- **Затухание с глубиной.** Пол, стены и фигуры в глубине вагона гаснут потому,
  что их цвет пересчитан по координате (`dim()` в `tools/draw_car_01.py`).
  Запечённая текстура свой цвет несёт с собой и гаснуть не умеет.
- **Закон цвета A10.** Цвет есть накопленное время: в испытании мир
  монохромный, и `colour_return` возвращает цвет по выигранным раундам.
  Текстура этому закону не подчиняется — она уже цветная.

Плюс третье, мелкое, но заметное: лужи света складываются аддитивно с плоским
полем; по фотографической текстуре они читаются мутью, а не светом.

Поэтому путь такой:

```
описание → генератор → PNG-референс → tools/trace_to_contours.py → контуры в data/ → движок
```

Кодер больше не выдумывает форму из окружностей и трапеций — но конвейер
остаётся один, и оба закона продолжают работать. **PNG в `data/` не попадает
никогда.** Исключения — то, что не участвует в механике: key art по
`docs/cover_brief.md`, титульный экран, иконки. Их можно оставить растром.

---

## 1. Стилевой префикс (обязателен во всех вызовах)

Генеративная модель не читала `visual_direction.md`. Без префикса получится
сорок вагонов в сорока стилях — просто более гладких, чем примитивы. Префикс
идёт первым в каждом промпте, `tools/asset_gen.py` подставляет его сам и без
него не запускается.

<!-- style-prefix -->
```text
Flat vector illustration, theatrical 2.5D stage art. Absolutely flat fills:
no gradients, no soft shading, no textures, no photographic detail, no 3D
render look, no bevels, no glow, no lens effects. Shapes read by silhouette and
by clean steps of value, not by rendering. Limited palette, no more than twelve
colours in the whole image. Hard edges between colour fields. No outlines
unless stated. Reference art of Kentucky Route Zero for staging and flatness;
1890s British India as the world. Plain solid background, single colour, no
scenery unless stated. No text, no captions, no letters, no signature, no
watermark, no frame, no border. Single subject, centred, fully inside the
frame with margin on every side.
```

Два правила поверх префикса, оба из практики генераторов:

1. **Никогда не просить прозрачный фон** — модель впечатает шахматку. Просить
   сплошной цвет и снимать его потом (у нас это делает трассировщик по
   `--bg-tol`, а не отдельный шаг).
2. **Не полагаться на «лицом влево/вправо»** — направление модели путают, и
   платить за зеркало не нужно: генерировать одно направление и отражать в
   данных (`flipped()` в рисовальных скриптах уже это делает).

---

## 2. Шаблоны по виду ассета

Подставляется `{описание}` — то, что пишет автор. Остальное фиксировано.

### Присутствие (бог)

Единственный вид, который рисуется по другому закону, чем весь мир
(`visual_direction.md` §3.1): лицо есть, глазурь в три тона плюс блик, полная
иконография. Ему и генерировать надо иначе.

<!-- kind: presence -->
```text
A Hindu deity in the manner of traditional devotional poster art and Amar
Chitra Katha comics: frontal, symmetrical, seated or standing, calm and
motionless, looking straight at the viewer. Glazed toy finish: three clean
tones on every form plus one small specular highlight, like painted lacquered
vinyl. The face is present, still and expressionless, never distorted, never
sexualised, never comic. Gold ornament rendered as flat gold with one light
step. Pale disc halo behind the head. Canonical attributes only, exactly as
listed. {описание}
```

К этому — обязательная сверка: иконография берётся из источников, не по
памяти, и это записано как требование в `visual_direction.md` §3.2. Модерация
Gemini и Grok на религиозные образы существует; см. §5.

### Человек (пассажир, служащий, задержавший)

<!-- kind: person -->
```text
A single flat silhouette figure of a person, one solid colour for the body,
no face, no facial features at all, no outline. The figure is recognised only
by clothing shape and by what is in the hands. Neutral standing or seated pose,
side or three-quarter view, feet on an implied ground line. {описание}
```

### Реквизит и обстановка вагона

<!-- kind: prop -->
```text
A single object drawn as flat colour fields for a side-on theatrical stage:
straight-on side view, no perspective, no cast shadow, no reflections, no
material realism. Dark structural parts, light loaded parts, one or two metal
accents. Wood, brass and iron of the 1890s Indian railways. {описание}
```

### Задник и мир испытания

Мир испытания уходит в однобитный точечный растр, а тот шумит на середине
тона. Поэтому задник должен быть **светлым**, а тёмное — только малыми формами.

<!-- kind: backdrop -->
```text
A wide flat backdrop in high key: pale, almost white ground and sky, soft light
grey mid tones, and only small dark accents — a stone, a bare tree, a distant
figure. No dark masses, no heavy foreground, no vignette. Layers of land
reading as clean steps of value from light at the horizon to slightly deeper
near the viewer, every edge a curve, never a straight horizontal line across
the image. {описание}
```

### Key art и титульный экран

Единственный случай, где растр остаётся растром: в механике не участвует.

<!-- kind: keyart -->
```text
Key art for a game cover: one composition, dramatic staging, flat colour
fields, no gradients or photographic rendering, room left clear at the top for
a title that is not drawn. {описание}
```

---

## 3. Как вызывать

```bash
# посмотреть, что уйдёт в модель, и сколько это стоит — без вызова и без денег
python3 tools/asset_gen.py --kind presence --dry-run \
  --describe "Shani: dark blue skin, blue robes, four arms holding arrow, bow,
              raised palm, hand on knee; trident; tall gold crown; seated
              cross-legged on a giant crow with spread wings" \
  -o refs/shani.png

# сгенерировать (нужны ключи и подтверждение расхода)
python3 tools/asset_gen.py --kind presence --model gemini --size 1K --yes \
  --describe "..." -o refs/shani.png

# референс → контуры → в данные
python3 tools/trace_to_contours.py refs/shani.png -o data/traced/shani.json \
  --height 5.2 --palette shani --preview refs/shani_traced.png
```

Референсы живут в `refs/` и в игру не попадают. В `data/` попадают только
контуры. Каждый вызов пишет рядом `.prompt.txt` и строку в
`docs/asset_ledger.md` — иначе через месяц никто не скажет, чем это сделано и
во что обошлось.

---

## 4. Деньги

Проверено по `asset-gen/SKILL.md` в godogen на момент интеграции:

| Что | Модель | Цена |
|---|---|---|
| Текстура, простой предмет | Grok | 2¢ |
| Референс, персонаж, точная композиция | Gemini 1K | 7¢ |
| То же в 512 / 2K / 4K | Gemini | 5¢ / 10¢ / 15¢ |
| Видео (нам не нужно) | Grok | 5¢/с |
| 3D-модель, риг, ретаргет (нам не нужны) | Tripo3D | 30¢ / +25¢ / 10¢ |

Это не «2¢ стандарт и 7¢ pro», как звучит в пересказе: это два разных
поставщика, и Grok дешевле, но хуже слушает промпт. Для присутствий и всего,
где важна иконография, — только Gemini.

**Порядок величин для M3.** Восемь присутствий по 3–5 попыток на Gemini 1K —
около 2–3 $. Сорок вагонов по 6–10 предметов на Grok — около 20–30 $ с
переделками. Это статья бюджета, которой в ТЗ не было: раньше считалось время
художника, теперь ещё и генерация. Порядок разумный, но не ноль.

---

## 5. Ограничения, которые надо проверить на практике

1. **Ключи.** Нужны `GOOGLE_API_KEY` и `XAI_API_KEY` в окружении. Без них
   инструмент останавливается с внятным сообщением, а не молча.
2. **Модерация.** У Gemini и Grok свои политики на религиозные образы.
   Проверять надо именно на присутствиях — на том, что нам нужнее всего.
   Если режет: генерировать композицию и атрибуты отдельно от лица, а лицо
   рисовать контурами, как сейчас.
3. **Стиль всё равно уплывёт.** Префикс держит рамку, но не гарантирует
   попадания. Правило: одно присутствие рисуется первым и становится
   эталоном, дальше остальные семь идут через `--image` от него
   (image-to-image), а не с нуля. Так делается семья стиля.

---

## 6. Откуда это взято

Конвейер и цены — из [godogen](https://github.com/htdt/godogen) (MIT,
© 2026 Alex Ermolov), скилл `asset-gen`. Оттуда взяты идея разделения труда
(модель рисует, кодер расставляет), состав поставщиков и практические правила:
не просить прозрачный фон, не верить направлению взгляда, вести реестр ассетов
с размером в игровых единицах.

Не взято намеренно: их движковый гид (`engines/godot.md`) — он про **C#/.NET**,
а у нас GDScript; и весь 3D-путь (Tripo3D, риг, видео) — `visual_direction.md`
отменяет 3D low-poly, нам нечего ригать. `publish.sh` тоже не применим: он
создаёт новый проект с нуля, а не встраивается в существующий.
