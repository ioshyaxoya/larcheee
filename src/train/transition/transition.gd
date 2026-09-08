class_name TransitionRuntime
extends RefCounted
## Ритуал перелезания (A8): постановка без бросков, 20–40 секунд. Вариант —
## по главе, погоде, времени суток, состоянию вагона (data/transitions.json).
## После первого просмотра вариант можно пропустить.

signal step(text_key: String, seconds: float, index: int)
signal finished(variant_id: String)

const PATH := "res://data/transitions.json"

var ctx: GameContext
var variants: Dictionary = {}
var current_variant: String = ""
var steps: Array = []
var index: int = -1


func _init(context: GameContext) -> void:
	ctx = context
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(parsed) == TYPE_DICTIONARY:
		variants = parsed.get("variants", {})


## Выбор варианта: первый из подходящих по условиям, предпочитая более специфичный (с условиями).
func pick_variant(preferred: String) -> String:
	var best := preferred if variants.has(preferred) else ""
	for vid in variants.keys():
		var v: Dictionary = variants[vid]
		var conds: Array = v.get("conditions", [])
		if conds.is_empty():
			continue
		if DialogueConditions.all(conds, ctx):
			best = String(vid)
	return best


func seen(variant_id: String) -> bool:
	return (ctx.world.car_state("transitions").get("seen", []) as Array).has(variant_id)


func play(preferred: String) -> String:
	current_variant = pick_variant(preferred)
	if current_variant == "":
		push_error("TransitionRuntime: нет варианта %s" % preferred)
		finished.emit("")
		return ""
	steps = variants[current_variant].get("steps", [])
	index = -1
	next_step()
	return current_variant


func can_skip() -> bool:
	return seen(current_variant)


func next_step() -> void:
	index += 1
	if index >= steps.size():
		_finish()
		return
	var st: Dictionary = steps[index]
	step.emit(str(st.get("text_key", "")), float(st.get("seconds", 3.0)), index)


func skip() -> void:
	if can_skip():
		_finish()


func total_seconds() -> float:
	var t := 0.0
	for st in steps:
		t += float(st.get("seconds", 3.0))
	return t


func _finish() -> void:
	var tr := ctx.world.car_state("transitions")
	var seen_list: Array = tr.get("seen", [])
	if not seen_list.has(current_variant):
		seen_list.append(current_variant)
	tr["seen"] = seen_list
	finished.emit(current_variant)
