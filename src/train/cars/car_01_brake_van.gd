extends Node
## car_01 — custom_script тормозного вагона. Только уникальная механика (B5):
## холодное открытие, спор о часах на регуляторе (вагон становится на час
## раньше), мягкий откат, сила против терпения Шани, мини-игры службы,
## концовка 5. Всё остальное — в данных вагона.

signal trial_started(trial: TrialRuntime)
signal scene_requested(scene: String)
signal exit_requested(direction: String)
signal ending_requested(ending_id: String)
signal soft_reset_requested(text_key: String)
signal control_locked(seconds: float)
signal title_card(text_key: String)
signal minigame_started(def: Dictionary)

const MINIGAMES_DIR := "res://data/minigames/"

var car: Car
var ctx: GameContext
var trial: TrialRuntime = null
var force_rounds: int = 0
var minigame_handler: Callable        # (id, def) -> Dictionary входов; пусто → автоигра
var simulated_inputs: Dictionary = {} # для тестов: id → входы
var hour_states: Dictionary = {}


func attach(car_node: Car, context: GameContext) -> void:
	car = car_node
	ctx = context
	hour_states = TrialRuntime.load_def(str(car.card.get("trial", "trial_shani"))).get("hours", {})
	car.custom_event.connect(_on_event)


func _on_event(event_name: String) -> void:
	match event_name:
		"door_glimpse":
			control_locked.emit(3.0)   # три секунды приоткрытой двери
		"title_card":
			title_card.emit("co.title")
		"start_trial":
			start_trial()
		"force_round":
			# Пока вы ломаете, он переводит часы — по часу за каждые два раунда взлома.
			force_rounds += 1
			if force_rounds % 2 == 0:
				turn_clock()
		"clock_turn":
			turn_clock()
		"exit_forward":
			car.leave_forward()
			exit_requested.emit("forward")
		"ending_5":
			ending_requested.emit("ending_5")
		"go_force", "go_deceit", "go_service", "go_stay":
			scene_requested.emit(event_name.trim_prefix("go_"))
		"hafiz_named":
			# Сказать вслух — вагон меняется: Кану плачет, Шани впервые встаёт.
			if car.npcs.has("npc_kanu"):
				(car.npcs["npc_kanu"] as NpcNode).set_state("crying")
			if car.npcs.has("god_shani"):
				(car.npcs["god_shani"] as NpcNode).set_state("standing")


func start_trial() -> TrialRuntime:
	trial = TrialRuntime.new(ctx)
	# Монимала вступается в раунде «имя» (преимущество), если едет в вагоне.
	trial.extra_advantage_conditions = [{"all": [{"flag": "prologue.detainer_id", "equals": "widow_monimala"}, {"flag": "prologue.detainer_resolution", "equals": "helped"}]}]
	trial.clock_turned.connect(func(h: int, _st: Dictionary): car.apply_hour_state(h, hour_states))
	trial.soft_reset.connect(_on_soft_reset)
	trial.start(str(car.card.get("trial", "trial_shani")))
	trial_started.emit(trial)
	return trial


## Стрелка на час назад вне спора (сила, провал обмана). Шесть часов — откат.
func turn_clock() -> void:
	var hours := car.hours_lost + 1
	car.apply_hour_state(hours, hour_states)
	var limit := 6
	if trial != null:
		limit = trial.hours_to_reset()
	if hours >= limit:
		_on_soft_reset("trial.shani.soft_reset")


## Мягкий откат: не смерть и не загрузка. Вагон дневной, пустой, на запасном пути;
## игрок — на платформе Хауры за минуту до отправления.
func _on_soft_reset(text_key: String) -> void:
	ctx.world.set_flag("car_01.soft_resets", int(ctx.world.get_flag("car_01.soft_resets", 0)) + 1)
	force_rounds = 0
	car.apply_hour_state(0, hour_states)
	ctx.world.set_flag("car_01.clock_hours_lost", 0)
	soft_reset_requested.emit(text_key)


# --- мини-игры службы --------------------------------------------------------

static func load_minigame(id: String) -> Dictionary:
	var path := MINIGAMES_DIR + id + ".json"
	if not FileAccess.file_exists(path):
		push_error("car_01: нет мини-игры %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


## Провайдер мини-игр для DialogueRuntime: входы от UI/теста, разбор — по данным.
func minigame(id: String) -> bool:
	var def := load_minigame(id)
	if def.is_empty():
		return false
	minigame_started.emit(def)
	var inputs: Variant = null
	if simulated_inputs.has(id):
		inputs = simulated_inputs[id]
	elif minigame_handler.is_valid():
		inputs = minigame_handler.call(id, def)
	return resolve_minigame(def, inputs)


## Разбор мини-игры по данным. inputs: rhythm → массив точностей −1..1;
## choice → {slot: color}; reading → {"notice": bool}. null → автоигра.
func resolve_minigame(def: Dictionary, inputs: Variant) -> bool:
	match str(def.get("type", "")):
		"rhythm":
			var taught: bool = ctx.world.get_flag(str(def.get("taught_flag", "")), false) == true
			var track := RhythmTrack.new()
			track.configure({"bpm": 60, "window_ms": def.get("window_ms_taught", 300) if taught else def.get("window_ms", 180)})
			var beats := int(def.get("beats", 3))
			var accs: Array = inputs if typeof(inputs) == TYPE_ARRAY else []
			var hits := 0
			for i in range(beats):
				var acc: float = float(accs[i]) if i < accs.size() else ctx.rng.randf() * 0.6 - 0.3
				if track.judge_accuracy(acc)["hit"]:
					hits += 1
			return hits >= int(def.get("pass_hits", 2))
		"choice":
			var picks: Dictionary = inputs if typeof(inputs) == TYPE_DICTIONARY else {}
			var all_ok := true
			for slot in def.get("slots", []):
				var chosen := str(picks.get(str(slot["id"]), slot["correct"] if picks.is_empty() else ""))
				if chosen != str(slot["correct"]):
					all_ok = false
			if not all_ok and def.has("error_flag"):
				ctx.world.set_flag(str(def["error_flag"]), true)
			return all_ok
		"reading":
			DialogueEffects.apply(def.get("on_complete", []), ctx)
			var notice: Dictionary = def.get("notice", {})
			if not notice.is_empty():
				var want := true
				if typeof(inputs) == TYPE_DICTIONARY:
					want = bool(inputs.get("notice", true))
				if want:
					var r := ctx.checks.roll(ctx.character, notice["check"])
					if r.success:
						DialogueEffects.apply(notice.get("effects", []), ctx)
			return true
	return false
