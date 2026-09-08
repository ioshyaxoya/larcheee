#!/usr/bin/env python3
"""dialogue_validator.py — валидатор графов диалогов, NPC и квестов BOMBAY MAIL.

Дополняет car_validator.py (карточка вагона, чеклист B7): проверяет рантайм-данные,
которые читает движок, — `data/dialogues/*.json`, `data/npcs/*.json`, `data/encounters/*.json`,
`data/prologue/quest_*.json`. Формат — docs/data_format.md.

Падает на:
    * незарегистрированном флаге или теге (`data/flags.json`, B5);
    * значении не по типу флага (bool / int / string / enum);
    * ссылке на несуществующий узел, NPC, происхождение, навык, палитру;
    * проверке без DC (скрытых бросков нет, B5) или без ветки провала;
    * оси отношения не из `data/attitude_axes.json`;
    * уникальной реплике (`pearl`) не из `data/pearls.json`;
    * сырой строке там, где должен быть ключ текста; ключе без русского текста.

Использование:
    python tools/dialogue_validator.py            # data/dialogues data/npcs data/prologue
    python tools/dialogue_validator.py data/prologue/quest_last_half_hour.json
Коды выхода: 0 — без ошибок, 1 — есть ошибки, 2 — ошибка запуска.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
DEFAULT_PATHS = [os.path.join(DATA_DIR, "dialogues"), os.path.join(DATA_DIR, "npcs"), os.path.join(DATA_DIR, "encounters"), os.path.join(DATA_DIR, "prologue")]
TRIGGER_EVENTS = {"car_entered", "car_left", "npc_approached", "item_taken", "dialogue_ended", "trial_lost_round", "trial_won", "trial_soft_reset", "flag_changed"}

TEXT_KEY_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SPEAKER_SPECIAL = {"narrator", "player"}
NODE_KEYS = {"speaker", "text_key", "stage", "on_enter", "options", "next", "end", "pearl", "pearl_id", "branches"}
OPTION_KEYS = {
    "id", "text_key", "conditions", "check", "chance", "cost_minutes", "cost_on_fail_minutes", "cost_note_key",
    "effects", "effects_on_fail", "next", "next_on_fail", "pearl", "pearl_id",
}
CHANCE_PROVIDERS = {"bridge_raised", "coin"}
TAG_PREFIX = "prologue."


@dataclass
class Registry:
    flags: dict            # имя → {"type": ..., "values": [...]} (плоский словарь базы приводится к этому виду)
    axes: dict
    abilities: set
    skills: dict
    origins: set
    classes: set
    pearls: set
    npc_ids: set
    dialogue_ids: set
    texts_ru: set
    texts_en: set


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_flags() -> dict:
    """data/flags.json: имя → описание (строка) или имя → {description, type, values}."""
    raw = _load_json(os.path.join(DATA_DIR, "flags.json"))
    flags = {}
    for name, spec in raw.items():
        if name.startswith("_"):
            continue
        if isinstance(spec, dict):
            flags[name] = {"type": spec.get("type", "any"), "values": spec.get("values", [])}
        else:
            flags[name] = {"type": "any", "values": []}
    return flags


def load_registry() -> Registry:
    axes = _load_json(os.path.join(DATA_DIR, "attitude_axes.json"))["axes"]
    abilities = set(_load_json(os.path.join(DATA_DIR, "character", "abilities.json"))["abilities"].keys())
    skills = {k: v["ability"] for k, v in _load_json(os.path.join(DATA_DIR, "character", "skills.json"))["skills"].items()}
    origins = set(_load_json(os.path.join(DATA_DIR, "character", "origins.json"))["origins"].keys())
    classes = set(_load_json(os.path.join(DATA_DIR, "character", "classes.json"))["classes"].keys())
    pearls = {p["id"] for p in _load_json(os.path.join(DATA_DIR, "pearls.json"))["pearls"]}
    npc_dir = os.path.join(DATA_DIR, "npcs")
    npc_ids = {n[:-5] for n in os.listdir(npc_dir) if n.endswith(".json")} if os.path.isdir(npc_dir) else set()
    dlg_dir = os.path.join(DATA_DIR, "dialogues")
    dialogue_ids = {n[:-5] for n in os.listdir(dlg_dir) if n.endswith(".json")} if os.path.isdir(dlg_dir) else set()
    texts_ru = set(_load_json(os.path.join(DATA_DIR, "texts", "ru.json")).keys())
    en_path = os.path.join(DATA_DIR, "texts", "en.json")
    texts_en = set(_load_json(en_path).keys()) if os.path.exists(en_path) else set()
    return Registry(load_flags(), axes, abilities, skills, origins, classes, pearls, npc_ids, dialogue_ids, texts_ru, texts_en)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []


class Checker:
    def __init__(self, path: str, reg: Registry, rep: Report) -> None:
        self.path = os.path.relpath(path, REPO_ROOT)
        self.reg = reg
        self.rep = rep
        self.local_speakers: set[str] = set()

    def err(self, where: str, msg: str) -> None:
        self.rep.errors.append(f"{self.path} › {where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.rep.warnings.append(f"{self.path} › {where}: {msg}")

    # -- атомы --------------------------------------------------------------
    def text_key(self, where: str, k, required: bool = True) -> None:
        if k is None:
            if required:
                self.err(where, "нет текстового ключа")
            return
        if not isinstance(k, str) or not TEXT_KEY_RE.match(k):
            self.err(where, f"«{k}» — не ключ текста (вид a.b.c); строки в данных запрещены (B5)")
            return
        if k not in self.reg.texts_ru:
            self.err(where, f"ключ `{k}` не найден в data/texts/ru.json")
        elif k not in self.reg.texts_en:
            self.warn(where, f"ключ `{k}` не переведён в data/texts/en.json")

    def flag(self, where: str, name, value=None, check_value: bool = False) -> None:
        if not isinstance(name, str) or name not in self.reg.flags:
            self.err(where, f"флаг `{name}` не зарегистрирован в data/flags.json (B5)")
            return
        if not check_value:
            return
        spec = self.reg.flags[name]
        t = spec["type"]
        ok = {
            "bool": isinstance(value, bool),
            "int": isinstance(value, int) and not isinstance(value, bool),
            "string": isinstance(value, str),
            "enum": value in spec["values"],
            "any": True,
        }.get(t, False)
        if not ok:
            self.err(where, f"флаг `{name}` типа {t}: недопустимое значение {value!r}")

    def tag(self, where: str, name) -> None:
        if not isinstance(name, str):
            self.err(where, "тег должен быть строкой")
            return
        self.flag(where, TAG_PREFIX + name)

    # -- условия и эффекты ---------------------------------------------------
    def conditions(self, where: str, conds) -> None:
        if conds is None:
            return
        if not isinstance(conds, list):
            self.err(where, "conditions должен быть списком")
            return
        for i, c in enumerate(conds):
            self.condition(f"{where}[{i}]", c)

    def condition(self, where: str, c) -> None:
        if not isinstance(c, dict):
            self.err(where, "условие должно быть объектом")
            return
        if "not" in c:
            return self.condition(where + ".not", c["not"])
        if "any" in c or "all" in c:
            return self.conditions(where + (".any" if "any" in c else ".all"), c.get("any", c.get("all")))
        if "flag" in c:
            self.flag(where, c["flag"], c.get("equals"), check_value="equals" in c)
            for v in c.get("in", []):
                self.flag(where, c["flag"], v, check_value=True)
            return
        if "tag" in c:
            return self.tag(where, c["tag"])
        if "origin" in c:
            if c["origin"] not in self.reg.origins:
                self.err(where, f"неизвестное происхождение `{c['origin']}`")
            return
        if "origin_in" in c:
            for o in c["origin_in"]:
                if o not in self.reg.origins:
                    self.err(where, f"неизвестное происхождение `{o}`")
            return
        if "class" in c:
            if c["class"] not in self.reg.classes:
                self.err(where, f"неизвестный класс `{c['class']}`")
            return
        if "sex" in c:
            if c["sex"] not in ("m", "f"):
                self.err(where, "sex: 'm' или 'f'")
            return
        if "axis" in c:
            axis = c["axis"]
            if axis not in self.reg.axes:
                self.err(where, f"ось `{axis}` не зарегистрирована в data/attitude_axes.json")
            elif c.get("pole") not in self.reg.axes[axis]["poles"]:
                self.err(where, f"полюс `{c.get('pole')}` не принадлежит оси `{axis}`")
            return
        if "money_min" in c or "minutes_spent_min" in c:
            return
        self.err(where, f"неизвестное условие {sorted(c.keys())}")

    def effects(self, where: str, effs, nodes: dict | None = None) -> None:
        if effs is None:
            return
        if not isinstance(effs, list):
            self.err(where, "effects должен быть списком")
            return
        for i, e in enumerate(effs):
            self.effect(f"{where}[{i}]", e, nodes)

    def effect(self, where: str, e, nodes: dict | None) -> None:
        if not isinstance(e, dict):
            self.err(where, "эффект должен быть объектом")
            return
        if "set_flag" in e:
            if "value" not in e:
                self.err(where, "set_flag без value")
            self.flag(where, e["set_flag"], e.get("value"), check_value=True)
        elif "add_tag" in e:
            self.tag(where, e["add_tag"])
        elif "add_minutes" in e:
            if not isinstance(e["add_minutes"], int) or e["add_minutes"] < 0:
                self.err(where, "add_minutes — неотрицательное целое")
            self.text_key(where + ".reason_key", e.get("reason_key"))
        elif "add_money" in e:
            if not isinstance(e["add_money"], int):
                self.err(where, "add_money — целое (анны)")
        elif "goto" in e:
            if nodes is not None and e["goto"] not in nodes:
                self.err(where, f"goto на несуществующий узел `{e['goto']}`")
        elif "end" in e:
            pass
        elif "emit" in e:
            if not isinstance(e["emit"], str) or not ID_RE.match(e["emit"]):
                self.err(where, "emit — идентификатор сигнала")
        elif "record_minutes_flag" in e:
            self.flag(where, e["record_minutes_flag"])
            if self.reg.flags.get(e["record_minutes_flag"], {}).get("type") not in ("int", "any"):
                self.err(where, "record_minutes_flag требует флаг типа int")
        else:
            self.err(where, f"неизвестный эффект {sorted(e.keys())}")

    # -- проверки --------------------------------------------------------------
    def check(self, where: str, chk) -> None:
        if not isinstance(chk, dict):
            self.err(where, "check должен быть объектом")
            return
        if not isinstance(chk.get("dc"), int):
            self.err(where, "проверка без целого DC — скрытых бросков нет, DC показывается игроку (B5)")
        ability, skill = chk.get("ability"), chk.get("skill")
        if "skills_any" in chk:
            if skill is not None or ability is not None:
                self.err(where, "skills_any не сочетается с skill/ability")
            if not isinstance(chk["skills_any"], list) or not chk["skills_any"]:
                self.err(where, "skills_any — непустой список навыков")
            else:
                for s in chk["skills_any"]:
                    if s not in self.reg.skills:
                        self.err(where, f"неизвестный навык `{s}`")
        elif skill is not None:
            if skill not in self.reg.skills:
                self.err(where, f"неизвестный навык `{skill}`")
            elif ability is not None and self.reg.skills[skill] != ability:
                self.err(where, f"навык `{skill}` привязан к `{self.reg.skills[skill]}`, не к `{ability}`")
        elif ability not in self.reg.abilities:
            self.err(where, f"неизвестная характеристика `{ability}`")
        self.text_key(where + ".label_key", chk.get("label_key"), required=False)

    def chance(self, where: str, ch, nodes: dict) -> None:
        if not isinstance(ch, dict):
            self.err(where, "chance должен быть объектом")
            return
        if ch.get("provider") not in CHANCE_PROVIDERS:
            self.err(where, f"неизвестный provider `{ch.get('provider')}` ({sorted(CHANCE_PROVIDERS)})")
        self.text_key(where + ".label_key", ch.get("label_key"))
        for k in ("on_hit", "on_miss"):
            if ch.get(k) not in nodes:
                self.err(where, f"{k} → несуществующий узел `{ch.get(k)}`")
        if "hit_minutes" in ch and (not isinstance(ch["hit_minutes"], int) or ch["hit_minutes"] < 0):
            self.err(where, "hit_minutes — неотрицательное целое")

    # -- граф -------------------------------------------------------------------
    def dialogue(self, where: str, dlg: dict) -> None:
        if not isinstance(dlg, dict) or "nodes" not in dlg or "start" not in dlg:
            self.err(where, "диалог должен содержать start и nodes")
            return
        nodes = dlg["nodes"]
        if dlg["start"] not in nodes:
            self.err(where, f"start `{dlg['start']}` не найден")
        reachable = self._reachable(dlg["start"], nodes)
        for nid, node in nodes.items():
            self.node(f"{where}.{nid}", nid, node, nodes)
            if nid not in reachable:
                self.warn(f"{where}.{nid}", "узел недостижим из start")

    @staticmethod
    def _reachable(start: str, nodes: dict) -> set:
        seen, stack = set(), [start]
        while stack:
            nid = stack.pop()
            if nid in seen or nid not in nodes:
                continue
            seen.add(nid)
            node = nodes[nid]
            nxt = []
            if "next" in node:
                nxt.append(node["next"])
            for br in node.get("branches", []):
                nxt.append(br.get("next"))
            for opt in node.get("options", []):
                nxt += [opt.get("next"), opt.get("next_on_fail")]
                ch = opt.get("chance") or {}
                nxt += [ch.get("on_hit"), ch.get("on_miss")]
                for e in opt.get("effects", []) + opt.get("effects_on_fail", []):
                    nxt.append(e.get("goto"))
            for e in node.get("on_enter", []):
                nxt.append(e.get("goto"))
            stack.extend(n for n in nxt if n)
        return seen

    def node(self, where: str, nid: str, node, nodes: dict) -> None:
        if not ID_RE.match(nid):
            self.err(where, "id узла — идентификатор")
        if not isinstance(node, dict):
            self.err(where, "узел должен быть объектом")
            return
        for k in node:
            if k not in NODE_KEYS:
                self.err(where, f"неизвестное поле узла `{k}`")
        is_branch = "branches" in node
        speaker = node.get("speaker", "narrator")
        if not is_branch and speaker not in SPEAKER_SPECIAL and speaker not in self.local_speakers and speaker not in self.reg.npc_ids:
            self.err(where, f"speaker `{speaker}` — не NPC (data/npcs или npcs документа) и не narrator/player")
        self.text_key(where + ".text_key", node.get("text_key"), required=not is_branch)
        self.text_key(where + ".stage", node.get("stage"), required=False)
        self.effects(where + ".on_enter", node.get("on_enter"), nodes)
        if node.get("pearl") and node.get("pearl_id") not in self.reg.pearls:
            self.err(where, f"уникальная реплика `{node.get('pearl_id')}` не зарегистрирована в data/pearls.json (B5)")
        if is_branch:
            brs = node["branches"]
            if not brs or brs[-1].get("conditions"):
                self.warn(where, "у ветвления нет безусловной последней ветки")
            for i, br in enumerate(brs):
                self.conditions(f"{where}.branches[{i}].conditions", br.get("conditions"))
                if br.get("next") not in nodes:
                    self.err(f"{where}.branches[{i}]", f"next `{br.get('next')}` не найден")
            return
        options = node.get("options", [])
        if not options and not node.get("end") and "next" not in node:
            self.err(where, "узел без options/next/end — тупик")
        if "next" in node and node["next"] not in nodes:
            self.err(where, f"next `{node['next']}` не найден")
        for i, opt in enumerate(options):
            self.option(f"{where}.options[{i}]", opt, nodes)

    def option(self, where: str, opt, nodes: dict) -> None:
        if not isinstance(opt, dict):
            self.err(where, "вариант должен быть объектом")
            return
        for k in opt:
            if k not in OPTION_KEYS:
                self.err(where, f"неизвестное поле варианта `{k}`")
        self.text_key(where + ".text_key", opt.get("text_key"))
        self.text_key(where + ".cost_note_key", opt.get("cost_note_key"), required=False)
        self.conditions(where + ".conditions", opt.get("conditions"))
        self.effects(where + ".effects", opt.get("effects"), nodes)
        self.effects(where + ".effects_on_fail", opt.get("effects_on_fail"), nodes)
        for k in ("cost_minutes", "cost_on_fail_minutes"):
            if k in opt and (not isinstance(opt[k], int) or opt[k] < 0):
                self.err(where, f"{k} — неотрицательное целое")
        if "check" in opt:
            self.check(where + ".check", opt["check"])
            if "next_on_fail" not in opt and not any("goto" in e for e in opt.get("effects_on_fail", [])):
                self.err(where, "у проверки нет next_on_fail — провал не прячется, ему нужна ветка (B5)")
        elif any(k in opt for k in ("next_on_fail", "effects_on_fail", "cost_on_fail_minutes")):
            self.err(where, "поля *_on_fail без check")
        if "chance" in opt:
            self.chance(where + ".chance", opt["chance"], nodes)
        for k in ("next", "next_on_fail"):
            if k in opt and opt[k] not in nodes:
                self.err(where, f"{k} `{opt[k]}` не найден")
        if not ("next" in opt or "chance" in opt or any(("goto" in e or "end" in e) for e in opt.get("effects", []))):
            self.err(where, "вариант без next/chance/goto/end — тупик")
        if opt.get("pearl") and opt.get("pearl_id") not in self.reg.pearls:
            self.err(where, f"уникальная реплика `{opt.get('pearl_id')}` не зарегистрирована в data/pearls.json")

    # -- документы --------------------------------------------------------------
    def npc(self, doc: dict) -> None:
        base = os.path.splitext(os.path.basename(self.path))[0]
        if doc.get("id") != base:
            self.err("id", f"`{doc.get('id')}` должен совпадать с именем файла")
        self.text_key("name_key", doc.get("name_key"))
        self.conditions("conditions", doc.get("conditions"))
        if "dialogue" in doc and doc["dialogue"] not in self.reg.dialogue_ids:
            self.err("dialogue", f"диалог `{doc['dialogue']}` не найден в data/dialogues/")
        pos = doc.get("position")
        if pos is not None and (not isinstance(pos, list) or len(pos) != 3):
            self.err("position", "[x, y, z]")
        axes = doc.get("attitude_axes", {})
        if not isinstance(axes, dict):
            self.err("attitude_axes", "объект ось → {полюс: text_key}")
            return
        for axis, reaction in axes.items():
            if axis not in self.reg.axes:
                self.err("attitude_axes", f"ось `{axis}` не зарегистрирована (B4)")
                continue
            if not isinstance(reaction, dict):
                self.err(f"attitude_axes.{axis}", "объект полюс → text_key")
                continue
            for pole, k in reaction.items():
                if pole not in self.reg.axes[axis]["poles"]:
                    self.err(f"attitude_axes.{axis}", f"полюс `{pole}` не принадлежит оси")
                self.text_key(f"attitude_axes.{axis}.{pole}", k)

    def encounter_doc(self, doc: dict) -> None:
        base = os.path.splitext(os.path.basename(self.path))[0]
        if doc.get("id") != base:
            self.err("id", f"`{doc.get('id')}` должен совпадать с именем файла")
        if doc.get("event") not in TRIGGER_EVENTS:
            self.err("event", f"неизвестное событие `{doc.get('event')}` ({sorted(TRIGGER_EVENTS)})")
        if "npc" in doc and doc["npc"] not in self.reg.npc_ids:
            self.err("npc", f"NPC `{doc['npc']}` не найден в data/npcs/")
        self.conditions("conditions", doc.get("conditions"))
        self.effects("effects", doc.get("effects"))
        if "dialogue" in doc and doc["dialogue"] is not None and doc["dialogue"] not in self.reg.dialogue_ids:
            self.err("dialogue", f"диалог `{doc['dialogue']}` не найден в data/dialogues/")

    def dialogue_doc(self, doc: dict) -> None:
        base = os.path.splitext(os.path.basename(self.path))[0]
        if doc.get("id") != base:
            self.err("id", f"`{doc.get('id')}` должен совпадать с именем файла")
        self.dialogue("nodes", doc)

    def quest_doc(self, doc: dict) -> None:
        base = os.path.splitext(os.path.basename(self.path))[0]
        for k in ("id", "title_key", "target_hours", "entry", "dialogues"):
            if k not in doc:
                self.err("root", f"нет обязательного поля `{k}`")
        if doc.get("id") != base:
            self.err("id", f"`{doc.get('id')}` должен совпадать с именем файла")
        self.text_key("title_key", doc.get("title_key"))
        for n in doc.get("npcs", []):
            nid = n.get("id")
            if not isinstance(nid, str) or not ID_RE.match(nid):
                self.err("npcs", f"некорректный id `{nid}`")
                continue
            self.local_speakers.add(nid)
            self.text_key(f"npcs.{nid}.name_key", n.get("name_key"))
        clock = doc.get("clock")
        if clock is not None:
            for k in ("start_minutes", "deadline_minutes"):
                if not isinstance(clock.get(k), int):
                    self.err("clock", f"{k} — целое (минуты от полуночи)")
            self.text_key("clock.deadline_label_key", clock.get("deadline_label_key"), required=False)
        for f in doc.get("output_flags", []):
            self.flag("output_flags", f)
        if doc.get("entry") not in doc.get("dialogues", {}):
            self.err("entry", f"диалог `{doc.get('entry')}` не найден")
        for did, dlg in doc.get("dialogues", {}).items():
            self.dialogue(f"dialogues.{did}", dlg)


def classify(path: str, doc: dict) -> str:
    parts = os.path.normpath(path).split(os.sep)
    if doc.get("kind") == "quest" or "prologue" in parts and os.path.basename(path).startswith("quest_"):
        return "quest"
    if "npcs" in parts:
        return "npc"
    if "dialogues" in parts:
        return "dialogue"
    if "encounters" in parts:
        return "encounter"
    return "skip"


def collect(paths: list[str]) -> list[str]:
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += [os.path.join(p, n) for n in sorted(os.listdir(p)) if n.endswith(".json")]
        elif p.endswith(".json"):
            files.append(p)
    return files


def main(argv: list[str]) -> int:
    paths = argv[1:] or DEFAULT_PATHS
    for p in paths:
        if not os.path.exists(p):
            print(f"dialogue_validator: путь не найден: {p}", file=sys.stderr)
            return 2
    try:
        reg = load_registry()
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"dialogue_validator: не удалось загрузить реестры data/: {exc}", file=sys.stderr)
        return 2
    rep = Report()
    files = collect(paths)
    checked = 0
    for path in files:
        try:
            doc = _load_json(path)
        except json.JSONDecodeError as exc:
            rep.errors.append(f"{os.path.relpath(path, REPO_ROOT)}: невалидный JSON — {exc}")
            continue
        kind = classify(path, doc)
        if kind == "skip":
            continue
        checked += 1
        c = Checker(path, reg, rep)
        {"quest": c.quest_doc, "npc": c.npc, "dialogue": c.dialogue_doc, "encounter": c.encounter_doc}[kind](doc)
    for w in rep.warnings:
        print(f"  предупреждение: {w}")
    for e in rep.errors:
        print(f"  ОШИБКА: {e}")
    print(f"\ndialogue_validator: {checked} документов, {len(rep.errors)} ошибок, {len(rep.warnings)} предупреждений")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
