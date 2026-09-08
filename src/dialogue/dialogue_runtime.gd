class_name DialogueRuntime
extends RefCounted
## Рантайм графа диалогов: узлы, ветвления, условия, эффекты, проверки и
## броски шанса внутри реплик, цена варианта на битовых часах.
## Цена показывается до выбора (available_options), списывается в момент выбора.

signal node_entered(node_id: String, node: Dictionary)
signal check_resolved(result: CheckResult)
signal time_charged(minutes: int, reason_key: String)
signal custom_event(name: String)
signal ended()

var ctx: GameContext
var nodes: Dictionary = {}
var current_id: String = ""
var current: Dictionary = {}
var finished: bool = false
var speakers: Dictionary = {}          # npc_id → name_key (говорящие квеста)
var chance_provider: Callable          # (provider: String) -> float
var minigame_provider: Callable        # (minigame_id: String) -> bool — успех/провал мини-игры
var last_check: CheckResult = null
var trail: Array[String] = []


func _init(context: GameContext) -> void:
	ctx = context
	chance_provider = func(_provider: String) -> float: return 0.5
	minigame_provider = func(_id: String) -> bool: return true


func start(dialogue: Dictionary) -> void:
	nodes = dialogue.get("nodes", {})
	finished = false
	trail.clear()
	enter(str(dialogue.get("start", "")))


func enter(node_id: String) -> void:
	if finished:
		return
	if not nodes.has(node_id):
		push_error("DialogueRuntime: узла «%s» нет" % node_id)
		_finish()
		return
	current_id = node_id
	current = nodes[node_id]
	trail.append(node_id)
	if current.has("branches"):
		for br in current["branches"]:
			if DialogueConditions.all(br.get("conditions", []), ctx):
				enter(str(br["next"]))
				return
		push_error("DialogueRuntime: ни одна ветка «%s» не подошла" % node_id)
		_finish()
		return
	var jump := DialogueEffects.apply(current.get("on_enter", []), ctx, self)
	node_entered.emit(node_id, current)
	if jump["end"]:
		_finish()
	elif jump["goto"] != "":
		enter(jump["goto"])
	elif current.get("end", false) and current.get("options", []).is_empty():
		_finish()


## Есть ли у узла варианты; если нет — узел продолжается кнопкой «Дальше» (advance).
func has_options() -> bool:
	return not current.get("options", []).is_empty()


## Варианты, доступные игроку сейчас, с ценой и разбором проверки — для UI.
func available_options() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var opts: Array = current.get("options", [])
	for i in range(opts.size()):
		var opt: Dictionary = opts[i]
		if not DialogueConditions.all(opt.get("conditions", []), ctx):
			continue
		var view := {
			"index": i,
			"text_key": str(opt.get("text_key", "")),
			"cost_minutes": int(opt.get("cost_minutes", 0)),
			"cost_on_fail_minutes": int(opt.get("cost_on_fail_minutes", opt.get("cost_minutes", 0))),
			"cost_note_key": str(opt.get("cost_note_key", "")),
			"check": opt.get("check", {}),
			"chance": opt.get("chance", {}),
			"minigame": str(opt.get("minigame", "")),
			"probability": 0.0,
			"hit_minutes": 0,
		}
		if opt.has("chance"):
			view["probability"] = float(chance_provider.call(str(opt["chance"].get("provider", "coin"))))
			view["hit_minutes"] = int(opt["chance"].get("hit_minutes", 0))
		out.append(view)
	return out


## Узел без вариантов: перейти по next или закончить.
func advance() -> void:
	if finished or has_options():
		return
	if current.has("next"):
		enter(str(current["next"]))
	else:
		_finish()


func choose(index: int) -> void:
	if finished:
		return
	var opts: Array = current.get("options", [])
	if index < 0 or index >= opts.size():
		push_error("DialogueRuntime: нет варианта %d" % index)
		return
	var opt: Dictionary = opts[index]
	if not DialogueConditions.all(opt.get("conditions", []), ctx):
		push_error("DialogueRuntime: вариант %d недоступен" % index)
		return
	var text_key := str(opt.get("text_key", ""))
	var success := true
	if opt.has("minigame"):
		success = bool(minigame_provider.call(str(opt["minigame"])))
	if opt.has("check"):
		last_check = ctx.checks.roll(ctx.character, opt["check"])
		success = last_check.success
		check_resolved.emit(last_check)
	var cost := int(opt.get("cost_minutes", 0))
	if not success:
		cost = int(opt.get("cost_on_fail_minutes", cost))
	if cost > 0:
		ctx.clock.spend(cost, text_key)
		time_charged.emit(cost, text_key)
	if opt.has("chance"):
		var ch: Dictionary = opt["chance"]
		var p := float(chance_provider.call(str(ch.get("provider", "coin"))))
		last_check = ctx.checks.roll_chance(str(ch.get("label_key", "")), p)
		check_resolved.emit(last_check)
		var jump := DialogueEffects.apply(opt.get("effects", []), ctx, self)
		if last_check.success:
			var extra := int(ch.get("hit_minutes", 0))
			if extra > 0:
				ctx.clock.spend(extra, str(ch.get("label_key", "")))
				time_charged.emit(extra, str(ch.get("label_key", "")))
			_go(jump, str(ch.get("on_hit", "")))
		else:
			_go(jump, str(ch.get("on_miss", "")))
		return
	if success:
		_go(DialogueEffects.apply(opt.get("effects", []), ctx, self), str(opt.get("next", "")))
	else:
		_go(DialogueEffects.apply(opt.get("effects_on_fail", []), ctx, self), str(opt.get("next_on_fail", "")))


func _go(jump: Dictionary, next_id: String) -> void:
	if jump["end"]:
		_finish()
	elif jump["goto"] != "":
		enter(jump["goto"])
	elif next_id != "":
		enter(next_id)
	else:
		_finish()


func speaker_name_key(node: Dictionary) -> String:
	var speaker := str(node.get("speaker", "narrator"))
	if speaker == "narrator" or speaker == "player":
		return ""
	if speakers.has(speaker):
		return str(speakers[speaker])
	return "npc." + speaker.trim_prefix("npc_") + ".name"


func _finish() -> void:
	if finished:
		return
	finished = true
	ended.emit()
