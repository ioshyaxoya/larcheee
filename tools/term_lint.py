#!/usr/bin/env python3
"""
term_lint.py — терминологический линтер BOMBAY MAIL.

Культурная рамка (ТЗ A2.2) — это не проза в документе, а правило в CI.
Линтер ловит запрещённую лексику до того, как она попадёт в игру или в пресс-релиз.

Использование:
    python tools/term_lint.py .                 # весь проект
    python tools/term_lint.py data/cars/        # каталог
    python tools/term_lint.py --json .          # машинный вывод
Код возврата: 0 — чисто, 1 — есть нарушения.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

SCAN_SUFFIXES = {".md", ".json", ".gd", ".tscn", ".txt", ".csv", ".po", ".cfg"}
SKIP_DIRS = {".git", "node_modules", ".godot", "archive", "__pycache__", ".venv"}

# Задача линтера — не пустить запрещённую лексику в то, что увидит игрок или пресса:
# игровые строки, данные, код, маркетинг. Проектные документы правила обсуждают
# по необходимости (разделы о запретах, changelog, чеклисты) и по умолчанию не сканируются.
# Прогнать и по ним: --docs.
DOC_DIRS = {"docs"}

# Слово-маркер божественного контекста. Если строка содержит любой из них,
# к ней применяются правила GOD_CONTEXT.
DIVINE_MARKERS = [
    "шани", "муруган", "хануман", "кали", "ганеша", "яма", "читрагупт",
    "лакшми", "агни", "присутстви", "божеств", "вахана", "испытание бога",
    "god_", "deity", "divine",
]

# Всегда запрещено, в любом файле и любом контексте.
ALWAYS = [
    (r"пантеон", "«пантеон» запрещён (правило локальности A2.2). Пиши «присутствия»."),
    (r"бог[иа]?\s+Индии", "«боги Индии» запрещено. Пиши «присутствия» или «Кали Калигхата»."),
    (r"индуистск\w*\s+пантеон", "запрещено. Пиши «присутствия»."),
    (r"все\s+боги", "«все боги» запрещено: пантеон не конечен."),
    (r"собрать\s+богов", "запрещено: это не сбор пантеона, а эвакуация из промзоны."),
    (r"коллекци\w*\s+божеств", "запрещено."),
    (r"убива\w*\s+бог", "Шуньястра не убивает богов — она создаёт зону, куда богу не войти."),
    (r"уничтожа\w*\s+бог", "то же: оружие не уничтожает присутствия."),
    (r"смерть\s+бог", "смерть присутствия не показывается никогда."),
]

# Запрещено только в строках с божественным контекстом.
GOD_CONTEXT = [
    (r"\bбо[йея]\b|\bбою\b|\bбоем\b", "с присутствием — не «бой», а «испытание» / «состязание» / «суд»."),
    (r"\bбосс\b", "присутствие — не босс."),
    (r"\bубить\b|\bубийств", "присутствие нельзя убить."),
    (r"победить\s+бог", "не «победить», а «обыграть в его испытании»."),
    (r"\bсразись\b|\bсразиться\b", "маркетинговый хук «сразись с богами» запрещён."),
]

# Строки, где термин цитируется как запрещённый или формулируется правило, — не нарушение.
QUOTING_HINTS = [
    "запрещ", "нельзя", "не говорит", "не пиши", "forbidden", "term_lint", "вместо",
    "не показывается", "бессмертн", "не убива", "не уничтожа", "правило", "пиши «",
]

# Явная пометка для строк, где термин нужен по делу: добавь `lint-ok` в комментарий.
SUPPRESS = "lint-ok"


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    text: str
    message: str


def is_quoting(line: str) -> bool:
    low = line.lower()
    return any(h in low for h in QUOTING_HINTS)


def has_divine_context(line: str) -> bool:
    low = line.lower()
    return any(m in low for m in DIVINE_MARKERS)


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings

    for n, line in enumerate(lines, 1):
        if SUPPRESS in line or is_quoting(line):
            continue
        low = line.lower()
        for pattern, message in ALWAYS:
            if re.search(pattern, low):
                findings.append(Finding(str(path), n, pattern, line.strip()[:120], message))
        if has_divine_context(line):
            for pattern, message in GOD_CONTEXT:
                if re.search(pattern, low):
                    findings.append(Finding(str(path), n, pattern, line.strip()[:120], message))
    return findings


def walk(root: Path, include_docs: bool) -> list[Path]:
    if root.is_file():
        return [root]
    out = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if not include_docs and any(part in DOC_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in SCAN_SUFFIXES:
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Терминологический линтер BOMBAY MAIL")
    ap.add_argument("path", nargs="?", default=".", help="файл или каталог")
    ap.add_argument("--json", action="store_true", help="машинный вывод")
    ap.add_argument("--docs", action="store_true",
                    help="сканировать и docs/ (там правила обсуждаются, будут ложные срабатывания)")
    args = ap.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"нет такого пути: {root}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    files = walk(root, args.docs)
    for f in files:
        findings.extend(scan_file(f))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        if not findings:
            print(f"term_lint: чисто ({len(files)} файлов проверено)")
        else:
            for f in findings:
                print(f"{f.path}:{f.line}: {f.message}")
                print(f"    {f.text}")
            print(f"\nterm_lint: {len(findings)} нарушений в {len(files)} файлах")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
