class_name QuestRuntime
extends RefCounted
## Квест на битовых часах (data/prologue/quest_*.json): настраивает часы,
## подключает провайдеры шанса и говорящих, гонит граф входного диалога.

signal finished(snapshot: Dictionary)

const DIR := "res://data/prologue/"

var ctx: GameContext
var def: Dictionary = {}
var runtime: DialogueRuntime


static func load_def(quest_id: String) -> Dictionary:
	var path := DIR + quest_id + ".json"
	if not FileAccess.file_exists(path):
		push_error("QuestRuntime: нет файла %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _init(context: GameContext) -> void:
	ctx = context


func start(quest_id: String, start_node: String = "", start_minutes: int = -1) -> DialogueRuntime:
	def = load_def(quest_id)
	if def.is_empty():
		return null
	var clock: Dictionary = def.get("clock", {})
	var start_m := int(clock.get("start_minutes", 20 * 60)) if start_minutes < 0 else start_minutes
	ctx.clock.configure(start_m, int(clock.get("deadline_minutes", 20 * 60 + 30)))
	ctx.world.location["quest"] = quest_id
	runtime = DialogueRuntime.new(ctx)
	runtime.chance_provider = func(provider: String) -> float: return ChanceProviders.probability(provider, ctx)
	for npc in def.get("npcs", []):
		runtime.speakers[str(npc["id"])] = str(npc["name_key"])
	runtime.ended.connect(_on_ended)
	var dlg: Dictionary = (def["dialogues"][str(def["entry"])] as Dictionary).duplicate()
	if start_node != "":
		dlg["start"] = start_node
	runtime.start(dlg)
	return runtime


## Что квест уносит дальше: все флаги пролога + опоздание.
func output_snapshot() -> Dictionary:
	var snap := {}
	for name in ctx.world.flags.keys():
		if String(name).begins_with("prologue."):
			snap[name] = ctx.world.flags[name]
	snap["minutes_late"] = ctx.clock.minutes_late()
	snap["clock"] = ctx.clock.now_string()
	return snap


func _on_ended() -> void:
	ctx.world.location["quest"] = ""
	finished.emit(output_snapshot())
