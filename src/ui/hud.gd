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
	set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var box := VBoxContainer.new()
	box.position = Vector2(16, 16)
	add_child(box)
	clock_label = Label.new()
	clock_label.add_theme_font_size_override("font_size", 40)
	box.add_child(clock_label)
	train_label = Label.new()
	box.add_child(train_label)
	money_label = Label.new()
	box.add_child(money_label)
	log_label = Label.new()
	log_label.modulate = Color(1, 0.85, 0.6)
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


func _on_time_spent(minutes: int, reason_key: String, _now: int) -> void:
	var reason := ctx.texts.t(reason_key) if reason_key != "" else ""
	_entries.append(ctx.texts.t("ui.clock.spent", {"minutes": minutes, "reason": reason}))
	while _entries.size() > 4:
		_entries.pop_front()
	refresh()
