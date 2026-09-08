class_name TrialRuntime
extends RefCounted
## Испытание присутствия (A9/A10): раунды-аргументы поверх ритма, лексика —
## «испытание». Для Шани шкала — часы на регуляторе: проигранный раунд =
## стрелка на час назад, и вагон физически становится на час раньше.
## Минус шесть часов — мягкий откат, не смерть и не загрузка.

signal round_started(round_def: Dictionary, index: int)
signal round_won(round_def: Dictionary, text_key: String)
signal round_lost(round_def: Dictionary, text_key: String)
signal clock_turned(hours_lost: int, hour_state: Dictionary)
signal gold_flash
signal trial_won(text_key: String)
signal soft_reset(text_key: String)
signal check_resolved(result: CheckResult)

const DIR := "res://data/trials/"

var ctx: GameContext
var def: Dictionary = {}
var rhythm := RhythmTrack.new()
var round_index: int = 0
var hours_lost: int = 0
var streak: int = 0
var finished: bool = false
var outcome: String = ""        # "won" | "soft_reset"
var last_check: CheckResult = null
var extra_advantage_conditions: Array = []


static func load_def(trial_id: String) -> Dictionary:
	var path := DIR + trial_id + ".json"
	if not FileAccess.file_exists(path):
		push_error("TrialRuntime: нет файла %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _init(context: GameContext) -> void:
	ctx = context


func start(trial_id: String) -> bool:
	def = load_def(trial_id)
	if def.is_empty():
		return false
	rhythm.configure(def.get("rhythm", {}))
	round_index = 0
	hours_lost = 0
	streak = 0
	finished = false
	outcome = ""
	round_started.emit(current_round(), round_index)
	return true


func rounds() -> Array:
	return def.get("rounds", [])


func current_round() -> Dictionary:
	var rs := rounds()
	return rs[round_index % rs.size()] if not rs.is_empty() else {}


func wins_needed() -> int:
	return int(def.get("wins_needed", 3))


func hours_to_reset() -> int:
	return int(def.get("soft_reset_at_hours_lost", 6))


## Критический аргумент доступен, если выполнены его условия (журнал прочитан, затирание замечено).
func critical_available() -> bool:
	var crit: Dictionary = def.get("critical_argument", {})
	return not crit.is_empty() and DialogueConditions.all(crit.get("conditions", []), ctx)


## Варианты текущего раунда для UI: только доступные по условиям.
func options() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var opts: Array = current_round().get("options", [])
	for i in range(opts.size()):
		var o: Dictionary = opts[i]
		if not DialogueConditions.all(o.get("conditions", []), ctx):
			continue
		var view := {"index": i, "text_key": str(o.get("text_key", "")), "check": o.get("check", {}), "auto": str(o.get("auto", "")), "needs_beat": o.has("check")}
		out.append(view)
	if critical_available():
		out.append({"index": -1, "text_key": str(def["critical_argument"].get("text_key", "")), "check": {}, "auto": "critical", "needs_beat": false})
	return out


## Выбор аргумента. rhythm_mod — видимый модификатор ритма (RhythmTrack.judge).
func choose(index: int, rhythm_mod: int = 0) -> void:
	if finished:
		return
	var rd := current_round()
	if index == -1:
		if not critical_available():
			return
		_win_trial(str(def["critical_argument"].get("outcome_key", "")))
		return
	var opts: Array = rd.get("options", [])
	if index < 0 or index >= opts.size():
		return
	var o: Dictionary = opts[index]
	var auto := str(o.get("auto", ""))
	var won := false
	if auto == "win":
		won = true
	elif auto == "lose":
		won = false
	else:
		var advantage := false
		for c in o.get("advantage_if", []):
			if DialogueConditions.evaluate(c, ctx):
				advantage = true
		for c in extra_advantage_conditions:
			if DialogueConditions.evaluate(c, ctx):
				advantage = true
		var extras: Array = []
		if rhythm_mod != 0:
			extras.append({"label_key": "ui.check.mod.rhythm", "value": rhythm_mod})
		last_check = ctx.checks.roll(ctx.character, o["check"], extras, advantage)
		check_resolved.emit(last_check)
		won = last_check.success
	if won:
		streak += 1
		round_won.emit(rd, str(o.get("win_key", "")))
		if streak >= wins_needed():
			_win_trial(str(def.get("win", {}).get("text_key", "")))
			return
	else:
		streak = 0
		round_lost.emit(rd, str(o.get("lose_key", "")))
		_turn_clock()
		if finished:
			return
	round_index += 1
	round_started.emit(current_round(), round_index)


## Стрелка на час назад: золотая вспышка, вагон становится на час раньше.
func _turn_clock() -> void:
	hours_lost += int(def.get("loss_per_round_hours", 1))
	gold_flash.emit()
	clock_turned.emit(hours_lost, (def.get("hours", {}) as Dictionary).get(str(hours_lost), {}))
	if hours_lost >= hours_to_reset():
		finished = true
		outcome = "soft_reset"
		DialogueEffects.apply(def.get("soft_reset", {}).get("effects", []), ctx)
		soft_reset.emit(str(def.get("soft_reset", {}).get("text_key", "")))


func _win_trial(text_key: String) -> void:
	finished = true
	outcome = "won"
	DialogueEffects.apply(def.get("win", {}).get("effects", []), ctx)
	trial_won.emit(text_key)
