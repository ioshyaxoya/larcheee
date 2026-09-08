#!/usr/bin/env python3
"""
hours_estimator.py — оценка длительности вагона по его содержимому.

Считает часы из графа контента и сравнивает с заявленным target_hours.
Допуск ±20% (ТЗ B7). Нужен, чтобы бюджет A4 не разъехался к тридцатому вагону.

Использование:
    python tools/hours_estimator.py data/cars/
Код возврата: 0 — все в допуске, 1 — есть расхождения.
"""

import argparse
import json
import sys
from pathlib import Path

# Стоимость единицы контента в часах. Калибруется на плейтестах M1.
COST = {
    "dialogue_node": 0.010,
    "npc": 0.035,
    "encounter": 0.220,
    "minigame": 0.180,
    "settlement_quest": 0.400,
    "exclusive_fact": 0.080,
    "environment_object": 0.020,
    "seed_item": 0.015,
    "performance": 0.350,
    "path": 0.150,
}

TOLERANCE = 0.20


def count(car: dict, key: str) -> int:
    v = car.get(key)
    if isinstance(v, list):
        return len(v)
    if isinstance(v, dict):
        return len(v)
    if isinstance(v, int):
        return v
    return 0


def estimate(car: dict) -> float:
    h = 0.0
    h += count(car, "dialogue_nodes") * COST["dialogue_node"]
    h += count(car, "npcs") * COST["npc"]
    h += count(car, "encounters") * COST["encounter"]
    h += count(car, "minigames") * COST["minigame"]
    h += count(car, "settlement_quests") * COST["settlement_quest"]
    h += count(car, "exclusive_facts") * COST["exclusive_fact"]
    h += count(car, "environment_objects") * COST["environment_object"]
    h += count(car, "seed_items") * COST["seed_item"]
    h += count(car, "paths") * COST["path"]
    if car.get("musical_number"):
        h += COST["performance"]
    return round(h, 2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Оценка длительности вагонов")
    ap.add_argument("path", nargs="?", default="data/cars/")
    args = ap.parse_args()

    root = Path(args.path)
    files = [root] if root.is_file() else sorted(root.glob("*.json")) if root.exists() else []
    if not files:
        print(f"вагонов не найдено в {root}", file=sys.stderr)
        return 2

    total_declared = total_estimated = 0.0
    off = []

    print(f"{'вагон':<14}{'заявлено':>10}{'оценка':>10}{'откл.':>9}")
    print("-" * 43)

    for f in files:
        try:
            car = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"{f.name:<14}  невалидный JSON")
            continue
        declared = float(car.get("target_hours") or 0)
        est = estimate(car)
        total_declared += declared
        total_estimated += est
        if declared:
            dev = (est - declared) / declared
            mark = "" if abs(dev) <= TOLERANCE else "  <-- вне допуска"
            if abs(dev) > TOLERANCE:
                off.append((car.get("id", f.name), declared, est, dev))
            print(f"{car.get('id', f.name):<14}{declared:>10.2f}{est:>10.2f}{dev:>8.0%}{mark}")
        else:
            print(f"{car.get('id', f.name):<14}{'—':>10}{est:>10.2f}")

    print("-" * 43)
    print(f"{'ИТОГО':<14}{total_declared:>10.2f}{total_estimated:>10.2f}")
    print(f"\nБюджет игры (A4): среднее прохождение ~130 ч — потолок, не догма.")

    if off:
        print(f"\nВне допуска ±20%: {len(off)}")
        for cid, d, e, dev in off:
            print(f"  {cid}: заявлено {d}, оценка {e} ({dev:+.0%})")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
