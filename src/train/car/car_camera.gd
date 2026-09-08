class_name CarCamera
extends Node
## Камера вагона: идёт за игроком и меняет кадр по зонам.
##
## Кадр не один на весь вагон: в тамбуре тесно, на посту кондуктора рабочий
## план, багажный корпус длинный, в глубине камера подходит ближе и опускается
## — там кончается свет (docs/car_01_brake_van.md §2). Параметры зон лежат в
## данных (`car.walk.zones[].camera`), а не в коде: их правит автор вагона.
##
## Смена кадра не мгновенная: камера доводит себя до нового плана, иначе
## переход между зонами читается рывком.

var camera: Camera3D
var map: WalkMap
var target := Vector3.ZERO
var facing := 1
var follow := 6.0            # скорость доводки положения
var frame_follow := 1.6      # скорость доводки самого кадра
var _height := 1.70
var _back := 4.6
var _pitch := -5.0
var _fov := 38.0
var _lead := 0.4
var _zone := ""


func bind(cam: Camera3D, walk_map: WalkMap) -> void:
	camera = cam
	map = walk_map
	target = walk_map.spawn
	_snap_frame(walk_map.zone_at(target))
	camera.position = _wanted_pos()
	camera.rotation_degrees = Vector3(_pitch, 0.0, 0.0)


func set_target(pos: Vector3) -> void:
	target = pos


func set_facing(f: int) -> void:
	facing = f


func _snap_frame(zone: Dictionary) -> void:
	var c: Dictionary = zone.get("camera", {})
	_height = float(c.get("height", _height))
	_back = float(c.get("back", _back))
	_pitch = float(c.get("pitch", _pitch))
	_fov = float(c.get("fov", _fov))
	_lead = float(c.get("lead", _lead))
	_zone = str(zone.get("id", ""))


func _wanted_pos() -> Vector3:
	# Камера смотрит вдоль вагона, поэтому за игроком идёт по z, а по x только
	# ведёт: полностью повторять шаги влево-вправо — укачивать зрителя.
	return Vector3(target.x * 0.34 + float(facing) * _lead * 0.5,
		_height, target.z + _back)


func _process(delta: float) -> void:
	if camera == null or map == null:
		return
	var zone := map.zone_at(target)
	var zid := str(zone.get("id", ""))
	if zid != _zone and not zone.is_empty():
		var c: Dictionary = zone.get("camera", {})
		# Кадр доводится, а не переставляется: рывок между зонами заметен.
		_height = lerpf(_height, float(c.get("height", _height)), minf(1.0, delta * frame_follow))
		_back = lerpf(_back, float(c.get("back", _back)), minf(1.0, delta * frame_follow))
		_pitch = lerpf(_pitch, float(c.get("pitch", _pitch)), minf(1.0, delta * frame_follow))
		_fov = lerpf(_fov, float(c.get("fov", _fov)), minf(1.0, delta * frame_follow))
		_lead = lerpf(_lead, float(c.get("lead", _lead)), minf(1.0, delta * frame_follow))
		if absf(_back - float(c.get("back", _back))) < 0.02:
			_zone = zid
	var k := minf(1.0, delta * follow)
	camera.position = camera.position.lerp(_wanted_pos(), k)
	camera.rotation_degrees.x = lerpf(camera.rotation_degrees.x, _pitch, k)
	if camera.projection == Camera3D.PROJECTION_PERSPECTIVE:
		camera.fov = lerpf(camera.fov, _fov, k)


func zone_id() -> String:
	return _zone
