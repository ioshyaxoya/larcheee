#!/usr/bin/env python3
"""
car_validator.py — валидатор вагонов BOMBAY MAIL.

Проверяет data/cars/*.json против схемы (ТЗ B4) и чеклиста готовности (ТЗ B7).
Камерные вагоны проходят облегчённый чеклист (A8/A19).

Использование:
    python tools/car_validator.py data/cars/
    python tools/car_validator.py data/cars/car_01.json --strict
Код возврата: 0 — годно, 1 — ошибки.
"""

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ["id", "title", "chapter", "target_hours", "palette", "settlement",
            "grid", "paths", "state_schema", "window_progress_delta"]

PALETTES = {"bollywood", "bollywood_dark", "human", "raj", "void"}
SETTLEMENTS = {"full", "brief", "none"}
PATHS = {"force", "deceit", "service", "stay"}
GOD_KEYS = ["trial", "vahana", "gift", "lie_about_exit", "performance"]

FLAGS_FILE = Path("data/flags.json")


def load_flags() -> set:
    if FLAGS_FILE.exists():
        try:
            return set(json.loads(FLAGS_FILE.read_text(encoding="utf-8")).keys())
        except (json.JSONDecodeError, AttributeError):
            return set()
    return set()


def validate(car: dict, known_flags: set, strict: bool) -> tuple[list, list]:
    errors, warnings = [], []
    cid = car.get("id", "<без id>")

    for key in REQUIRED:
        if key not in car:
            errors.append(f"{cid}: нет обязательного поля '{key}'")

    if car.get("palette") not in PALETTES:
        errors.append(f"{cid}: palette '{car.get('palette')}' не из {sorted(PALETTES)}")

    settlement = car.get("settlement")
    if settlement not in SETTLEMENTS:
        errors.append(f"{cid}: settlement '{settlement}' не из {sorted(SETTLEMENTS)}")

    is_god = bool(car.get("is_god"))
    is_chamber = car.get("kind") == "chamber"

    # Пути
    paths = car.get("paths", {})
    if not is_chamber:
        missing = PATHS - set(paths)
        if missing:
            errors.append(f"{cid}: не хватает путей {sorted(missing)} (полный вагон обязан иметь четыре)")
    else:
        if "stay" not in paths:
            warnings.append(f"{cid}: у камерного вагона нет пути 'stay'")

    # Прогресс окна
    wpd = car.get("window_progress_delta", {})
    for p in paths:
        if p not in wpd:
            errors.append(f"{cid}: window_progress_delta не задан для пути '{p}'")
    if "stay" in wpd and isinstance(wpd["stay"], (int, float)) and wpd["stay"] >= 0:
        if cid != "car_01":  # исключение: концовка 5
            errors.append(f"{cid}: window_progress_delta.stay должен быть отрицательным (A19)")

    # Уровни
    levels = car.get("grid", {}).get("levels", [])
    if not is_chamber and len(levels) < 2:
        errors.append(f"{cid}: нужно минимум 2 уровня вертикальности (A14), задано {len(levels)}")

    # Хвостовая вариация
    if not car.get("tail_variant"):
        errors.append(f"{cid}: нет tail_variant — вагон обязан жить в хвосте (A8)")

    # Реакция на тряску
    if not car.get("tremor_reaction"):
        errors.append(f"{cid}: нет tremor_reaction — у каждого мира своя теология тряски (A8)")

    # Оседлость
    if settlement == "full":
        need = ["settlement_role", "settlement_income", "settlement_quests", "exclusive_fact"]
        for k in need:
            if not car.get(k):
                errors.append(f"{cid}: settlement=full требует поля '{k}' (A19)")
        q = car.get("settlement_quests") or []
        if isinstance(q, list) and not (2 <= len(q) <= 4):
            warnings.append(f"{cid}: у полной оседлости ожидается 2–4 бытовых квеста, задано {len(q)}")

    # Присутствия
    if is_god:
        god = car.get("god_data", {})
        for k in GOD_KEYS:
            if k not in god:
                errors.append(f"{cid}: божественный вагон требует god_data.{k} (A9)")
        if god.get("unkillable") is not True:
            errors.append(f"{cid}: god_data.unkillable должен быть true (A2.2)")
        if settlement != "none":
            errors.append(f"{cid}: у божественного вагона settlement должен быть 'none' (A19)")

    # Среда в столкновении
    if not is_chamber and not car.get("environment_objects"):
        warnings.append(f"{cid}: нет environment_objects — нужен минимум один объект среды (B7)")

    # Межвагонные связи
    if not is_chamber:
        if not car.get("reacts_to_prologue_tag") and cid != "car_01":
            warnings.append(f"{cid}: нет реакции на флаг пролога (B7)")
        if not car.get("reacts_to_car") and cid != "car_01":
            warnings.append(f"{cid}: нет реакции на состояние другого вагона (B7)")

    # Флаги
    for flag in car.get("sets_flags", []):
        if known_flags and flag not in known_flags:
            errors.append(f"{cid}: флаг '{flag}' не зарегистрирован в data/flags.json (B5)")

    # Часы
    th = car.get("target_hours")
    if isinstance(th, (int, float)):
        if is_chamber and th > 2.5:
            warnings.append(f"{cid}: камерный вагон на {th} ч — многовато (ожидается 1.5–2)")
        if not is_chamber and th < 2:
            warnings.append(f"{cid}: полный мир на {th} ч — маловато")

    if strict:
        errors.extend(warnings)
        warnings = []
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Валидатор вагонов BOMBAY MAIL")
    ap.add_argument("path", nargs="?", default="data/cars/")
    ap.add_argument("--strict", action="store_true", help="предупреждения считать ошибками")
    args = ap.parse_args()

    root = Path(args.path)
    files = [root] if root.is_file() else sorted(root.glob("*.json")) if root.exists() else []
    if not files:
        print(f"вагонов не найдено в {root}", file=sys.stderr)
        return 2

    known_flags = load_flags()
    all_errors, all_warnings = [], []

    for f in files:
        try:
            car = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            all_errors.append(f"{f.name}: невалидный JSON — {e}")
            continue
        e, w = validate(car, known_flags, args.strict)
        all_errors.extend(e)
        all_warnings.extend(w)

    for w in all_warnings:
        print(f"  предупреждение: {w}")
    for e in all_errors:
        print(f"  ОШИБКА: {e}")

    print(f"\ncar_validator: {len(files)} вагонов, {len(all_errors)} ошибок, {len(all_warnings)} предупреждений")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
