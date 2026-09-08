extends Node
## Точка входа: холодное открытие (вагон 01, часть 1) → «Последние полчаса» →
## возврат в вагон 01 (часть 2): спор о часах, четыре пути, концовка 5.
## Сцена театральная: ортокамера на рельсах, плоскости в объёме, грейдинг по палитре.

signal title_dismissed

var ctx: GameContext
var world_viewport: SubViewport
var trial_viewport: SubViewport
var presence_viewport: SubViewport
var stage: Node3D
var trial_stage: Node3D = null
var camera: Camera3D
var trial_camera: Camera3D
var presence_camera: Camera3D
var world_env: WorldEnvironment
var palette: Palette
var grade: GradeLayer
var theme_res: Theme
var hud: Hud
var dialogue_ui: DialogueUi
var check_ui: CheckUi
var trial_ui: TrialUi
var credits_ui: CreditsUi
var transition_ui: TransitionUi
var debug_panel: DebugPanel
var title_card: Control
var title_label: Label
var hint_label: Label
var car: Car = null
var quest: QuestRuntime = null
var control_locked: bool = false


func _ready() -> void:
	ctx = Game.ctx if Game.ctx != null else Game.new_game(0)
	palette = Palette.new()
	theme_res = GameTheme.build()
	_build_stage()
	_build_grade()
	_build_ui()
	_bind(ctx)


func _build_stage() -> void:
	# Сцена живёт в подвьюпорте: её кадр грейдится шейдером, интерфейс — нет.
	world_viewport = SubViewport.new()
	world_viewport.name = "World"
	world_viewport.size = Vector2i(1280, 720)
	world_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(world_viewport)
	stage = Node3D.new()
	stage.name = "Stage"
	world_viewport.add_child(stage)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 9.0
	camera.position = Vector3(0, 6, 9)
	camera.rotation_degrees = Vector3(-30, 0, 0)
	camera.cull_mask = 1          # слой 1: вагон
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
	_build_trial_viewports()


## Встреча с присутствием собирается из двух кадров одного мира: мир испытания
## (слой 3) уходит в точки, присутствие (слой 2) остаётся цветным. Поэтому две
## отдельные камеры на общем `world_3d`, а не один кадр и маска по цвету:
## монохром не должен «съедать» бога, а бог не должен светиться сквозь скалы.
func _build_trial_viewports() -> void:
	trial_viewport = SubViewport.new()
	trial_viewport.name = "TrialWorld"
	trial_viewport.size = Vector2i(1280, 720)
	# Вне испытания эти два подвьюпорта не нужны, и держать их включёнными —
	# втрое лишняя работа на каждый кадр всей игры. На слабом или программном
	# рендерере (браузер без аппаратного ускорения) кадр просто не успевает, и
	# сцена испытания приходит пустой. Включаются они на входе в испытание.
	trial_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	trial_viewport.own_world_3d = false
	add_child(trial_viewport)
	trial_viewport.world_3d = world_viewport.world_3d
	trial_camera = Camera3D.new()
	trial_camera.cull_mask = 4    # слой 3: мир Шани
	trial_viewport.add_child(trial_camera)
	trial_camera.current = true

	presence_viewport = SubViewport.new()
	presence_viewport.name = "Presence"
	presence_viewport.size = Vector2i(1280, 720)
	presence_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	presence_viewport.transparent_bg = true
	presence_viewport.own_world_3d = false
	add_child(presence_viewport)
	presence_viewport.world_3d = world_viewport.world_3d
	presence_camera = Camera3D.new()
	presence_camera.cull_mask = 2  # слой 2: присутствие
	presence_viewport.add_child(presence_camera)
	presence_camera.current = true


func _build_grade() -> void:
	grade = GradeLayer.new()
	add_child(grade)
	grade.set_source(world_viewport.get_texture())
	grade.set_trial_source(trial_viewport.get_texture(), presence_viewport.get_texture())
	grade.bind(palette)


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 2   # интерфейс поверх грейдинга
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
	var title_layer := CanvasLayer.new()
	title_layer.layer = 10
	title_card_theme_holder(title_layer)
	add_child(title_layer)
	title_card = Control.new()
	title_card.theme = theme_res
	title_card.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	title_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_card.visible = false
	title_layer.add_child(title_card)
	var backdrop := ColorRect.new()
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0, 0, 0, 0.92)
	title_card.add_child(backdrop)
	title_label = Label.new()
	title_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	title_label.add_theme_font_override("font", GameTheme.clock_font())
	title_label.add_theme_font_size_override("font_size", 46)
	title_label.add_theme_color_override("font_color", GameTheme.TEXT)
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_card.add_child(title_label)
	hint_label = Label.new()
	hint_label.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	hint_label.offset_left = -260
	hint_label.offset_top = -32
	hint_label.modulate = Color(0.6, 0.6, 0.65)
	layer.add_child(hint_label)
	debug_panel.start_requested.connect(_on_start)
	debug_panel.enter_car_requested.connect(_on_enter_car)
	debug_panel.talk_requested.connect(_on_talk)
	debug_panel.take_requested.connect(func(item_id: String):
		if car != null and car.take_item(item_id):
			debug_panel.show_car_controls(car))
	debug_panel.car_only_requested.connect(_on_car_only)
	debug_panel.scene_requested.connect(func(scene: String):
		if car == null:
			return
		dialogue_ui.attach(car.play_scene(scene)))
	debug_panel.trial_requested.connect(func():
		if car != null:
			_on_trial_started(car.custom.start_trial()))
	debug_panel.save_requested.connect(func(): ctx.save())
	debug_panel.load_requested.connect(_on_load)
	credits_ui.closed.connect(func(): debug_panel.visible = true)


