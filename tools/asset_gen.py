#!/usr/bin/env python3
"""asset_gen.py — генерация референсов через Gemini и xAI Grok.

Референс, не ассет: в игру попадают контуры, полученные из PNG трассировщиком
(`tools/trace_to_contours.py`), а не сам PNG. Почему так — `docs/asset_prompt_template.md` §0.

Идея разделения труда (модель рисует, кодер расставляет), состав поставщиков и
практические правила взяты из godogen (MIT, © 2026 Alex Ermolov),
скилл `asset-gen`: https://github.com/htdt/godogen

Три вещи этот инструмент делает не так, как обычная обёртка над API, и все три
существуют потому, что без них проект расползётся:

1. **Без стилевого префикса не запускается.** Префикс читается из
   `docs/asset_prompt_template.md` — один источник истины для документа и для
   кода. Модель не читала visual_direction.md; без префикса выйдет сорок
   вагонов в сорока стилях.
2. **Без подтверждения не тратит денег.** Каждый вызов платный, поэтому нужен
   `--yes`, а `--dry-run` показывает готовый промпт и цену бесплатно.
3. **Ведёт реестр.** Рядом с PNG пишется `.prompt.txt`, в
   `docs/asset_ledger.md` — строка с ценой. Иначе через месяц никто не скажет,
   чем это сделано и во что обошлось.

Запуск:
  python3 tools/asset_gen.py --kind presence --dry-run --describe "..." -o refs/x.png
  python3 tools/asset_gen.py --kind prop --model grok --yes --describe "..." -o refs/x.png
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "docs", "asset_prompt_template.md")
LEDGER = os.path.join(ROOT, "docs", "asset_ledger.md")

GEMINI_MODEL = "gemini-3.1-flash-image-preview"
GEMINI_COST = {"512": 5, "1K": 7, "2K": 10, "4K": 15}
GROK_MODEL = "grok-imagine-image"
GROK_COST = 2
GROK_SIZES = ("1K", "2K")
ASPECTS = ("1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3")


# --- промпт ------------------------------------------------------------------

def _block_after(text: str, anchor: str) -> str:
    """Огороженный блок, идущий сразу за якорем-комментарием."""
    m = re.search(re.escape(anchor) + r"\s*```[a-z]*\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("asset_gen: в %s нет блока после «%s» — "
                         "шаблон промпта повреждён" % (os.path.basename(TEMPLATE), anchor))
    return " ".join(m.group(1).split())


def load_prompt_parts() -> tuple:
    if not os.path.exists(TEMPLATE):
        raise SystemExit("asset_gen: нет %s — без стилевого префикса не работаем "
                         "(docs/asset_prompt_template.md §1)" % TEMPLATE)
    with open(TEMPLATE, encoding="utf-8") as fh:
        text = fh.read()
    prefix = _block_after(text, "<!-- style-prefix -->")
    kinds = {}
    for m in re.finditer(r"<!-- kind: ([a-z_]+) -->", text):
        kinds[m.group(1)] = _block_after(text, m.group(0))
    if not kinds:
        raise SystemExit("asset_gen: в шаблоне нет ни одного вида ассета")
    return prefix, kinds


def build_prompt(kind: str, describe: str, background: str) -> str:
    prefix, kinds = load_prompt_parts()
    if kind not in kinds:
        raise SystemExit("asset_gen: вид «%s» не описан в шаблоне (есть: %s)"
                         % (kind, ", ".join(sorted(kinds))))
    body = kinds[kind].replace("{описание}", describe.strip())
    bg = ("Background: a single flat %s, filling the whole frame behind the "
          "subject. Never a transparent or checkered background." % background)
    return "%s %s %s" % (prefix, body, bg)


# --- поставщики --------------------------------------------------------------

def _key(name: str, where: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise SystemExit(
            "asset_gen: нет переменной окружения %s.\n"
            "Ключ берётся здесь: %s\n"
            "Без него генерация невозможна; промпт можно посмотреть с --dry-run."
            % (name, where))
    return val


def gen_gemini(prompt: str, size: str, aspect: str, ref: str | None) -> bytes:
    import requests
    key = _key("GOOGLE_API_KEY", "https://aistudio.google.com/")
    parts: list = [{"text": prompt}]
    if ref:
        with open(ref, "rb") as fh:
            parts.append({"inline_data": {"mime_type": "image/png",
                                          "data": base64.b64encode(fh.read()).decode()}})
    url = ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
           % GEMINI_MODEL)
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"],
                                 "imageConfig": {"aspectRatio": aspect,
                                                 "imageSize": size}}}
    r = requests.post(url, params={"key": key}, json=body, timeout=300)
    if r.status_code != 200:
        raise SystemExit("asset_gen: Gemini ответил %d: %s" % (r.status_code, r.text[:600]))
    data = r.json()
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                return base64.b64decode(blob["data"])
    raise SystemExit("asset_gen: Gemini не вернул изображение. Ответ: %s"
                     % json.dumps(data)[:600])


def gen_grok(prompt: str, aspect: str, ref: str | None) -> bytes:
    import requests
    key = _key("XAI_API_KEY", "https://console.x.ai/home")
    body = {"model": GROK_MODEL, "prompt": prompt, "n": 1,
            "aspect_ratio": aspect, "response_format": "b64_json"}
    if ref:
        with open(ref, "rb") as fh:
            body["image"] = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    r = requests.post("https://api.x.ai/v1/images/generations",
                      headers={"Authorization": "Bearer " + key},
                      json=body, timeout=300)
    if r.status_code != 200:
        raise SystemExit("asset_gen: xAI ответил %d: %s" % (r.status_code, r.text[:600]))
    data = r.json().get("data", [])
    if not data:
        raise SystemExit("asset_gen: xAI не вернул изображение")
    item = data[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        img = requests.get(item["url"], timeout=300)
        if img.status_code == 200:
            return img.content
    raise SystemExit("asset_gen: в ответе xAI нет ни b64_json, ни доступного url")


# --- реестр ------------------------------------------------------------------

def write_ledger(row: dict) -> None:
    header = ("# BOMBAY MAIL — реестр сгенерированных референсов\n\n"
              "Пишется автоматически `tools/asset_gen.py`. Столбец «Размер» — в\n"
              "игровых единицах: без него контуры расставляют не в том масштабе.\n"
              "Референсы живут в `refs/` и в игру не попадают: в `data/` идут\n"
              "только контуры из `tools/trace_to_contours.py`.\n\n"
              "| Когда | Вид | Модель | Цена | Файл | Размер в игре | Описание |\n"
              "|---|---|---|---|---|---|---|\n")
    if not os.path.exists(LEDGER):
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write(header)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write("| %s | %s | %s | %d¢ | `%s` | %s | %s |\n"
                 % (row["when"], row["kind"], row["model"], row["cost"],
                    row["path"], row.get("size_note", "—"),
                    row["describe"].replace("|", "/")[:120]))


def main() -> int:
    ap = argparse.ArgumentParser(description="Референсы через Gemini и xAI Grok")
    ap.add_argument("--kind", required=True,
                    help="вид ассета из docs/asset_prompt_template.md §2")
    ap.add_argument("--describe", required=True, help="что именно нарисовать")
    ap.add_argument("-o", "--output", required=True, help="куда положить PNG")
    ap.add_argument("--model", choices=["gemini", "grok"], default="gemini",
                    help="gemini — точность и иконография; grok — дешевле, слушает хуже")
    ap.add_argument("--size", default="1K", help="512 / 1K / 2K / 4K (Gemini), 1K / 2K (Grok)")
    ap.add_argument("--aspect-ratio", default="1:1", choices=ASPECTS)
    ap.add_argument("--image", default=None,
                    help="референс для image-to-image: так делается семья стиля")
    ap.add_argument("--background", default="pale warm grey",
                    help="цвет сплошного фона; прозрачный не просить никогда")
    ap.add_argument("--size-note", default="", help="размер в игровых единицах, для реестра")
    ap.add_argument("--dry-run", action="store_true", help="показать промпт и цену, не тратя денег")
    ap.add_argument("--yes", action="store_true", help="подтвердить расход и генерировать")
    args = ap.parse_args()

    if args.model == "gemini":
        if args.size not in GEMINI_COST:
            raise SystemExit("asset_gen: для Gemini размер один из %s" % ", ".join(GEMINI_COST))
        cost = GEMINI_COST[args.size]
    else:
        if args.size not in GROK_SIZES:
            raise SystemExit("asset_gen: для Grok размер 1K или 2K")
        cost = GROK_COST

    prompt = build_prompt(args.kind, args.describe, args.background)

    if args.dry_run or not args.yes:
        print(json.dumps({
            "ok": True, "dry_run": True, "model": args.model, "size": args.size,
            "cost_cents": cost, "prompt_chars": len(prompt), "output": args.output,
            "prompt": prompt,
        }, ensure_ascii=False, indent=2))
        if not args.dry_run:
            sys.stderr.write("\nasset_gen: это платный вызов (%d¢). "
                             "Повторите с --yes, если согласны.\n" % cost)
            return 2
        return 0

    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sys.stderr.write("asset_gen: %s, %s, %d¢ → %s\n" % (args.model, args.size, cost, out))
    if args.model == "gemini":
        blob = gen_gemini(prompt, args.size, args.aspect_ratio, args.image)
    else:
        blob = gen_grok(prompt, args.aspect_ratio, args.image)
    with open(out, "wb") as fh:
        fh.write(blob)
    with open(out + ".prompt.txt", "w", encoding="utf-8") as fh:
        fh.write(prompt + "\n")
    write_ledger({"when": time.strftime("%Y-%m-%d %H:%M"), "kind": args.kind,
                  "model": args.model, "cost": cost,
                  "path": os.path.relpath(out, ROOT),
                  "size_note": args.size_note or "—", "describe": args.describe})
    print(json.dumps({"ok": True, "path": os.path.relpath(out, ROOT),
                      "cost_cents": cost}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
