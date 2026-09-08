class_name WalkMap
extends RefCounted
## Проходимость вагона из данных карточки (`car.walk`).
##
## Сетка вагона объявлена в карточке (`grid: 18×46`, уровни floor и gallery) и
## описана зонами в docs/car_01_brake_van.md §2: тамбур, пост кондуктора,
## багажный корпус, глубина. Здесь она превращается в метры: куда можно
## ступить, где стоит вещь, в какой зоне игрок сейчас — и какой кадр в этой
## зоне берёт камера.
##
## Клетка — не шаг игрока: игрок ходит непрерывно, а сетка нужна для
## проходимости, зон и авторской привязки предметов.

var cell := Vector2(0.32, 0.52)     # метры на клетку по X и по Z
var origin := Vector3(-2.72, 0.0, 1.6)
var size := Vector2i(18, 46)
var half_width := 2.52              # до чего можно дойти к стене
var spawn := Vector3.ZERO
var blocked: Array = []             # прямоугольники в метрах: [x0, z0, x1, z1]
var zones: Array = []               # {id, from, to, camera}


static func from_card(card: Dictionary) -> WalkMap:
	var m := WalkMap.new()
	var w: Dictionary = card.get("walk", {})
	var grid: Dictionary = card.get("grid", {})
	m.size = Vector2i(int(grid.get("w", 18)), int(grid.get("h", 46)))
	if w.has("cell"):
		m.cell = Vector2(float(w["cell"][0]), float(w["cell"][1]))
	if w.has("origin"):
		m.origin = Vector3(float(w["origin"][0]), float(w["origin"][1]), float(w["origin"][2]))
	m.half_width = float(w.get("half_width", 2.52))
	m.blocked = w.get("blocked", [])
	m.zones = w.get("zones", [])
	var sp: Array = w.get("spawn", [9, 3])
	m.spawn = m.to_metres(int(sp[0]), int(sp[1]))
	return m


## Клетка → метры (центр клетки).
func to_metres(cx: int, cz: int) -> Vector3:
	return Vector3(origin.x + (float(cx) + 0.5) * cell.x, origin.y,
		origin.z - (float(cz) + 0.5) * cell.y)


func to_cell(pos: Vector3) -> Vector2i:
	return Vector2i(int(floor((pos.x - origin.x) / cell.x)),
		int(floor((origin.z - pos.z) / cell.y)))


## Можно ли стоять в этой точке. Стены — по половине ширины, вещи — по
## прямоугольникам из данных: их считает рисовальный скрипт по самим контурам,
## поэтому проходимость не расходится с тем, что нарисовано.
func walkable(pos: Vector3) -> bool:
	if absf(pos.x) > half_width:
		return false
	var cz := (origin.z - pos.z) / cell.y
	if cz < 0.0 or cz > float(size.y):
		return false
	for r in blocked:
		if pos.x > float(r[0]) and pos.x < float(r[2]) \
				and pos.z > float(r[1]) and pos.z < float(r[3]):
			return false
	return true


## Зона, в которой игрок стоит: по ней камера берёт свой кадр.
func zone_at(pos: Vector3) -> Dictionary:
	var cz := int((origin.z - pos.z) / cell.y)
	for z in zones:
		if cz >= int((z as Dictionary).get("from", 0)) and cz <= int((z as Dictionary).get("to", 0)):
			return z
	return {}
