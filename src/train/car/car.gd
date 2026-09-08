class_name Car
extends Node3D
## Вагон: загружается из карточки data/cars/<id>.json, спавнит NPC по
## data/npcs/, подключает столкновения из data/encounters/ как триггеры.
## Пространство — плоскости в объёме (задник, пол, кулисы): docs/visual_direction.md.

signal npc_approached(npc_id: String)
signal dialogue_started(npc_id: String, runtime: DialogueRuntime)
signal dialogue_ended(npc_id: String)
signal custom_event(name: String)

const CELL := 0.5   # метров на клетку сетки карточки

var ctx: GameContext
var card: Dictionary = {}
var car_id: String = ""
var npcs: Dictionary = {}          # npc_id → NpcNode
var triggers: TriggerSystem
var entered: bool = false
var active_runtime: DialogueRuntime = null


func setup(car_card: Dictionary, context: GameContext) -> void:
	ctx = context
	card = car_card
	car_id = str(card.get("id", ""))
	name = car_id
	triggers = TriggerSystem.new(ctx)
	triggers.custom_event.connect(func(n: String): custom_event.emit(n))
	_build_stage()
	_spawn_npcs()
	for enc_id in card.get("encounters", []):
		var enc := CarLoader.load_encounter(str(enc_id))
		if not enc.is_empty():
			triggers.add(enc)
	for t in card.get("triggers", []):
		triggers.add(t)


func _build_stage() -> void:
	if DisplayServer.get_name() == "headless":
		return   # dummy-рендер не строит меши; логика вагона от сцены не зависит
	var grid: Dictionary = card.get("grid", {"w": 18, "h": 46})
	var w := float(grid.get("w", 18)) * CELL
	var h := float(grid.get("h", 46)) * CELL
	var floor_mesh := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(w, h)
	floor_mesh.mesh = plane
	floor_mesh.name = "Floor"
	add_child(floor_mesh)
	var backdrop := MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(w, 3.0)
	backdrop.mesh = quad
	backdrop.position = Vector3(0, 1.5, -h / 2.0)
	backdrop.name = "Backdrop"
	add_child(backdrop)
	var light := OmniLight3D.new()
	light.name = "Lantern"
	light.position = Vector3(0, 2.2, 2.0)
	light.light_color = Color(1.0, 0.8, 0.55)
	light.omni_range = 6.0
	light.visible = ctx.world.get_flag("car_01.lantern_lit", false) == true
	add_child(light)


func _spawn_npcs() -> void:
	for npc_id in card.get("npcs", []):
		var def := CarLoader.load_npc(str(npc_id))
		if def.is_empty():
			continue
		if not DialogueConditions.all(def.get("conditions", []), ctx):
			continue
		var node := NpcNode.new()
		node.setup(def, ctx)
		add_child(node)
		npcs[str(npc_id)] = node


## Вход в вагон: срабатывают триггеры car_entered, вагон помечается посещённым.
func enter() -> void:
	entered = true
	ctx.world.location["car"] = car_id
	var st := ctx.world.car_state(car_id)
	st["visited"] = true
	triggers.fire("car_entered")


func visible_npc_ids() -> Array[String]:
	var out: Array[String] = []
	for k in npcs.keys():
		out.append(String(k))
	return out


## Заговорить с NPC: триггеры npc_approached, затем его диалог из data/dialogues/.
func talk_to(npc_id: String) -> DialogueRuntime:
	if not npcs.has(npc_id):
		push_error("Car: NPC «%s» нет в вагоне" % npc_id)
		return null
	var node: NpcNode = npcs[npc_id]
	npc_approached.emit(npc_id)
	triggers.fire("npc_approached", {"npc": npc_id})
	var dlg_id := str(node.def.get("dialogue", ""))
	if dlg_id == "":
		return null
	var dlg := DialogueLoader.load_dialogue(dlg_id)
	if dlg.is_empty():
		return null
	var rt := DialogueRuntime.new(ctx)
	rt.custom_event.connect(func(n: String): custom_event.emit(n))
	rt.ended.connect(func():
		active_runtime = null
		triggers.fire("dialogue_ended", {"npc": npc_id})
		dialogue_ended.emit(npc_id))
	active_runtime = rt
	dialogue_started.emit(npc_id, rt)
	rt.start(dlg)
	return rt
