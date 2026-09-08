class_name StageMotion
extends Node
## Движение постановки. Задаётся данными, как и сама постановка: у кулисы,
## предмета, фигуры или лужи света может быть блок `motion`.
##
## Почему не AnimationPlayer: анимировать надо сорок вагонов и восемь
## присутствий, и делать это должен автор данных, а не кодер сценами. Здесь
## только несколько видов вечного движения — того, которое идёт всегда и
## говорит «поезд едет», а не постановочные сцены.
##
## Виды:
##   sway    — качание по осям: amp (метры), period (секунды), phase
##   bob     — то же, но по синусу вверх-вниз; удобнее читать в данных
##   pace    — расхаживание: медленно туда-обратно, с разворотом на концах
##   flicker — мигание яркости: min, max, period (для пламени и лужи света)
##   scroll  — равномерный сдвиг: speed (метры в секунду) с возвратом по loop
##   turn    — поворот по осям: amp (градусы), period
##
## Всё считается от базового положения, записанного при сборке, поэтому
## движение не накапливает дрейф и не спорит с данными. На один узел можно
## положить несколько движений (`motion` — список): смещения складываются, а
## не спорят друг с другом. Так ворон расхаживает и одновременно поводит
## головой, не требуя вложенных узлов.

class Item:
	var node: Node3D
	var base_pos: Vector3
	var base_rot: Vector3
	var kind := ""
	var amp := Vector3.ZERO
	var rot_amp := Vector3.ZERO
	var period := 3.0
	var phase := 0.0
	var lo := 0.8
	var hi := 1.0
	var speed := Vector3.ZERO
	var loop := 0.0
	var base_alpha := 1.0
	var material: StandardMaterial3D = null


var items: Array[Item] = []
var time := 0.0


## Добавить узел с блоком `motion` из данных. Без блока — ничего не делает.
## `motion` — словарь или список словарей.
func add(node: Node3D, def: Dictionary) -> void:
	var raw = def.get("motion", {})
	if raw is Array:
		for one in raw:
			_add_one(node, one as Dictionary)
	elif raw is Dictionary and not (raw as Dictionary).is_empty():
		_add_one(node, raw as Dictionary)


func _add_one(node: Node3D, m: Dictionary) -> void:
	if m.is_empty():
		return
	var it := Item.new()
	it.node = node
	it.base_pos = node.position
	it.base_rot = node.rotation_degrees
	it.kind = str(m.get("kind", "sway"))
	it.amp = _vec(m.get("amp", [0.0, 0.0, 0.0]))
	it.rot_amp = _vec(m.get("rot_amp", [0.0, 0.0, 0.0]))
	it.period = maxf(0.05, float(m.get("period", 3.0)))
	it.phase = float(m.get("phase", 0.0))
	it.lo = float(m.get("min", 0.8))
	it.hi = float(m.get("max", 1.0))
	it.speed = _vec(m.get("speed", [0.0, 0.0, 0.0]))
	it.loop = float(m.get("loop", 0.0))
	if node is MeshInstance3D:
		var mat = (node as MeshInstance3D).material_override
		if mat is StandardMaterial3D:
			it.material = mat
			it.base_alpha = mat.albedo_color.a
	items.append(it)


static func _vec(v) -> Vector3:
	var a: Array = v if v is Array else [0.0, 0.0, 0.0]
	while a.size() < 3:
		a.append(0.0)
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _process(delta: float) -> void:
	time += delta
	# Смещения складываются по узлу и применяются один раз: иначе два движения
	# на одном узле затирают друг друга, и второе просто не видно.
	var pos_shift := {}
	var rot_shift := {}
	for it in items:
		var t := TAU * (time / it.period + it.phase)
		var dp := Vector3.ZERO
		var dr := Vector3.ZERO
		match it.kind:
			"sway", "bob":
				dp = it.amp * sin(t)
				dr = it.rot_amp * sin(t)
			"pace":
				# Расхаживание: не синус, а ход с задержкой на концах — птица
				# доходит, останавливается, поворачивается и идёт назад.
				var s := sin(t)
				dp = it.amp * (signf(s) * pow(absf(s), 0.55))
				dr = it.rot_amp * cos(t)
			"turn":
				dr = it.rot_amp * sin(t)
			"scroll":
				dp = it.speed * time
				if it.loop > 0.0 and it.speed.length() > 0.0:
					dp = it.speed.normalized() * fmod(dp.length(), it.loop)
			"flicker":
				# Пламя не синусоида: две несовпадающие волны.
				var f := 0.5 + 0.5 * (0.62 * sin(t) + 0.38 * sin(t * 2.7 + 1.3))
				var k := it.lo + (it.hi - it.lo) * f
				if it.material != null:
					var c := it.material.albedo_color
					c.a = it.base_alpha * k
					it.material.albedo_color = c
				else:
					it.node.scale = Vector3.ONE * (0.94 + 0.06 * k)
		if dp != Vector3.ZERO or dr != Vector3.ZERO:
			var key := it.node.get_instance_id()
			pos_shift[key] = pos_shift.get(key, Vector3.ZERO) + dp
			rot_shift[key] = rot_shift.get(key, Vector3.ZERO) + dr
	for it in items:
		var key := it.node.get_instance_id()
		if pos_shift.has(key):
			it.node.position = it.base_pos + pos_shift[key]
		if rot_shift.has(key):
			it.node.rotation_degrees = it.base_rot + rot_shift[key]
