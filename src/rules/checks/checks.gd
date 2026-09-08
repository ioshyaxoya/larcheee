class_name Checks
extends RefCounted
## Все проверки d20 идут отсюда (B5). Скрытых бросков нет: каждый бросок
## уходит сигналом check_rolled с полным разбором, и UI обязан его показать.

signal check_rolled(result: CheckResult)

var rng: SeededRng
var data: CharacterData
var history: Array[CheckResult] = []


func _init(seeded_rng: SeededRng, char_data: CharacterData) -> void:
	rng = seeded_rng
	data = char_data


## spec: {"skill": ..} | {"skills_any": [..]} | {"ability": ..}, "dc", "label_key".
func roll(character: Character, spec: Dictionary) -> CheckResult:
	var r := CheckResult.new()
	r.kind = "check"
	r.label_key = str(spec.get("label_key", ""))
	r.dc = int(spec.get("dc", 10))
	var skill := ""
	if spec.has("skills_any"):
		var best := -99
		for s in spec["skills_any"]:
			var m := character.skill_modifier(String(s), data)
			if m > best:
				best = m
				skill = String(s)
	elif spec.has("skill"):
		skill = str(spec["skill"])
	var ability: String = str(spec.get("ability", "")) if skill == "" else data.skill_ability(skill)
	r.skill_used = skill
	r.ability_used = ability
	r.die = rng.d20()
	r.natural_20 = r.die == 20
	r.natural_1 = r.die == 1
	if ability != "":
		r.modifiers.append({"label_key": "ui.check.mod.ability", "param": "ability", "name_key": "ability." + ability, "value": character.modifier(ability)})
	if skill != "" and character.is_proficient(skill):
		r.modifiers.append({"label_key": "ui.check.mod.proficiency", "param": "skill", "name_key": "skill." + skill, "value": character.proficiency_bonus()})
	r.total = r.die + r.modifier_sum()
	r.success = r.total >= r.dc
	history.append(r)
	check_rolled.emit(r)
	return r


## Видимый бросок шанса: d20 против порога round(p × 20). Успех = событие случилось.
func roll_chance(label_key: String, probability: float) -> CheckResult:
	var r := CheckResult.new()
	r.kind = "chance"
	r.label_key = label_key
	r.probability = clampf(probability, 0.0, 1.0)
	r.threshold = int(round(r.probability * 20.0))
	r.dc = r.threshold
	r.die = rng.d20()
	r.total = r.die
	r.success = r.die <= r.threshold
	r.modifiers.append({"label_key": "ui.check.mod.chance", "param": "", "name_key": "", "value": 0})
	history.append(r)
	check_rolled.emit(r)
	return r
