class_name DialogueUi
extends Control
## Панель диалога: говорящий, ремарка (stage), реплика, варианты с ценой
## в минутах — цена видна до выбора. Узел без вариантов продолжается кнопкой.

var ctx: GameContext
var runtime: DialogueRuntime
var speaker_label: Label
var stage_label: Label
var text_label: RichTextLabel
var options_box: VBoxContainer
var option_buttons: Array[Button] = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	panel.offset_top = -260
	add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	speaker_label = Label.new()
	speaker_label.add_theme_font_size_override("font_size", 20)
	box.add_child(speaker_label)
	stage_label = Label.new()
	stage_label.modulate = Color(0.75, 0.75, 0.8)
	box.add_child(stage_label)
	text_label = RichTextLabel.new()
	text_label.bbcode_enabled = false
	text_label.fit_content = true
	text_label.custom_minimum_size = Vector2(0, 70)
	box.add_child(text_label)
	options_box = VBoxContainer.new()
	box.add_child(options_box)
	visible = false


func bind(context: GameContext) -> void:
	ctx = context


func attach(rt: DialogueRuntime) -> void:
	runtime = rt
	rt.node_entered.connect(_on_node)
	rt.ended.connect(_on_ended)
	visible = true
	if not rt.current.is_empty():
		_on_node(rt.current_id, rt.current)


func _on_node(_node_id: String, node: Dictionary) -> void:
	var speaker_key := runtime.speaker_name_key(node)
	speaker_label.text = ctx.texts.t(speaker_key) if speaker_key != "" else ""
	stage_label.text = ctx.texts.t(str(node["stage"])) if node.has("stage") else ""
	stage_label.visible = node.has("stage")
	var params := {"now": ctx.clock.now_string(), "late": ctx.clock.minutes_late(), "name": ctx.character.display_name if ctx.character else ""}
	text_label.text = ctx.texts.t(str(node.get("text_key", "")), params)
	_rebuild_options()


func _rebuild_options() -> void:
	for b in option_buttons:
		b.queue_free()
	option_buttons.clear()
	if runtime.finished:
		return
	if runtime.has_options():
		for view in runtime.available_options():
			var b := Button.new()
			b.text = option_caption(view)
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			var idx: int = view["index"]
			b.pressed.connect(func(): runtime.choose(idx))
			options_box.add_child(b)
			option_buttons.append(b)
	else:
		var b := Button.new()
		b.text = ctx.texts.t("ui.check.continue")
		b.pressed.connect(func(): runtime.advance())
		options_box.add_child(b)
		option_buttons.append(b)


## Подпись варианта: текст + цена в минутах (+ цена провала, + шанс и надбавка).
func option_caption(view: Dictionary) -> String:
	var parts: PackedStringArray = [ctx.texts.t(view["text_key"])]
	var tail: PackedStringArray = []
	if int(view["cost_minutes"]) > 0 or not (view["check"] as Dictionary).is_empty():
		tail.append(ctx.texts.t("ui.cost.minutes", {"minutes": view["cost_minutes"]}))
	if not (view["check"] as Dictionary).is_empty():
		var chk: Dictionary = view["check"]
		tail.append("%s %s" % [ctx.texts.t(str(chk.get("label_key", ""))), ctx.texts.t("ui.check.dc", {"dc": chk.get("dc", 10)})])
		if int(view["cost_on_fail_minutes"]) != int(view["cost_minutes"]):
			tail.append(ctx.texts.t("ui.cost.on_fail", {"minutes": view["cost_on_fail_minutes"]}))
	if not (view["chance"] as Dictionary).is_empty():
		tail.append(ctx.texts.t("ui.chance.percent", {"percent": int(round(float(view["probability"]) * 100))}))
		if int(view["hit_minutes"]) > 0:
			tail.append(ctx.texts.t("ui.cost.hit_more", {"minutes": view["hit_minutes"]}))
	if String(view["cost_note_key"]) != "":
		tail.append(ctx.texts.t(view["cost_note_key"]))
	if not tail.is_empty():
		parts.append("[" + " · ".join(tail) + "]")
	return "  ".join(parts)


func _on_ended() -> void:
	for b in option_buttons:
		b.queue_free()
	option_buttons.clear()
	visible = false
