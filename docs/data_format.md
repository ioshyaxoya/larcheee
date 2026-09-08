# BOMBAY MAIL — формат рантайм-данных

Карточка вагона (`data/cars/car_NN.json`) описана в ТЗ B4 и `docs/car_01_brake_van.md` §0;
её проверяет `tools/car_validator.py` по чеклисту B7. Этот документ описывает
**рантайм-данные**, которые читает движок: NPC, графы диалогов, столкновения, квесты.
Их проверяет `tools/dialogue_validator.py`. Общий язык условий и эффектов — один на всё.

| Каталог | Что | Кто читает |
|---|---|---|
| `data/npcs/<id>.json` | NPC: имя, положение, оси отношения, диалог, условия появления | `src/train/car` |
| `data/dialogues/<id>.json` | граф диалога | `src/dialogue` |
| `data/encounters/<id>.json` | столкновение = триггер по событию вагона | `src/train/car/trigger_system.gd` |
| `data/prologue/quest_<id>.json` | квест на битовых часах (граф + часы + говорящие) | `src/quest` |
| `data/prologue/tags.json` | тег пролога → вагон (B6) | — |
| `data/flags.json` | реестр флагов: `имя: описание` или `имя: {description, type, values}` | все |
| `data/texts/ru.json`, `en.json` | тексты по ключам; строк в данных и коде нет (B5) | `src/core/texts.gd` |
| `data/attitude_axes.json`, `data/pearls.json`, `data/palettes.json` | оси, жемчужины, палитры | валидатор |
| `data/character/*.json` | характеристики, навыки, происхождения, классы (приложение 2) | `src/rules/character` |

**Теги пролога** — флаги `prologue.<tag>` типа `bool`. Условие `{"tag": "union_seed"}` читает `prologue.union_seed`.

## NPC

```jsonc
{
  "id": "god_shani", "name_key": "npc.god_shani.name", "kind": "presence | human | animal",
  "dialogue": "car_01_shani_first",           // id из data/dialogues/, необязателен
  "position": [x, y, z], "silhouette": "dark_lame",
  "attitude_axes": {"record": {"recorded": "text_key", "unrecorded": "text_key"}},   // по осям, не по клеткам (B5)
  "conditions": [ … ]                          // не выполнены — NPC не спавнится
}
```

## Столкновение (триггер)

```jsonc
{"id": "enc_01_bir_singh_woken", "event": "npc_approached", "npc": "npc_bir_singh",
 "once": true, "conditions": [ … ], "effects": [ … ], "dialogue": null}
```

События: `car_entered`, `car_left`, `npc_approached`, `item_taken`, `dialogue_ended`,
`trial_lost_round`, `trial_won`, `trial_soft_reset`, `flag_changed`. Карточка вагона
перечисляет столкновения в `encounters`.

## Квест

```jsonc
{
  "id": "quest_last_half_hour", "kind": "quest", "title_key": "lhh.title", "target_hours": 0.6,
  "entry": "main",
  "clock": {"start_minutes": 1200, "deadline_minutes": 1230, "deadline_label_key": "…"},
  "output_flags": ["prologue.detainer_id", …],
  "npcs": [{"id": "nibaron_das", "name_key": "lhh.npc.nibaron_das"}],   // говорящие квеста
  "dialogues": {"main": {"start": "intro", "nodes": { … }}}
}
```

## Узел диалога

```jsonc
"node_id": {
  "speaker": "npc_id | narrator | player",
  "text_key": "…",                  // реплика ≤ 3 строк (B5)
  "stage": "…",                     // ремарка (ключ текста), B5
  "on_enter": [ эффекты ],
  "options": [ варианты ]           // или "next": "node_id" (кнопка «Дальше»),
                                    // или "branches": [{"conditions": [], "next": "id"}] — первая подошедшая,
                                    // или "end": true
  "pearl": true, "pearl_id": "…"    // уникальная реплика, реестр data/pearls.json
}
```

## Вариант

```jsonc
{
  "text_key": "…",
  "conditions": [ … ],                       // не выполнены — вариант скрыт
  "cost_minutes": 8,                         // цена на битовых часах, видна до выбора
  "cost_on_fail_minutes": 12,                // цена при провале проверки, видна до выбора
  "cost_note_key": "…",
  "check": {"skill": "persuasion", "dc": 12, "label_key": "…"},
        // {"skills_any": ["persuasion", "deception"], "dc": 12} — берётся лучший модификатор
        // {"ability": "str", "dc": 10}
  "chance": {"provider": "bridge_raised", "label_key": "…", "on_hit": "id", "on_miss": "id", "hit_minutes": 4},
  "effects": [ … ], "next": "id",                    // успех / без проверки
  "effects_on_fail": [ … ], "next_on_fail": "id"     // провал; у проверки обязателен
}
```

Все проверки — через `src/rules/checks` (B5). Каждый бросок уходит сигналом
`check_rolled` с кубиком, модификаторами и СЛ; провал не прячется. Бросок шанса —
видимый d20 против порога `round(p × 20)`.

Соглашение квеста «Последние полчаса»: где спека не задаёт цену провала, провал стоит
на 4 минуты дороже успеха.

## Условия

`{"flag": "x", "is": true}` · `{"flag": "x", "equals": v}` · `{"flag": "x", "in": [v…]}` ·
`{"flag": "x", "set": false}` · `{"tag": "t"}` (`"is": false` — отсутствие) ·
`{"origin": "o"}` · `{"origin_in": [o…]}` · `{"class": "c"}` · `{"sex": "m" | "f"}` ·
`{"axis": "skin", "pole": "white"}` · `{"money_min": n}` (анны) · `{"minutes_spent_min": n}` ·
`{"not": усл}` · `{"any": [усл…]}` · `{"all": [усл…]}`

## Эффекты

`{"set_flag": "x", "value": v}` · `{"add_tag": "t"}` ·
`{"add_minutes": n, "reason_key": "…"}` (битовые часы; причина показывается) ·
`{"add_money": n}` · `{"goto": "id"}` · `{"end": true}` ·
`{"emit": "signal_name"}` (хук для `custom_script` / сцены) ·
`{"record_minutes_flag": "prologue.minutes_late"}` (опоздание относительно `clock.deadline_minutes`)

## Провайдеры шанса

`bridge_raised` — понтонный мост разведён: `0.15` при 8 минутах в бите 1, `0.75` при 12
(`quest.last_half_hour.bit1_minutes`). `coin` — 50 %.

## Проверки перед PR

```bash
python tools/term_lint.py .
python tools/car_validator.py data/cars/
python tools/dialogue_validator.py
python tools/hours_estimator.py data/cars/
godot --headless --import --path . && godot --headless --path . -s tests/smoke.gd
```

Godot 4.3: `Godot_v4.3-stable_linux.x86_64` с releases.godotengine.org; CI скачивает сам.
