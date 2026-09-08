class_name DialogueUi
extends Control
## Панель диалога: говорящий, ремарка (stage), реплика, варианты с ценой
## в минутах — цена видна до выбора. Узел без вариантов продолжается кнопкой.

var ctx: GameContext
var runtime: DialogueRuntime
var speaker_label: Label
var stage_label: Label
var text_label: RichTextLabel
# Реплика набирается по буквам, а варианты появляются, когда она дописана.
# В диалоговой игре это единственное движение, которое есть в каждом кадре, и
# оно же задаёт темп чтения: читатель не получает стену текста целиком.
var typing := false
var type_speed := 46.0          # знаков в секунду
var _typed := 0.0
var _pending_options := false
var options_box: VBoxContainer
var option_buttons: Array[Button] = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Панель прижата к низу и растёт по содержимому: сколько вариантов, столько высоты.
	var column := VBoxContainer.new()
	column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.alignment = BoxContainer.ALIGNMENT_END
	add_child(column)
	var panel := PanelContainer.new()
	panel.size_flags_vertical = Control.SIZE_SHRINK_END
	column.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 28)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_bottom", 14)
	panel.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	margin.add_child(box)
	speaker_label = Label.new()
	speaker_label.add_theme_font_override("font", GameTheme.clock_font())
	speaker_label.add_theme_font_size_override("font_size", 19)
	speaker_label.add_theme_color_override("font_color", GameTheme.GOLD)
	box.add_child(speaker_label)
	stage_label = Label.new()
	stage_label.add_theme_font_override("font", GameTheme.stage_font())
	stage_label.add_theme_color_override("font_color", GameTheme.TEXT_DIM)
	stage_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(stage_label)
	text_label = RichTextLabel.new()
	text_label.bbcode_enabled = false
	text_label.add_theme_font_size_override("normal_font_size", 19)
	text_label.fit_content = true
	text_label.custom_minimum_size = Vector2(0, 56)
	box.add_child(text_label)
	options_box = VBoxContainer.new()
	options_box.add_theme_constant_override("separation", 1)
	box.add_child(options_box)
	visible = false


func bind(context: GameContext) -> void:
	ctx = context


## Прицепить граф. Сигналы предыдущего отцепляются: иначе его `ended`
## погасит панель уже после того, как показан новый граф.
func attach(rt: DialogueRuntime) -> void:
	if rt == null:
		return
	detach()
	runtime = rt
	rt.node_entered.connect(_on_node)
	rt.ended.connect(_on_ended.bind(rt))
	visible = true
	if not rt.current.is_empty():
		_on_node(rt.current_id, rt.current)
	elif rt.finished:
		_on_ended(rt)


func detach() -> void:
	if runtime == null:
		return
	if runtime.node_entered.is_connected(_on_node):
		runtime.node_entered.disconnect(_on_node)
	var bound := _on_ended.bind(runtime)
	if runtime.ended.is_connected(bound):
		runtime.ended.disconnect(bound)
	runtime = null


func _on_node(_node_id: String, node: Dictionary) -> void:
	if runtime == null:
		return
	var speaker_key := runtime.speaker_name_key(node)
	speaker_label.text = ctx.texts.t(speaker_key) if speaker_key != "" else ""
	stage_label.text = ctx.texts.t(str(node["stage"])) if node.has("stage") else ""
	stage_label.visible = node.has("stage")
	var params := {"now": ctx.clock.now_string(), "late": ctx.clock.minutes_late(), "name": ctx.character.display_name if ctx.character else ""}
	text_label.text = ctx.texts.t(str(node.get("text_key", "")), params)
	_start_typing()


## Начать набор реплики. Варианты придут, когда текст дописан.
func _start_typing() -> void:
	_typed = 0.0
	text_label.visible_characters = 0
	typing = text_label.get_total_character_count() > 0
	_pending_options = true
	if not typing:
		_finish_typing()


## Досказать сразу: щелчок или пробел не должны ждать машинку.
func skip_typing() -> void:
	if typing:
		_finish_typing()


func _finish_typing() -> void:
	typing = false
	text_label.visible_characters = -1
	if _pending_options:
		_pending_options = false
		_rebuild_options()


func _process(delta: float) -> void:
	if not typing:
		return
	_typed += delta * type_speed
	var total := text_label.get_total_character_count()
	text_label.visible_characters = int(min(_typed, float(total)))
	if _typed >= float(total):
		_finish_typing()


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
			b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			var idx: int = view["index"]
			b.pressed.connect(func(): runtime.choose(idx))
			options_box.add_child(b)
			option_buttons.append(b)
	else:
		var b := Button.new()
		b.text = ctx.texts.t("ui.check.continue")
		b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
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


func _on_ended(which: DialogueRuntime) -> void:
	if which != runtime:
		return   # граф уже сменился: панель принадлежит новому
	for b in option_buttons:
		b.queue_free()
	option_buttons.clear()
	visible = false
