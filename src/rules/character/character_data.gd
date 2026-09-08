class_name CharacterData
extends RefCounted
## Данные персонажей из data/character/*.json: характеристики, навыки,
## происхождения, классы (docs/appendix_2_characters.md).

const DIR := "res://data/character/"
const ABILITY_ORDER := ["str", "dex", "con", "int", "wis", "cha"]
const STANDARD_ARRAY := [15, 14, 13, 12, 10, 8]

var abilities: Dictionary = {}
var skills: Dictionary = {}
var origins: Dictionary = {}
var classes: Dictionary = {}


func _init() -> void:
	abilities = _load("abilities.json").get("abilities", {})
	skills = _load("skills.json").get("skills", {})
	origins = _load("origins.json").get("origins", {})
	classes = _load("classes.json").get("classes", {})


static func _load(name: String) -> Dictionary:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(DIR + name))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("CharacterData: %s — невалидный JSON" % name)
		return {}
	return parsed


func skill_ability(skill: String) -> String:
	return skills.get(skill, {}).get("ability", "")


## Собирает персонажа 1-го уровня: стандартный массив по приоритету
## (ключевая характеристика класса, затем характеристики происхождения),
## прибавки происхождения +2/+1, навыки происхождения и класса, деньги.
func build(origin_id: String, class_id: String, sex: String, display_name: String = "???") -> Character:
	if not origins.has(origin_id):
		push_error("CharacterData: неизвестное происхождение %s" % origin_id)
		return null
	if not classes.has(class_id):
		push_error("CharacterData: неизвестный класс %s" % class_id)
		return null
	var origin: Dictionary = origins[origin_id]
	var klass: Dictionary = classes[class_id]
	var ch := Character.new()
	ch.display_name = display_name
	ch.origin_id = origin_id
	ch.class_id = class_id
	ch.sex = "f" if sex == "f" else "m"
	var priority: Array = [klass.get("primary", "str")]
	for a in origin.get("abilities", []):
		if not priority.has(a):
			priority.append(a)
	for a in ABILITY_ORDER:
		if not priority.has(a):
			priority.append(a)
	for i in range(ABILITY_ORDER.size()):
		ch.abilities[priority[i]] = STANDARD_ARRAY[i]
	var bonuses: Array = origin.get("abilities", [])
	if bonuses.size() > 0:
		ch.abilities[bonuses[0]] += 2
	if bonuses.size() > 1:
		ch.abilities[bonuses[1]] += 1
	for s in origin.get("skills", []):
		if not ch.proficient_skills.has(s):
			ch.proficient_skills.append(s)
	for s in klass.get("skills", []):
		if not ch.proficient_skills.has(s):
			ch.proficient_skills.append(s)
	ch.money = int(origin.get("money", 0))
	for f in origin.get("flags", []):
		ch.origin_flags.append(String(f))
	ch.axes = (origin.get("axes", {}) as Dictionary).duplicate()
	ch.axes["sex"] = "woman" if ch.sex == "f" else "man"
	return ch
