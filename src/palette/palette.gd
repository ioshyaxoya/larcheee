class_name Palette
extends RefCounted
## Грейдинг по car.palette (A10) и режим испытания (docs/visual_direction.md §4):
## при остановленном времени цвет уходит (насыщенность → 0), каждый выигранный
## раунд возвращает слой цвета (colour_return 0→1). Одна золотая вспышка — событие.

const PATH := "res://data/palettes.json"

var palettes: Dictionary = {}
var trial_mode: Dictionary = {}
var current_id: String = "human"
var colour_return: float = 1.0
var in_trial: bool = false


func _init() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(parsed) == TYPE_DICTIONARY:
		palettes = parsed.get("palettes", {})
		trial_mode = parsed.get("trial_mode", {})


func has(id: String) -> bool:
	return palettes.has(id)


func params(id: String) -> Dictionary:
	return palettes.get(id, palettes.get("human", {}))


## Итоговые параметры с учётом режима испытания.
func effective() -> Dictionary:
	var p := params(current_id).duplicate()
	if in_trial:
		var sat_zero := float(trial_mode.get("saturation_at_zero", 0.0))
		p["saturation"] = lerpf(sat_zero, float(p.get("saturation", 1.0)), colour_return)
		p["dither"] = str(trial_mode.get("dither", "1bit"))
	return p


func set_palette(id: String) -> void:
	if not has(id):
		push_error("Palette: палитра %s не зарегистрирована" % id)
		return
	current_id = id


func enter_trial() -> void:
	in_trial = true
	colour_return = 0.0


func set_colour_return(value: float) -> void:
	colour_return = clampf(value, 0.0, 1.0)


func exit_trial() -> void:
	in_trial = false
	colour_return = 1.0


## Применить к окружению сцены (Environment.adjustment_*) — базовый грейдинг M0.
func apply(env: Environment) -> void:
	if env == null:
		return
	var p := effective()
	env.adjustment_enabled = true
	env.adjustment_brightness = float(p.get("brightness", 1.0))
	env.adjustment_contrast = float(p.get("contrast", 1.0))
	env.adjustment_saturation = float(p.get("saturation", 1.0))
	var tint: Array = p.get("tint", [1, 1, 1])
	env.ambient_light_color = Color(float(tint[0]) * 0.2, float(tint[1]) * 0.2, float(tint[2]) * 0.2)
