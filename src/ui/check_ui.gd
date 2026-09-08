class_name CheckUi
extends Control
## Видимая проверка d20 (B5): кубик на экране, каждый модификатор раскрыт,
## СЛ и итог, провал не прячется. Показывается на каждый бросок Checks.

signal dismissed

var ctx: GameContext
var panel: PanelContainer
var title_label: Label
var die_label: Label
var mods_label: Label
var total_label: Label
var outcome_label: Label
var continue_button: Button
var last: CheckResult = null


func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel = PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.custom_minimum_size = Vector2(360, 240)
	add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	title_label = Label.new()
	box.add_child(title_label)
	die_label = Label.new()
	die_label.add_theme_font_size_override("font_size", 64)
	die_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(die_label)
	mods_label = Label.new()
	box.add_child(mods_label)
	total_label = Label.new()
	box.add_child(total_label)
	outcome_label = Label.new()
	outcome_label.add_theme_font_size_override("font_size", 28)
	box.add_child(outcome_label)
	continue_button = Button.new()
	continue_button.pressed.connect(hide_result)
	box.add_child(continue_button)
	visible = false


func bind(context: GameContext) -> void:
	ctx = context
	ctx.checks.check_rolled.connect(show_result)
	continue_button.text = ctx.texts.t("ui.check.continue")


func show_result(r: CheckResult) -> void:
	last = r
	var label := ctx.texts.t(r.label_key) if r.label_key != "" else ""
	if r.kind == "chance":
		title_label.text = ctx.texts.t("ui.check.chance_title", {"label": label}) + "  " + ctx.texts.t("ui.chance.percent", {"percent": int(round(r.probability * 100))})
	else:
		title_label.text = ctx.texts.t("ui.check.title", {"label": label})
	die_label.text = str(r.die)
	var lines: PackedStringArray = []
	for m in r.modifiers:
		var v := int(m["value"])
		if r.kind == "chance":
			lines.append("%s ≤ %d" % [CheckResult.modifier_label(m, ctx.texts), r.threshold])
		else:
			lines.append("%s %s%d" % [CheckResult.modifier_label(m, ctx.texts), "+" if v >= 0 else "", v])
	mods_label.text = "\n".join(lines)
	total_label.text = ctx.texts.t("ui.check.total", {"total": r.total}) + "  ·  " + ctx.texts.t("ui.check.dc", {"dc": r.dc})
	var outcome := ctx.texts.t("ui.check.success" if r.success else "ui.check.fail")
	if r.natural_20:
		outcome += " — " + ctx.texts.t("ui.check.crit_success")
	elif r.natural_1:
		outcome += " — " + ctx.texts.t("ui.check.crit_fail")
	outcome_label.text = outcome
	outcome_label.modulate = Color(0.6, 1.0, 0.6) if r.success else Color(1.0, 0.5, 0.45)
	visible = true


func hide_result() -> void:
	visible = false
	dismissed.emit()
