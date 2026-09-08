class_name NpcNode
extends Node3D
## NPC на сцене: плоский силуэт без лица, читаемый очертанием (тюрбан, топи,
## сари, шинель) — docs/visual_direction.md §3. Форма и светлота задаются
## данными NPC. Подписей над головой нет: имя говорящего показывает панель
## диалога. Свет лепит фигуру, а не текстура.

var npc_id: String = ""
var def: Dictionary = {}
var state: String = "default"
var hidden_by_dark: bool = false
var body: Node3D


func setup(npc_def: Dictionary, _ctx: GameContext) -> void:
	def = npc_def
	npc_id = str(npc_def.get("id", ""))
	name = npc_id
	var pos: Array = npc_def.get("position", [0, 0, 0])
	position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	if DisplayServer.get_name() == "headless":
		return
	body = StageBuilder.silhouette(npc_def)
	add_child(body)


## Состояние NPC (данные npc.states): patrol, hidden, crying, standing.
func set_state(new_state: String) -> void:
	state = new_state
	if state == "standing" and body != null:
		body.position.y = 0.12
	_refresh_visibility()


func set_hidden_by_dark(hidden: bool) -> void:
	hidden_by_dark = hidden
	_refresh_visibility()


func _refresh_visibility() -> void:
	visible = state != "hidden" and not hidden_by_dark


## Реплика по оси отношения: полюс персонажа → text_key (B4 attitude_axes).
func axis_line_key(axis: String, ctx: GameContext) -> String:
	if ctx.character == null:
		return ""
	var pole: String = str(ctx.character.axes.get(axis, ""))
	var reactions: Dictionary = def.get("attitude_axes", {}).get(axis, {})
	return str(reactions.get(pole, ""))
