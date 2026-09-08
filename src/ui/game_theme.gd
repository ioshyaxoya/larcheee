class_name GameTheme
extends RefCounted
## Тема интерфейса: IBM Plex Sans, тёмный грунт, тёплый текст, одна золотая
## акцентная линия. Плоские кнопки без хрома — интерфейс не спорит со сценой
## (docs/visual_direction.md §3: свет делает работу).

const FONT_REGULAR := "res://assets/fonts/IBMPlexSans-Regular.ttf"
const FONT_LIGHT := "res://assets/fonts/IBMPlexSans-Light.ttf"
const FONT_SEMIBOLD := "res://assets/fonts/IBMPlexSans-SemiBold.ttf"

const INK := Color(0.043, 0.043, 0.055, 0.94)      # грунт панели
const TEXT := Color(0.90, 0.88, 0.84)              # тёплый off-white
const TEXT_DIM := Color(0.62, 0.60, 0.58)          # ремарки
const GOLD := Color(1.0, 0.78, 0.28)               # акцент: одна линия, одна вспышка
const GOLD_DIM := Color(0.55, 0.42, 0.16)


static func font(path: String) -> Font:
	var f = load(path)
	return f if f is Font else ThemeDB.fallback_font


static func build() -> Theme:
	var theme := Theme.new()
	var regular := font(FONT_REGULAR)
	theme.default_font = regular
	theme.default_font_size = 17

	# Панели: грунт и тонкая золотая линия сверху — рампа сцены.
	var panel := StyleBoxFlat.new()
	panel.bg_color = INK
	panel.border_width_top = 1
	panel.border_color = GOLD_DIM
	panel.content_margin_left = 0
	panel.content_margin_right = 0
	panel.content_margin_top = 0
	panel.content_margin_bottom = 0
	theme.set_stylebox("panel", "PanelContainer", panel)
	theme.set_stylebox("panel", "Panel", panel)

	# Кнопки-варианты: без рамок, слева золотая метка при наведении.
	var empty := StyleBoxEmpty.new()
	empty.content_margin_left = 12
	empty.content_margin_right = 12
	empty.content_margin_top = 3
	empty.content_margin_bottom = 3
	var hover := StyleBoxFlat.new()
	hover.bg_color = Color(1.0, 0.78, 0.28, 0.08)
	hover.border_width_left = 2
	hover.border_color = GOLD
	hover.content_margin_left = 10
	hover.content_margin_right = 12
	hover.content_margin_top = 3
	hover.content_margin_bottom = 3
	var pressed := hover.duplicate() as StyleBoxFlat
	pressed.bg_color = Color(1.0, 0.78, 0.28, 0.16)
	theme.set_stylebox("normal", "Button", empty)
	theme.set_stylebox("hover", "Button", hover)
	theme.set_stylebox("pressed", "Button", pressed)
	theme.set_stylebox("focus", "Button", empty)
	theme.set_stylebox("disabled", "Button", empty)
	theme.set_color("font_color", "Button", TEXT)
	theme.set_color("font_hover_color", "Button", Color(1.0, 0.93, 0.78))
	theme.set_color("font_pressed_color", "Button", GOLD)
	theme.set_color("font_disabled_color", "Button", TEXT_DIM)

	theme.set_color("font_color", "Label", TEXT)
	theme.set_color("default_color", "RichTextLabel", TEXT)
	theme.set_font("normal_font", "RichTextLabel", regular)
	theme.set_constant("line_separation", "RichTextLabel", 4)

	# Шкала ритма: тонкая золотая полоса.
	var bar_bg := StyleBoxFlat.new()
	bar_bg.bg_color = Color(1, 1, 1, 0.08)
	bar_bg.content_margin_top = 0
	bar_bg.content_margin_bottom = 0
	var bar_fill := StyleBoxFlat.new()
	bar_fill.bg_color = GOLD_DIM
	theme.set_stylebox("background", "ProgressBar", bar_bg)
	theme.set_stylebox("fill", "ProgressBar", bar_fill)

	# Служебные элементы панели разработчика — тише основного текста.
	for control in ["OptionButton", "SpinBox", "CheckBox", "LineEdit"]:
		theme.set_color("font_color", control, TEXT_DIM)
	return theme


## Крупный шрифт для часов и титров: моно-цифры не пляшут.
static func clock_font() -> Font:
	return font(FONT_SEMIBOLD)


static func stage_font() -> Font:
	return font(FONT_LIGHT)
