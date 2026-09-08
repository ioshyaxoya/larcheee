class_name Endings
extends RefCounted
## Концовки (A15): данные в data/endings/<id>.json — строки, титры, эффекты.
## Концовка 5 «Фонарь» — единственная без детонации.

signal ending_started(def: Dictionary)

const DIR := "res://data/endings/"

var ctx: GameContext


func _init(context: GameContext) -> void:
	ctx = context


static func load_def(ending_id: String) -> Dictionary:
	var path := DIR + ending_id + ".json"
	if not FileAccess.file_exists(path):
		push_error("Endings: нет файла %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


## Запускает концовку: эффекты, флаг ending.reached, сигнал для титров.
func play(ending_id: String) -> Dictionary:
	var def := load_def(ending_id)
	if def.is_empty():
		return {}
	DialogueEffects.apply(def.get("effects", []), ctx)
	ctx.world.location["car"] = ""
	ending_started.emit(def)
	return def


func credits_lines(def: Dictionary) -> Array[String]:
	var out: Array[String] = []
	for k in def.get("lines", []):
		out.append(ctx.texts.t(str(k)))
	for k in def.get("credits", []):
		out.append(ctx.texts.t(str(k)))
	return out
