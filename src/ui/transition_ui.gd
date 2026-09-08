class_name TransitionUi
extends Control
## Ритуал перелезания: шаг за шагом, без бросков. Пропуск — после первого просмотра варианта.

var ctx: GameContext
var runtime: TransitionRuntime
var label: RichTextLabel
var skip_button: Button
var next_button: Button
var timer: SceneTreeTimer


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.02, 0.05, 0.92)
	add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["margin_left", "margin_right"]:
		margin.add_theme_constant_override(side, 160)
	for side in ["margin_top", "margin_bottom"]:
		margin.add_theme_constant_override(side, 200)
	add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 16)
	margin.add_child(box)
	label = RichTextLabel.new()
	label.fit_content = true
	box.add_child(label)
	next_button = Button.new()
	next_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	next_button.pressed.connect(func(): if runtime: runtime.next_step())
	box.add_child(next_button)
	skip_button = Button.new()
	skip_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	skip_button.pressed.connect(func(): if runtime: runtime.skip())
	box.add_child(skip_button)
	visible = false


func bind(context: GameContext) -> void:
	ctx = context
	next_button.text = ctx.texts.t("ui.check.continue")
	skip_button.text = ctx.texts.t("ui.transition.skip")


func attach(rt: TransitionRuntime) -> void:
	runtime = rt
	rt.step.connect(func(k: String, _s: float, _i: int):
		label.text = ctx.texts.t(k)
		skip_button.visible = rt.can_skip())
	rt.finished.connect(func(_v: String): visible = false)
	visible = true
