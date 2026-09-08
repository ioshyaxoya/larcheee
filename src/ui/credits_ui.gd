class_name CreditsUi
extends Control
## Титры концовки. Настоящие: строки концовки, авторы, атрибуция SRD 5.2 (CC-BY-4.0).

signal closed

var ctx: GameContext
var label: RichTextLabel
var title_label: Label
var back_button: Button


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0, 0, 0, 1)
	add_child(bg)
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	add_child(box)
	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 36)
	box.add_child(title_label)
	label = RichTextLabel.new()
	label.fit_content = true
	label.custom_minimum_size = Vector2(700, 300)
	box.add_child(label)
	back_button = Button.new()
	back_button.pressed.connect(func():
		visible = false
		closed.emit())
	box.add_child(back_button)
	visible = false


func bind(context: GameContext) -> void:
	ctx = context
	back_button.text = ctx.texts.t("ui.credits.back")


func show_ending(def: Dictionary, endings: Endings) -> void:
	title_label.text = ctx.texts.t(str(def.get("title_key", "")))
	label.text = "\n\n".join(endings.credits_lines(def))
	visible = true
