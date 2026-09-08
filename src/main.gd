extends Node
## Точка входа M0: театральная сцена (ортокамера на рельсах, плоскости в объёме),
## HUD с битовыми часами, панель диалога, видимая проверка, отладочная панель.
## Поток: выбрать персонажа → «Последние полчаса» → войти в тормозной вагон.

var ctx: GameContext
var stage: Node3D
var camera: Camera3D
var hud: Hud
var dialogue_ui: DialogueUi
var check_ui: CheckUi
var debug_panel: DebugPanel
var car: Car = null
var quest: QuestRuntime = null
var control_locked: bool = false


func _ready() -> void:
	ctx = Game.ctx if Game.ctx != null else Game.new_game(0)
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
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.03, 0.03, 0.05)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.12, 0.12, 0.18)
	env.environment = e
	stage.add_child(env)


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = Hud.new()
	layer.add_child(hud)
	dialogue_ui = DialogueUi.new()
	layer.add_child(dialogue_ui)
	debug_panel = DebugPanel.new()
	layer.add_child(debug_panel)
	check_ui = CheckUi.new()
	layer.add_child(check_ui)
	debug_panel.start_requested.connect(_on_start)
	debug_panel.enter_car_requested.connect(_on_enter_car)
	debug_panel.talk_requested.connect(_on_talk)
	debug_panel.save_requested.connect(func(): ctx.save())
	debug_panel.load_requested.connect(_on_load)


func _bind(context: GameContext) -> void:
	ctx = context
	hud.bind(ctx)
	dialogue_ui.bind(ctx)
	check_ui.bind(ctx)
	debug_panel.bind(ctx)


func _on_start(origin: String, class_id: String, sex: String, tags: Array, seed_v: int) -> void:
	_bind(Game.new_game(seed_v))
	var ch := ctx.char_data.build(origin, class_id, sex)
	ctx.set_character(ch)
	for tag in tags:
		ctx.world.add_tag(str(tag))
	quest = QuestRuntime.new(ctx)
	var rt := quest.start("quest_last_half_hour")
	rt.custom_event.connect(_on_custom_event)
	quest.finished.connect(func(_snap: Dictionary): debug_panel.show_enter_car())
	dialogue_ui.attach(rt)
	hud.refresh()


func _on_enter_car() -> void:
	if car != null:
		car.queue_free()
	car = Car.new()
	car.setup(CarLoader.load_card("car_01"), ctx)
	stage.add_child(car)
	car.enter()
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


## Прыжок — единственные полторы секунды пролога, где управление отбирается.
func _on_custom_event(event_name: String) -> void:
	if event_name == "jump_cutscene":
		control_locked = true
		dialogue_ui.visible = false
		get_tree().create_timer(1.5).timeout.connect(func():
			control_locked = false
			dialogue_ui.visible = true)
