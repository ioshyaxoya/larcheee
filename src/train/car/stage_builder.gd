class_name StageBuilder
extends RefCounted
## Театральная постановка вагона (docs/visual_direction.md §3, ориентир —
## Kentucky Route Zero): плоские цветовые поля в объёме, никаких градиентов от
## источников. Свет — это форма: лужа света описана в данных как плоскость с
## аддитивным смешиванием, а не как физический светильник. Тьма по умолчанию.
##
## Всё содержимое сцены живёт в данных вагона (`car.stage`), как и остальная
## логика вагона (B5). Типы: `layers` (кулисы), `props` (реквизит),
## `pools` (лужи света).

static var _pool_texture: GradientTexture2D = null


static func build(card: Dictionary, parent: Node3D) -> void:
	var stage: Dictionary = card.get("stage", {})
	if stage.is_empty():
		return
	for layer in stage.get("layers", []):
		parent.add_child(quad(layer, false))
	for prop in stage.get("props", []):
		parent.add_child(quad(prop, false))
	for pool in stage.get("pools", []):
		parent.add_child(quad(pool, true))


## Плоскость: кулиса, реквизит или лужа света. Цвет плоский и заданный —
## то, что автор написал в данных, то и на экране.
static func quad(def: Dictionary, is_pool: bool) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = str(def.get("id", "quad"))
	var mesh := QuadMesh.new()
	var size: Array = def.get("size", [1.0, 1.0])
	mesh.size = Vector2(float(size[0]), float(size[1]))
	node.mesh = mesh
	var pos: Array = def.get("pos", [0.0, 0.0, 0.0])
	node.position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	var rot: Array = def.get("rot", [0.0, 0.0, 0.0])
	node.rotation_degrees = Vector3(float(rot[0]), float(rot[1]), float(rot[2]))
	node.material_override = pool_material(def) if is_pool else flat_material(def)
	node.visible = bool(def.get("visible", true))
	return node


## Плоский непросвечиваемый цвет: силуэт читается очертанием, не светотенью.
static func flat_material(def: Dictionary) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color_of(def, [0.06, 0.065, 0.09])
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	if bool(def.get("billboard", false)):
		mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	return mat


## Лужа света: аддитивное пятно с мягким краем. Свет как форма.
static func pool_material(def: Dictionary) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	var c := color_of(def, [1.0, 0.72, 0.38])
	c.a = float(def.get("strength", 0.5))
	mat.albedo_color = c
	mat.albedo_texture = pool_gradient()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.no_depth_test = bool(def.get("no_depth_test", false))
	return mat


static func color_of(def: Dictionary, fallback: Array) -> Color:
	var c: Array = def.get("color", fallback)
	return Color(float(c[0]), float(c[1]), float(c[2]))


static func pool_gradient() -> GradientTexture2D:
	if _pool_texture != null:
		return _pool_texture
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.55, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.35), Color(1, 1, 1, 0)])
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 256
	t.height = 256
	_pool_texture = t
	return t


## Фигура из плоских частей (шарнирная вырезка, visual_direction §3): голова,
## корпус, плечо, подол. Лиц нет — человек читается очертанием.
static func silhouette(def: Dictionary) -> Node3D:
	var root := Node3D.new()
	var parts: Array = def.get("silhouette_parts", [])
	var shade: Array = def.get("color", [0.035, 0.035, 0.05])
	if parts.is_empty():
		var size: Array = def.get("silhouette_size", [0.6, 1.7])
		parts = [{"pos": [0.0, float(size[1]) * 0.5, 0.0], "size": size}]
	for part in parts:
		var pdef: Dictionary = (part as Dictionary).duplicate()
		if not pdef.has("color"):
			pdef["color"] = shade
		pdef["billboard"] = true
		root.add_child(quad(pdef, false))
	return root


## Камера: фиксированный театральный кадр из данных вагона.
static func apply_camera(card: Dictionary, camera: Camera3D) -> void:
	var cam: Dictionary = card.get("stage", {}).get("camera", {})
	if cam.is_empty():
		return
	var pos: Array = cam.get("pos", [0.0, 5.0, 8.0])
	camera.position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	var rot: Array = cam.get("rot", [-28.0, 0.0, 0.0])
	camera.rotation_degrees = Vector3(float(rot[0]), float(rot[1]), float(rot[2]))
	camera.size = float(cam.get("size", 8.0))
