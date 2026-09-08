class_name GradeLayer
extends CanvasLayer
## Грейдинг кадра: один конвейер, два шейдера (docs/visual_direction.md §6).
## Базовый режим — theatrical.gdshader, режим испытания — dither_1bit.gdshader
## с параметром colour_return: время стоит, цвета нет; выигранный раунд его возвращает.

const THEATRICAL := "res://assets/shaders/theatrical.gdshader"
const DITHER := "res://assets/shaders/dither_1bit.gdshader"

var palette: Palette
var rect: TextureRect
var theatrical_mat: ShaderMaterial
var dither_mat: ShaderMaterial


func _init() -> void:
	layer = 0   # кадр мира; интерфейс идёт слоями выше и не грейдится
	rect = TextureRect.new()
	rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(rect)
	theatrical_mat = ShaderMaterial.new()
	theatrical_mat.shader = load(THEATRICAL)
	dither_mat = ShaderMaterial.new()
	dither_mat.shader = load(DITHER)
	rect.material = theatrical_mat


func bind(p: Palette) -> void:
	palette = p
	refresh()


## Кадр мира: текстура подвьюпорта, в котором живёт сцена.
func set_source(tex: Texture2D) -> void:
	rect.texture = tex


## Переносит параметры палитры в шейдер. Вызывается на смене палитры и на
## каждом выигранном или проигранном раунде испытания.
func refresh() -> void:
	if palette == null:
		return
	var p := palette.effective()
	var tint: Array = p.get("tint", [1, 1, 1])
	var tint_v := Vector3(float(tint[0]), float(tint[1]), float(tint[2]))
	var mat: ShaderMaterial = dither_mat if palette.in_trial else theatrical_mat
	rect.material = mat
	mat.set_shader_parameter("tint", tint_v)
	mat.set_shader_parameter("saturation", float(p.get("saturation", 1.0)))
	mat.set_shader_parameter("vignette", float(p.get("vignette", 0.3)))
	if palette.in_trial:
		mat.set_shader_parameter("colour_return", palette.colour_return)
		mat.set_shader_parameter("pixel_size", 2.0)
	else:
		mat.set_shader_parameter("contrast", float(p.get("contrast", 1.0)))
		mat.set_shader_parameter("brightness", float(p.get("brightness", 1.0)))
		mat.set_shader_parameter("glow", 0.35 if p.get("glow", false) else 0.0)
		mat.set_shader_parameter("grain", 0.028)


func _process(_delta: float) -> void:
	if not palette.in_trial and rect.material == theatrical_mat:
		theatrical_mat.set_shader_parameter("seed", float(Time.get_ticks_msec() % 10000) * 0.001)
