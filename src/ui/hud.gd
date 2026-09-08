class_name Hud
extends Control
## HUD: битовые часы (сейчас / поезд), деньги, журнал потерь времени.
## Каждая потеря показывается в минутах в момент потери (столп 3).

var ctx: GameContext
var clock_label: Label
var train_label: Label
var money_label: Label
var log_label: Label
var _entries: Array[String] = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Мягкая тень под текстом: HUD лежит прямо на кадре и должен читаться
	# и в монохроме испытания, и на светлой луже.
	var scrim := TextureRect.new()
	scrim.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	scrim.size = Vector2(520, 380)
	scrim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 1.0])
	grad.colors = PackedColorArray([Color(0.02, 0.02, 0.03, 0.85), Color(0.02, 0.02, 0.03, 0.0)])
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.12, 0.1)
	tex.fill_to = Vector2(1.0, 0.9)
	tex.width = 256
	tex.height = 256
	scrim.texture = tex
	scrim.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	add_child(scrim)
	var box := VBoxContainer.new()
	box.position = Vector2(28, 24)
	box.add_theme_constant_override("separation", 2)
	add_child(box)
	clock_label = Label.new()
	clock_label.add_theme_font_override("font", GameTheme.clock_font())
	clock_label.add_theme_font_size_override("font_size", 44)
	clock_label.add_theme_color_override("font_color", GameTheme.TEXT)
	box.add_child(clock_label)
	train_label = Label.new()
	train_label.add_theme_color_override("font_color", GameTheme.TEXT_DIM)
	box.add_child(train_label)
	money_label = Label.new()
	money_label.add_theme_color_override("font_color", GameTheme.TEXT_DIM)
	box.add_child(money_label)
	log_label = Label.new()
	log_label.add_theme_font_override("font", GameTheme.stage_font())
	log_label.add_theme_color_override("font_color", GameTheme.GOLD)
	box.add_child(log_label)


func bind(context: GameContext) -> void:
	ctx = context
	ctx.clock.time_spent.connect(_on_time_spent)
	refresh()


func refresh() -> void:
	if ctx == null:
		return
	clock_label.text = ctx.texts.t("ui.clock.now", {"now": ctx.clock.now_string()})
	train_label.text = ctx.texts.t("ui.clock.train")
	money_label.text = ctx.texts.t("ui.money", {"money": ctx.world.money})
	log_label.text = "\n".join(_entries)


## Забыть журнал минут: пролог кончился, и его расход больше не при чём.
## Иначе список «−7 мин — досмотр багажа» висит поверх суда Шани.
func clear_log() -> void:
	_entries.clear()
	refresh()


func _on_time_spent(minutes: int, reason_key: String, _now: int) -> void:
	var reason := ctx.texts.t(reason_key) if reason_key != "" else ""
	_entries.append(ctx.texts.t("ui.clock.spent", {"minutes": minutes, "reason": reason}))
	while _entries.size() > 4:
		_entries.pop_front()
	refresh()
