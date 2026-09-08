class_name PlayerNode
extends Node3D
## Игрок в вагоне: ходит, шагает ногами, не проходит сквозь вещи.
##
## Фигура — шарнирная вырезка (visual_direction §3): корпус, две ноги, две
## руки, каждая со своей точкой вращения. Шаг — не перерисовка кадров, а
## поворот бёдер и плеч вокруг этих точек, поэтому «анимация» здесь дешёвая и
## одна на всех персонажей.
##
## Ходьба непрерывная, а не по клеткам: сетка вагона нужна для проходимости,
## зон и предметов, а не для шага.

signal moved(pos: Vector3)
signal facing_changed(facing: int)

const DIR := "res://data/player.json"

var walk: WalkMap
var speed := 1.9                 # метры в секунду
var facing := 1                  # 1 — вправо, -1 — влево
var locked := false
var _groups: Array = []          # {node, pivot, swing}
var _shadow: Node3D
var _phase := 0.0
var _moving := false
var _body_root: Node3D


func setup(map: WalkMap) -> void:
	walk = map
	position = map.spawn
	if DisplayServer.get_name() == "headless":
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(DIR))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("PlayerNode: не читается %s" % DIR)
		return
	var doc: Dictionary = parsed
	_body_root = Node3D.new()
	_body_root.name = "Figure"
	add_child(_body_root)
	if doc.has("ground_shadow"):
		_shadow = StageBuilder.polygon({"id": "shadow", "parts": [doc["ground_shadow"]]})
		_body_root.add_child(_shadow)
	for g in doc.get("groups", []):
		var def: Dictionary = g
		var pivot: Array = def.get("pivot", [0.0, 0.0, 0.0])
		var holder := Node3D.new()
		holder.name = str(def.get("id", "group"))
		holder.position = Vector3(float(pivot[0]), float(pivot[1]), float(def.get("z", 0.0)))
		_body_root.add_child(holder)
		# Контуры нарисованы от точки вращения, поэтому внутри держателя
		# они ложатся со сдвигом обратно — так поворот идёт вокруг бедра.
		var inner := StageBuilder.polygon({"id": "parts", "parts": def.get("parts", [])})
		inner.position = Vector3(-float(pivot[0]), -float(pivot[1]), 0.0)
		holder.add_child(inner)
		_groups.append({"node": holder, "swing": def.get("swing", {})})


func _process(delta: float) -> void:
	var dir := 0.0
	var fwd := 0.0
	if not locked:
		dir = Input.get_axis("ui_left", "ui_right")
		fwd = Input.get_axis("ui_down", "ui_up")
	_moving = absf(dir) > 0.01 or absf(fwd) > 0.01
	if _moving:
		var step := Vector3(dir, 0.0, -fwd).normalized() * speed * delta
		var want := position + step
		# Оси проверяются отдельно: вдоль стены и вдоль вещи можно скользить,
		# иначе игрок липнет к каждому углу.
		if walk.walkable(Vector3(want.x, position.y, position.z)):
			position.x = want.x
		if walk.walkable(Vector3(position.x, position.y, want.z)):
			position.z = want.z
		if absf(dir) > 0.01 and signf(dir) != float(facing):
			facing = int(signf(dir))
			facing_changed.emit(facing)
			if _body_root != null:
				_body_root.scale.x = float(facing)
		moved.emit(position)
		_phase += delta * speed * 2.6
	else:
		# Стоя фигура возвращается в покой, а не замирает в шаге.
		_phase = lerpf(_phase, round(_phase / TAU) * TAU, minf(1.0, delta * 8.0))
	_pose()


## Поза: бёдра и плечи качаются в противофазе, корпус чуть подпрыгивает.
func _pose() -> void:
	var walking := _moving
	for g in _groups:
		var swing: Dictionary = g["swing"]
		if swing.is_empty():
			continue
		var amp := float(swing.get("amp", 20.0)) * (1.0 if walking else 0.12)
		var ph := float(swing.get("phase", 0.0))
		(g["node"] as Node3D).rotation_degrees.z = amp * sin(_phase + ph * TAU)
	if _body_root != null:
		var bob := 0.018 * absf(sin(_phase)) if walking else 0.0
		_body_root.position.y = bob
		if _shadow != null:
			_shadow.scale = Vector3(1.0 - bob * 1.4, 1.0, 1.0)
