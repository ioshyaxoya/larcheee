class_name CheckResult
extends RefCounted
## Результат одной видимой проверки d20 (или видимого броска шанса).
## Всё, что здесь лежит, показывается игроку: кубик, каждый модификатор, СЛ.

var kind: String = "check"          # "check" | "chance"
var label_key: String = ""
var die: int = 0
var die_second: int = 0            # второй кубик при преимуществе (показывается)
var advantage: bool = false
var modifiers: Array[Dictionary] = []   # {label_key, param, name_key, value}
var total: int = 0
var dc: int = 0
var success: bool = false
var natural_20: bool = false
var natural_1: bool = false
var skill_used: String = ""
var ability_used: String = ""
var probability: float = 0.0
var threshold: int = 0


func modifier_sum() -> int:
	var s := 0
	for m in modifiers:
		s += int(m["value"])
	return s


## Подпись модификатора: «Навык: Убеждение», «Харизма».
static func modifier_label(m: Dictionary, texts: Texts) -> String:
	var params := {}
	if String(m.get("param", "")) != "":
		params[m["param"]] = texts.t(String(m.get("name_key", "")))
	return texts.t(String(m["label_key"]), params)


func describe(texts: Texts) -> String:
	var parts: PackedStringArray = []
	parts.append(texts.t("ui.check.die") + " " + str(die))
	for m in modifiers:
		var v := int(m["value"])
		parts.append("%s %s%d" % [modifier_label(m, texts), "+" if v >= 0 else "", v])
	parts.append(texts.t("ui.check.total", {"total": total}))
	parts.append(texts.t("ui.check.dc", {"dc": dc}))
	parts.append(texts.t("ui.check.success" if success else "ui.check.fail"))
	return " · ".join(parts)
