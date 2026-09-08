class_name GradeLayer
extends CanvasLayer
## Грейдинг кадра: один конвейер, два шейдера (docs/visual_direction.md §6).
## Базовый режим — theatrical.gdshader, режим испытания — dither_1bit.gdshader
## с параметром colour_return: время стоит, цвета нет; выигранный раунд его возвращает.

const THEATRICAL := "res://assets/shaders/theatrical.gdshader"
const DITHER := "res://assets/shaders/dither_1bit.gdshader"
const PRESENCE := "res://assets/shaders/presence.gdshader"

var palette: Palette
var rect: TextureRect
var presence_rect: TextureRect
var theatrical_mat: ShaderMaterial
var dither_mat: ShaderMaterial
var presence_mat: ShaderMaterial
var world_tex: Texture2D          # кадр вагона: он же — то, что видно в глитче
var trial_tex: Texture2D          # кадр мира испытания
var glitch: float = 0.0


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
	# Присутствие идёт вторым кадром поверх дизеренного мира и не грейдится:
	# мир — точки, бог — цвет. Прозрачный фон подвьюпорта делает остальное.
	presence_rect = TextureRect.new()
	presence_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	presence_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	presence_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	presence_rect.stretch_mode = TextureRect.STRETCH_SCALE
	presence_rect.visible = false
	presence_mat = ShaderMaterial.new()
	presence_mat.shader = load(PRESENCE)
	presence_rect.material = presence_mat
	add_child(presence_rect)


func bind(p: Palette) -> void:
	palette = p
	refresh()


## Кадр мира: текстура подвьюпорта, в котором живёт сцена.
func set_source(tex: Texture2D) -> void:
	world_tex = tex
	rect.texture = tex


## Кадры испытания: мир Шани (в точки) и присутствие (в цвете, поверх).
func set_trial_source(world: Texture2D, presence: Texture2D) -> void:
	trial_tex = world
	presence_rect.texture = presence


## Сбой мира: Шани сомневается во всём вокруг, и сквозь его мир проступают
## стены вагона — тоже точками. 0 — мир держится, 1 — рвётся полосами.
func set_glitch(v: float) -> void:
	glitch = clampf(v, 0.0, 1.0)
	if palette != null and palette.in_trial:
		dither_mat.set_shader_parameter("glitch", glitch)


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
	# В испытании основной кадр — мир Шани, а кадр вагона уходит в глитч.
	rect.texture = trial_tex if (palette.in_trial and trial_tex != null) else world_tex
	presence_rect.visible = palette.in_trial
	mat.set_shader_parameter("tint", tint_v)
	mat.set_shader_parameter("saturation", float(p.get("saturation", 1.0)))
	mat.set_shader_parameter("vignette", float(p.get("vignette", 0.3)))
	if palette.in_trial:
		mat.set_shader_parameter("colour_return", palette.colour_return)
		mat.set_shader_parameter("pixel_size", 2.0)
		mat.set_shader_parameter("glitch", glitch)
		if world_tex != null:
			mat.set_shader_parameter("alt_tex", world_tex)
		# Тот же спад к краям, что у мира: присутствие в кадре, а не на кадре.
		presence_mat.set_shader_parameter("vignette", float(p.get("vignette", 0.35)))
		presence_mat.set_shader_parameter("ambient_mix", 0.10 - 0.06 * palette.colour_return)
	else:
		mat.set_shader_parameter("contrast", float(p.get("contrast", 1.0)))
		mat.set_shader_parameter("brightness", float(p.get("brightness", 1.0)))
		mat.set_shader_parameter("glow", 0.35 if p.get("glow", false) else 0.0)
		mat.set_shader_parameter("grain", 0.028)


func _process(_delta: float) -> void:
	var t := float(Time.get_ticks_msec() % 100000) * 0.001
	if not palette.in_trial and rect.material == theatrical_mat:
		theatrical_mat.set_shader_parameter("seed", t)
		return
	if palette.in_trial:
		dither_mat.set_shader_parameter("time", t)
