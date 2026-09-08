class_name Character
extends RefCounted
## Персонаж: характеристики SRD 5.2, происхождение, класс, пол, уровень,
## навыки, деньги (анны), оси отношения. Рост — уровни, билет, репутация;
## никаких «+2 к мечу».

var display_name: String = "???"
var origin_id: String = ""
var class_id: String = ""
var sex: String = "m"
var level: int = 1
var abilities: Dictionary = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
var proficient_skills: Array[String] = []
var origin_flags: Array[String] = []
var axes: Dictionary = {}
var money: int = 0


func modifier(ability: String) -> int:
	return floori((int(abilities.get(ability, 10)) - 10) / 2.0)


func proficiency_bonus() -> int:
	return 2 + floori((level - 1) / 4.0)


func is_proficient(skill: String) -> bool:
	return proficient_skills.has(skill)


func skill_modifier(skill: String, data: CharacterData) -> int:
	var total := modifier(data.skill_ability(skill))
	if is_proficient(skill):
		total += proficiency_bonus()
	return total


func to_dict() -> Dictionary:
	return {
		"name": display_name,
		"origin": origin_id,
		"class": class_id,
		"gender": sex,
		"level": level,
		"abilities": abilities.duplicate(),
		"skills": Array(proficient_skills),
		"origin_flags": Array(origin_flags),
		"axes": axes.duplicate(),
		"money": money,
	}


static func from_dict(d: Dictionary) -> Character:
	var ch := Character.new()
	ch.display_name = str(d.get("name", "???"))
	ch.origin_id = str(d.get("origin", ""))
	ch.class_id = str(d.get("class", ""))
	ch.sex = str(d.get("gender", "m"))
	ch.level = int(d.get("level", 1))
	var ab: Dictionary = d.get("abilities", {})
	for k in ab.keys():
		ch.abilities[k] = int(ab[k])
	for s in d.get("skills", []):
		ch.proficient_skills.append(String(s))
	for f in d.get("origin_flags", []):
		ch.origin_flags.append(String(f))
	ch.axes = (d.get("axes", {}) as Dictionary).duplicate()
	ch.money = int(d.get("money", 0))
	return ch
