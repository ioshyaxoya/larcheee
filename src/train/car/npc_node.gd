class_name NpcNode
extends Node3D
## NPC в вагоне: плоская фигура-силуэт (визуальное направление: плоский
## театральный 2.5D, фигуры без лиц) и подпись. Реакции — по осям attitude_axes.

var npc_id: String = ""
var def: Dictionary = {}
var label: Label3D


func setup(npc_def: Dictionary, ctx: GameContext) -> void:
	def = npc_def
	npc_id = str(npc_def.get("id", ""))
	name = npc_id
	var pos: Array = npc_def.get("position", [0, 0, 0])
	position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	if DisplayServer.get_name() != "headless":
		var body := MeshInstance3D.new()
		var quad := QuadMesh.new()
		quad.size = Vector2(0.6, 1.8)
		body.mesh = quad
		body.position.y = 0.9
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.08, 0.07, 0.1)
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		body.material_override = mat
		add_child(body)
		label = Label3D.new()
		label.text = ctx.texts.t(str(npc_def.get("name_key", "")))
		label.position.y = 2.0
		label.font_size = 24
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		add_child(label)


## Реплика по оси отношения: полюс персонажа → text_key (B4 attitude_axes).
func axis_line_key(axis: String, ctx: GameContext) -> String:
	if ctx.character == null:
		return ""
	var pole: String = str(ctx.character.axes.get(axis, ""))
	var reactions: Dictionary = def.get("attitude_axes", {}).get(axis, {})
	return str(reactions.get(pole, ""))