## Титр — тоже интерфейс: тема нужна и ему.
func title_card_theme_holder(_layer: CanvasLayer) -> void:
	pass


func _bind(context: GameContext) -> void:
	ctx = context
	for ui in [hud, dialogue_ui, check_ui, trial_ui, credits_ui, transition_ui, debug_panel]:
		ui.theme = theme_res
		ui.bind(ctx)
	hint_label.text = ctx.texts.t("ui.debug.hint")


func _apply_palette() -> void:
	palette.apply(world_env.environment)
	if grade != null:
		grade.refresh()


# --- поток ------------------------------------------------------------------

## F1 — показать или спрятать панель разработчика.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and (event as InputEventKey).keycode == KEY_F1:
		debug_panel.visible = not debug_panel.visible


func _on_start(origin: String, class_id: String, sex: String, tags: Array, seed_v: int) -> void:
	_bind(Game.new_game(seed_v))
	debug_panel.visible = false
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
	var card := CarLoader.load_card("car_01")
	car.setup(card, ctx)
	stage.add_child(car)
	StageBuilder.apply_camera(card, camera, car.motion)
	palette.set_palette(str(card.get("palette", "human")))
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
	if title_card.visible:
		await title_dismissed   # пролог начинается после титра, не под ним
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
	# Журнал минут пролога в суде не нужен: шкала здесь другая — часы на
	# регуляторе, а не потерянные в Калькутте минуты.
	hud.clear_log()
	palette.enter_trial()
	_enter_presence(trial)
	_apply_palette()
	trial.round_won.connect(func(_rd: Dictionary, _k: String):
		palette.set_colour_return(float(trial.streak) / float(trial.wins_needed()))
		# Мир Шани держится тем крепче, чем меньше он в вас сомневается.
		grade.set_glitch(clampf(0.55 - 0.16 * float(trial.streak), 0.0, 1.0))
		_apply_palette())
	trial.round_lost.connect(func(_rd: Dictionary, _k: String):
		palette.set_colour_return(0.0)
		grade.set_glitch(0.78)
		_apply_palette())
	trial.trial_won.connect(func(_k: String):
		_leave_presence()
		palette.exit_trial()
		_apply_palette()
		dialogue_ui.attach(car.play_scene("paths_hub")))
	trial_ui.attach(trial)


## Встреча с присутствием: собрать мир испытания и поставить обе камеры.
## Постановка живёт в данных испытания (`trial.stage`), как и постановка вагона.
func _enter_presence(trial: TrialRuntime) -> void:
	_leave_presence()
	var st: Dictionary = trial.def.get("stage", {})
	if st.is_empty():
		return
	trial_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	presence_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	trial_stage = Node3D.new()
	trial_stage.name = "TrialStage"
	stage.add_child(trial_stage)
	var trial_motion := StageBuilder.build_stage(st, trial_stage)
	var frame := {"stage": st}
	StageBuilder.apply_camera(frame, trial_camera, trial_motion)
	StageBuilder.apply_camera(frame, presence_camera, trial_motion)
	grade.set_glitch(0.55)


func _leave_presence() -> void:
	trial_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	presence_viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	if trial_stage != null:
		trial_stage.queue_free()
		trial_stage = null
	grade.set_glitch(0.0)


func _on_soft_reset(_text_key: String) -> void:
	_leave_presence()
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
	tr.finished.connect(func(_v: String): _show_title("ui.car02.stub"))
	transition_ui.attach(tr)
	tr.play(str(car.card.get("transition_variant", "night_bengal")))


func _on_ending(ending_id: String) -> void:
	var endings := Endings.new(ctx)
	var def := endings.play(ending_id)
	debug_panel.visible = false
	credits_ui.show_ending(def, endings)


## Отладочный вход: сразу в тормозной вагон, минуя пролог. Пути и спор — оттуда.
func _on_car_only(origin: String, class_id: String, sex: String, seed_v: int) -> void:
	_bind(Game.new_game(seed_v))
	ctx.set_character(ctx.char_data.build(origin, class_id, sex))
	ctx.world.set_flag("car_01.lantern_lit", true)
	ctx.world.set_flag("prologue.completed", true)
	_spawn_car()
	debug_panel.show_car_controls(car)
	dialogue_ui.attach(car.play_scene("paths_hub"))


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


func _show_title(text_key: String, seconds: float = 3.0) -> void:
	title_label.text = ctx.texts.t(text_key)
	title_card.visible = true
	await get_tree().create_timer(seconds).timeout
	title_card.visible = false
	title_dismissed.emit()
