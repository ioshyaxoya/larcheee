class_name DebugPanel
extends Control
## Отладочная панель M0: выбрать происхождение, класс, пол, теги пролога и seed,
## начать квест, войти в вагон, заговорить с NPC, сохранить/загрузить.

signal start_requested(origin: String, class_id: String, sex: String, tags: Array, seed_v: int)
signal enter_car_requested
signal talk_requested(npc_id: String)
signal take_requested(item_id: String)
signal car_only_requested(origin: String, class_id: String, sex: String, seed_v: int)
signal scene_requested(scene: String)
signal trial_requested
signal save_requested
signal load_requested

var ctx: GameContext
var origin_btn: OptionButton
var class_btn: OptionButton
var sex_btn: OptionButton
var seed_spin: SpinBox
var tag_boxes: Dictionary = {}
var talk_box: VBoxContainer
var enter_button: Button
var _origin_ids: Array = []
var _class_ids: Array = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	panel.offset_left = -380
	panel.offset_top = 16
	panel.offset_right = -16
	add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	origin_btn = OptionButton.new()
	class_btn = OptionButton.new()
	sex_btn = OptionButton.new()
	seed_spin = SpinBox.new()
	seed_spin.max_value = 999999
	box.add_child(origin_btn)
	box.add_child(class_btn)
	box.add_child(sex_btn)
	box.add_child(seed_spin)
	talk_box = VBoxContainer.new()
	box.add_child(talk_box)
	enter_button = Button.new()
	enter_button.visible = false
	enter_button.pressed.connect(func(): enter_car_requested.emit())
	box.add_child(enter_button)
	var row := HBoxContainer.new()
	box.add_child(row)
	var save_b := Button.new()
	save_b.pressed.connect(func(): save_requested.emit())
	row.add_child(save_b)
	var load_b := Button.new()
	load_b.pressed.connect(func(): load_requested.emit())
	row.add_child(load_b)
	set_meta("save_b", save_b)
	set_meta("load_b", load_b)
	set_meta("box", box)


func bind(context: GameContext) -> void:
	ctx = context
	var t := ctx.texts
	origin_btn.clear()
	_origin_ids = ctx.char_data.origins.keys()
	for oid in _origin_ids:
		origin_btn.add_item(t.t(str(ctx.char_data.origins[oid]["name_key"])))
	class_btn.clear()
	_class_ids = ctx.char_data.classes.keys()
	for cid in _class_ids:
		class_btn.add_item(t.t(str(ctx.char_data.classes[cid]["name_key"])))
	sex_btn.clear()
	sex_btn.add_item(t.t("ui.debug.sex_m"))
	sex_btn.add_item(t.t("ui.debug.sex_f"))
	seed_spin.prefix = t.t("ui.debug.seed") + " "
	var box: VBoxContainer = get_meta("box")
	if tag_boxes.is_empty():
		var tags_label := Label.new()
		tags_label.text = t.t("ui.debug.tags")
		box.add_child(tags_label)
		box.move_child(tags_label, 4)
		var grid := GridContainer.new()
		grid.columns = 2
		box.add_child(grid)
		box.move_child(grid, 5)
		for tag in ["union_seed", "mallick_lecture", "opium_touched", "widow_saved", "sepoy_met", "kabuli_ledger", "tiretta_favor", "lascar_papers", "census_answered", "ice_bought"]:
			var cb := CheckBox.new()
			cb.text = tag
			grid.add_child(cb)
			tag_boxes[tag] = cb
		var start_b := Button.new()
		start_b.text = t.t("ui.debug.start")
		start_b.pressed.connect(_on_start)
		box.add_child(start_b)
		box.move_child(start_b, 6)
		var car_b := Button.new()
		car_b.text = t.t("ui.debug.car_only")
		car_b.pressed.connect(func(): car_only_requested.emit(str(_origin_ids[origin_btn.selected]), str(_class_ids[class_btn.selected]), "f" if sex_btn.selected == 1 else "m", int(seed_spin.value)))
		box.add_child(car_b)
		box.move_child(car_b, 7)
		var paths_b := Button.new()
		paths_b.text = t.t("ui.debug.paths")
		paths_b.pressed.connect(func(): scene_requested.emit("paths_hub"))
		box.add_child(paths_b)
		box.move_child(paths_b, 8)
		var trial_b := Button.new()
		trial_b.text = t.t("ui.debug.trial")
		trial_b.pressed.connect(func(): trial_requested.emit())
		box.add_child(trial_b)
		box.move_child(trial_b, 9)
	enter_button.text = t.t("ui.debug.enter_car")
	(get_meta("save_b") as Button).text = t.t("ui.debug.save")
	(get_meta("load_b") as Button).text = t.t("ui.debug.load")


func _on_start() -> void:
	var tags: Array = []
	for tag in tag_boxes.keys():
		if (tag_boxes[tag] as CheckBox).button_pressed:
			tags.append(tag)
	start_requested.emit(str(_origin_ids[origin_btn.selected]), str(_class_ids[class_btn.selected]), "f" if sex_btn.selected == 1 else "m", tags, int(seed_spin.value))


func show_car_controls(car: Car) -> void:
	enter_button.visible = false
	for c in talk_box.get_children():
		c.queue_free()
	for npc_id in car.visible_npc_ids():
		var b := Button.new()
		var node: NpcNode = car.npcs[npc_id]
		b.text = ctx.texts.t("ui.debug.talk", {"name": ctx.texts.t(str(node.def.get("name_key", "")))})
		b.pressed.connect(func(): talk_requested.emit(npc_id))
		talk_box.add_child(b)
	for item_id in car.items.keys():
		var def: Dictionary = car.items[item_id]
		if not def.get("takeable", false):
			continue
		var ib := Button.new()
		ib.text = ctx.texts.t("ui.debug.take", {"name": ctx.texts.t(str(def.get("name_key", "")))})
		ib.pressed.connect(func(): take_requested.emit(String(item_id)))
		talk_box.add_child(ib)


func show_enter_car() -> void:
	enter_button.visible = true
