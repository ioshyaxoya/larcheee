extends Node
## Точка входа: холодное открытие (вагон 01, часть 1) → «Последние полчаса» →
## возврат в вагон 01 (часть 2): спор о часах, четыре пути, концовка 5.
## Сцена театральная: ортокамера на рельсах, плоскости в объёме, грейдинг по палитре.

var ctx: GameContext
var stage: Node3D
var camera: Camera3D
var world_env: WorldEnvironment
var palette: Palette
var hud: Hud
var dialogue_ui: DialogueUi
var check_ui: CheckUi
var trial_ui: TrialUi
var credits_ui: CreditsUi
var transition_ui: TransitionUi
var debug_panel: DebugPanel
var title_label: Label
var car: Car = null
var quest: QuestRuntime = null
var control_locked: bool = false


func _ready() -> void:
	ctx = Game.ctx if Game.ctx != null else Game.new_game(0)
	palette = Palette.new()
	_build_stage()
	_build_ui()
	_bind(ctx)


func _build_stage() -> void:
	stage = Node3D.new()
	stage.name = "Stage"
	add_child(stage)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 9.0
	camera.position = Vector3(0, 6, 9)
	camera.rotation_degrees = Vector3(-30, 0, 0)
	stage.add_child(camera)
	camera.current = true
	world_env = WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.03, 0.03, 0.05)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.12, 0.12, 0.18)
	world_env.environment = e
	stage.add_child(world_env)


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = Hud.new()
	layer.add_child(hud)
	dialogue_ui = DialogueUi.new()
	layer.add_child(dialogue_ui)
	trial_ui = TrialUi.new()
	layer.add_child(trial_ui)
	transition_ui = TransitionUi.new()
	layer.add_child(transition_ui)
	debug_panel = DebugPanel.new()
	layer.add_child(debug_panel)
	check_ui = CheckUi.new()
	layer.add_child(check_ui)
	credits_ui = CreditsUi.new()
	layer.add_child(credits_ui)
	title_label = Label.new()
	title_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	title_label.add_theme_font_size_override("font_size", 48)
	title_label.visible = false
	layer.add_child(title_label)
	debug_panel.start_requested.connect(_on_start)
	debug_panel.enter_car_requested.connect(_on_enter_car)
	debug_panel.talk_requested.connect(_on_talk)
	debug_panel.take_requested.connect(func(item_id: String):
		if car != null and car.take_item(item_id):
			debug_panel.show_car_controls(car))
	debug_panel.save_requested.connect(func(): ctx.save())
	debug_panel.load_requested.connect(_on_load)
	credits_ui.closed.connect(func(): debug_panel.visible = true)


func _bind(context: GameContext) -> void:
	ctx = context
	for ui in [hud, dialogue_ui, check_ui, trial_ui, credits_ui, transition_ui, debug_panel]:
		ui.bind(ctx)


func _apply_palette() -> void:
	palette.apply(world_env.environment)


# --- поток ------------------------------------------------------------------

func _on_start(origin: String, class_id: String, sex: String, tags: Array, seed_v: int) -> void:
	_bind(Game.new_game(seed_v))
	var ch := ctx.char_data.build(origin, class_id, sex)
	ctx.set_character(ch)
	for tag in tags:
		ctx.world.add_tag(str(tag))
	_spawn_car()
	# Холодное открытие: три минуты до пролога.
	var rt := car.play_scene("cold_open")
	rt.ended.connect(_start_prologue, CONNECT_ONE_SHOT)
	dialogue_ui.attach(rt)
	hud.refresh()


