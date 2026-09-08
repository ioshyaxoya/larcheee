class_name CarLoader
extends RefCounted
## Загрузка данных вагона: карточка data/cars/<id>.json (схема B4, валидатор
## car_validator.py), NPC data/npcs/<id>.json, столкновения data/encounters/<id>.json.

const CARS_DIR := "res://data/cars/"
const NPCS_DIR := "res://data/npcs/"
const ENCOUNTERS_DIR := "res://data/encounters/"


static func _read(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("CarLoader: нет файла %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("CarLoader: %s — невалидный JSON" % path)
		return {}
	return parsed


static func load_card(car_id: String) -> Dictionary:
	return _read(CARS_DIR + car_id + ".json")


static func load_npc(npc_id: String) -> Dictionary:
	return _read(NPCS_DIR + npc_id + ".json")


static func load_encounter(enc_id: String) -> Dictionary:
	return _read(ENCOUNTERS_DIR + enc_id + ".json")
