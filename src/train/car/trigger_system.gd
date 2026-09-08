class_name TriggerSystem
extends RefCounted
## Триггеры вагона: столкновения из data/encounters/*.json по событиям
## car_entered / npc_approached / dialogue_ended / item_taken. Логика — в
## данных: условия и эффекты общего языка (docs/data_format.md).

signal custom_event(name: String)
signal fired(trigger_id: String)

var ctx: GameContext
var triggers: Array[Dictionary] = []
var fired_once: Dictionary = {}


func _init(context: GameContext) -> void:
	ctx = context


func add(trigger: Dictionary) -> void:
	triggers.append(trigger)


## Возвращает id сработавших триггеров.
func fire(event: String, payload: Dictionary = {}) -> Array[String]:
	var hits: Array[String] = []
	for t in triggers:
		if str(t.get("event", "")) != event:
			continue
		var tid := str(t.get("id", ""))
		if t.get("once", false) and fired_once.get(tid, false):
			continue
		if t.has("npc") and str(t["npc"]) != str(payload.get("npc", "")):
			continue
		if not DialogueConditions.all(t.get("conditions", []), ctx):
			continue
		DialogueEffects.apply(t.get("effects", []), ctx, self)
		fired_once[tid] = true
		hits.append(tid)
		fired.emit(tid)
	return hits