func _spawn_car() -> void:
	if car != null:
		car.queue_free()
	car = Car.new()
	car.setup(CarLoader.load_card("car_01"), ctx)
	stage.add_child(car)
	palette.set_palette(str(car.card.get("palette", "human")))
	_apply_palette()
	car.custom.control_locked.connect(_lock_control)
	car.custom.title_card.connect(_show_title)
	car.custom.trial_started.connect(_on_trial_started)
	car.custom.scene_requested.connect(func(scene: String): dialogue_ui.attach(car.play_scene(scene)))
	car.custom.exit_requested.connect(_on_exit_forward)
	car.custom.ending_requested.connect(_on_ending)
	car.custom.soft_reset_requested.connect(_on_soft_reset)
	car.custom.minigame_handler = func(_id: String, _def: Dictionary): return null   # автоигра до появления UI мини-игр
	car.enter()


func _start_prologue() -> void:
	car.visible = false
	quest = QuestRuntime.new(ctx)
	var rt := quest.start("quest_last_half_hour")
	rt.custom_event.connect(_on_quest_event)
	quest.finished.connect(_return_to_car, CONNECT_ONE_SHOT)
	dialogue_ui.attach(rt)


func _return_to_car(_snap: Dictionary) -> void:
	# Возврат — с пункта 8: силуэт поворачивается. NPC из пролога уже здесь.
	_spawn_car()
	var rt := car.play_scene("return")
	dialogue_ui.attach(rt)


func _on_trial_started(trial: TrialRuntime) -> void:
	palette.enter_trial()
	_apply_palette()
	trial.round_won.connect(func(_rd: Dictionary, _k: String):
		palette.set_colour_return(float(trial.streak) / float(trial.wins_needed()))
		_apply_palette())
	trial.round_lost.connect(func(_rd: Dictionary, _k: String):
		palette.set_colour_return(0.0)
		_apply_palette())
	trial.trial_won.connect(func(_k: String):
		palette.exit_trial()
		_apply_palette()
		dialogue_ui.attach(car.play_scene("paths_hub")))
	trial_ui.attach(trial)


func _on_soft_reset(_text_key: String) -> void:
	palette.exit_trial()
	_apply_palette()
	car.visible = false
	quest = QuestRuntime.new(ctx)
	var rt := quest.start("quest_last_half_hour", "platform", 20 * 60 + 29)
	rt.custom_event.connect(_on_quest_event)
	quest.finished.connect(_return_to_car, CONNECT_ONE_SHOT)
	dialogue_ui.attach(rt)


func _on_exit_forward(_direction: String) -> void:
	var tr := TransitionRuntime.new(ctx)
	tr.finished.connect(func(_v: String):
		title_label.text = ctx.texts.t("ui.car02.stub")
		title_label.visible = true
		get_tree().create_timer(3.0).timeout.connect(func(): title_label.visible = false))
	transition_ui.attach(tr)
	tr.play(str(car.card.get("transition_variant", "night_bengal")))


func _on_ending(ending_id: String) -> void:
	var endings := Endings.new(ctx)
	var def := endings.play(ending_id)
	debug_panel.visible = false
	credits_ui.show_ending(def, endings)


func _on_enter_car() -> void:
	if car == null:
		_spawn_car()
	debug_panel.show_car_controls(car)


func _on_talk(npc_id: String) -> void:
	if car == null:
		return
	var rt := car.talk_to(npc_id)
	if rt != null:
		dialogue_ui.attach(rt)


func _on_load() -> void:
	var fresh := Game.new_game(0)
	if fresh.load_from():
		_bind(fresh)
		hud.refresh()


## Прыжок — единственные полторы секунды пролога, где управление отбирается;
## дверь холодного открытия — три секунды.
func _on_quest_event(event_name: String) -> void:
	if event_name == "jump_cutscene":
		_lock_control(1.5)


func _lock_control(seconds: float) -> void:
	control_locked = true
	dialogue_ui.visible = false
	get_tree().create_timer(seconds).timeout.connect(func():
		control_locked = false
		dialogue_ui.visible = true)


func _show_title(text_key: String) -> void:
	title_label.text = ctx.texts.t(text_key)
	title_label.visible = true
	get_tree().create_timer(3.0).timeout.connect(func(): title_label.visible = false)
