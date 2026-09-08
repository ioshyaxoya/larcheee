class_name TrialUi
extends Control
## Испытание Шани: аргумент, ремарка, варианты. Перед аргументом с проверкой —
## удар в такт (PerformanceUi): попал — видимый +2, мимо — −2. Шкала — часы.

var ctx: GameContext
var trial: TrialRuntime
var rhythm_bar: ProgressBar
var title_label: Label
var argument_label: RichTextLabel
var stage_label: Label
var hours_label: Label
var options_box: VBoxContainer
var flash: ColorRect
var _pending_index: int = -1
var _buttons: Array[Button] = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash = ColorRect.new()
	flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	flash.color = Color(1.0, 0.8, 0.2, 0.0)
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(flash)
	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	panel.offset_top = -320
	add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	title_label = Label.new()
	box.add_child(title_label)
	hours_label = Label.new()
	hours_label.add_theme_font_size_override("font_size", 22)
	box.add_child(hours_label)
	stage_label = Label.new()
	stage_label.modulate = Color(0.75, 0.75, 0.8)
	box.add_child(stage_label)
	argument_label = RichTextLabel.new()
	argument_label.fit_content = true
	argument_label.custom_minimum_size = Vector2(0, 60)
	box.add_child(argument_label)
	rhythm_bar = ProgressBar.new()
	rhythm_bar.max_value = 1.0
	rhythm_bar.show_percentage = false
	box.add_child(rhythm_bar)
	options_box = VBoxContainer.new()
	box.add_child(options_box)
	visible = false


func bind(context: GameContext) -> void:
	ctx = context


func attach(t: TrialRuntime) -> void:
	trial = t
	trial.round_started.connect(_on_round)
	trial.round_won.connect(func(_rd: Dictionary, k: String): _note(k))
	trial.round_lost.connect(func(_rd: Dictionary, k: String): _note(k))
	trial.gold_flash.connect(_gold)
	trial.trial_won.connect(func(_k: String): visible = false)
	trial.soft_reset.connect(func(_k: String): visible = false)
	trial.rhythm.start(Time.get_ticks_msec())
	visible = true
	title_label.text = ctx.texts.t("ui.trial.title")
	_on_round(trial.current_round(), trial.round_index)


func _process(_delta: float) -> void:
	if visible and trial != null:
		rhythm_bar.value = trial.rhythm.phase(Time.get_ticks_msec())
		if flash.color.a > 0.0:
			flash.color.a = maxf(0.0, flash.color.a - _delta * 2.0)


func _on_round(rd: Dictionary, _index: int) -> void:
	argument_label.text = ctx.texts.t(str(rd.get("argument_key", "")))
	stage_label.text = ctx.texts.t(str(rd.get("stage_key", ""))) + "\n" + ctx.texts.t(str(rd.get("find_key", "")))
	hours_label.text = ctx.texts.t("ui.trial.hours_lost", {"time": BeatClock.format_time(20 * 60 + 30 - trial.hours_lost * 60), "streak": trial.streak, "need": trial.wins_needed()})
	for b in _buttons:
		b.queue_free()
	_buttons.clear()
	for view in trial.options():
		var b := Button.new()
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		var text := ctx.texts.t(view["text_key"])
		if not (view["check"] as Dictionary).is_empty():
			text += "  [%s %s · %s]" % [ctx.texts.t(str(view["check"].get("label_key", ""))), ctx.texts.t("ui.check.dc", {"dc": view["check"].get("dc", 10)}), ctx.texts.t("ui.trial.beat")]
		b.text = text
		var idx: int = view["index"]
		var needs_beat: bool = view["needs_beat"]
		b.pressed.connect(func():
			var mod := 0
			if needs_beat:
				mod = int(trial.rhythm.judge(Time.get_ticks_msec())["modifier"])
			trial.choose(idx, mod))
		options_box.add_child(b)
		_buttons.append(b)


func _note(key: String) -> void:
	if key != "":
		argument_label.text = ctx.texts.t(key)


func _gold() -> void:
	flash.color.a = 0.9
