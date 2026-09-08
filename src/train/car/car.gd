class_name Car
extends Node3D
## Вагон: загружается из карточки data/cars/<id>.json, спавнит NPC по
## data/npcs/, подключает столкновения из data/encounters/ как триггеры.
## Пространство — плоскости в объёме (задник, пол, кулисы): docs/visual_direction.md.

signal npc_approached(npc_id: String)
signal dialogue_started(npc_id: String, runtime: DialogueRuntime)
signal dialogue_ended(npc_id: String)
signal custom_event(name: String)
signal item_taken(item_id: String)
signal hour_state_changed(hours_lost: int, state: Dictionary)

const CELL := 0.5   # метров на клетку сетки карточки
const ITEMS_DIR := "res://data/items/"

var ctx: GameContext
var card: Dictionary = {}
var car_id: String = ""
var npcs: Dictionary = {}          # npc_id → NpcNode
var triggers: TriggerSystem
var items: Dictionary = {}         # item_id → def (только те, что в вагоне сейчас)
var custom: Node = null            # car.custom_script — уникальная механика вагона
var hours_lost: int = 0
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
	_load_items()
	_attach_custom_script()
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


func _load_items() -> void:
	var ids: Array = []
	for i in card.get("items_present", []):
		ids.append(i)
	for i in card.get("seed_items", []):
		ids.append(i)
	for iid in ids:
		var path := ITEMS_DIR + str(iid) + ".json"
		if not FileAccess.file_exists(path):
			push_error("Car: нет предмета %s" % path)
			continue
		var def = JSON.parse_string(FileAccess.get_file_as_string(path))
		if typeof(def) != TYPE_DICTIONARY:
			continue
		if ctx.world.has_item(str(iid)):
			continue
		if not DialogueConditions.all(def.get("conditions", []), ctx):
			continue
		items[str(iid)] = def


func _attach_custom_script() -> void:
	var path := str(card.get("custom_script", ""))
	if path == "" or path == "null":
		return
	var script := load(path)
	if script == null:
		push_error("Car: custom_script %s не загружен" % path)
		return
	custom = Node.new()
	custom.set_script(script)
	custom.name = "Custom"
	add_child(custom)
	if custom.has_method("attach"):
		custom.call("attach", self, ctx)


func seed_items_present() -> Array[String]:
	var out: Array[String] = []
	for iid in items.keys():
		if str(items[iid].get("kind", "")) == "seed":
			out.append(String(iid))
	return out


## Взять предмет со стеллажа. Семян — не больше seed_take_limit (карточка).
func take_item(item_id: String) -> bool:
	if not items.has(item_id):
		return false
	var def: Dictionary = items[item_id]
	if not def.get("takeable", false):
		return false
	if str(def.get("kind", "")) == "seed":
		var limit := int(card.get("seed_take_limit", 3))
		var taken := int(ctx.world.get_flag("car_01.seeds_taken", 0)) if car_id == "car_01" else 0
		if taken >= limit:
			return false
		if car_id == "car_01":
			ctx.world.set_flag("car_01.seeds_taken", taken + 1)
	ctx.world.add_item(item_id)
	items.erase(item_id)
	DialogueEffects.apply(def.get("on_take", []), ctx, self)
	triggers.fire("item_taken", {"item": item_id})
	item_taken.emit(item_id)
	return true


## Состояние вагона по state_schema карточки — из флагов car_XX.<ключ>.
func state() -> Dictionary:
	var st := {}
	for key in card.get("state_schema", {}).keys():
		st[key] = ctx.world.get_flag(car_id + "." + str(key), null)
	st["clock_hours_lost"] = hours_lost if st.get("clock_hours_lost") == null else st["clock_hours_lost"]
	return st


## Хвостовой вариант: какие сцены хвоста применимы по tail_rules/tail_scene.
func tail_scene_keys() -> Array[String]:
	var st := state()
	var scene: Dictionary = card.get("tail_scene", {})
	var out: Array[String] = []
	if st.get("lantern_taken", false) == true and scene.has("lantern_taken"):
		out.append(str(scene["lantern_taken"]))
		return out
	if st.get("forced_door", false) == true and scene.has("forced_door"):
		out.append(str(scene["forced_door"]))
	if st.get("shift_worked", false) == true and scene.has("shift_worked"):
		out.append(str(scene["shift_worked"]))
	if int(st.get("clock_hours_lost", 0)) > 0 and scene.has("clock_hours_lost>0"):
		out.append(str(scene["clock_hours_lost>0"]))
	if out.is_empty() and scene.has("default"):
		out.append(str(scene["default"]))
	return out


## Вагон физически становится на N часов раньше: свет, NPC (данные испытания).
func apply_hour_state(hours: int, hour_states: Dictionary) -> void:
	hours_lost = hours
	if car_id == "car_01":
		ctx.world.set_flag("car_01.clock_hours_lost", hours)
	var st: Dictionary = hour_states.get(str(hours), {})
	var lantern := get_node_or_null("Lantern")
	if lantern != null:
		var light := str(st.get("light", "night"))
		var colors := {"night": Color(1.0, 0.8, 0.55), "dusk": Color(1.0, 0.6, 0.35), "sunset": Color(1.0, 0.5, 0.3), "afternoon": Color(1.0, 0.9, 0.7), "day": Color(1.0, 1.0, 0.95), "siding": Color(0.9, 0.9, 0.9)}
		lantern.light_color = colors.get(light, colors["night"])
		lantern.light_energy = 1.0 + hours * 0.6
	for npc_id in st.get("npc_states", {}).keys():
		if npcs.has(npc_id):
			(npcs[npc_id] as NpcNode).set_state(str(st["npc_states"][npc_id]))
	if hours == 0:
		for npc_id in npcs.keys():
			(npcs[npc_id] as NpcNode).set_state("default")
	hour_state_changed.emit(hours, st)


## Вход в вагон: срабатывают триггеры car_entered, вагон помечается посещённым.
func enter() -> void:
	entered = true
	ctx.world.location["car"] = car_id
	var st := ctx.world.car_state(car_id)
	st["visited"] = true
	triggers.fire("car_entered")


## Выход вперёд: состояние вагона записывается, вагон уходит в хвост,
## окно двигается на window_progress_delta пути (A8).
func leave_forward() -> void:
	var st := ctx.world.car_state(car_id)
	st["state"] = state()
	if not ctx.world.tail_order.has(car_id):
		ctx.world.tail_order.append(car_id)
	var path := str(ctx.world.get_flag(car_id + ".path", ""))
	var delta := int((card.get("window_progress_delta", {}) as Dictionary).get(path, 0))
	ctx.world.progress += delta
	ctx.world.set_flag("window.progress", ctx.world.progress)
	ctx.world.location["car"] = ""
	triggers.fire("car_left")


## Запустить сцену вагона по имени из card.scenes (диалог из data/dialogues).
func play_scene(scene: String) -> DialogueRuntime:
	var dlg_id := str((card.get("scenes", {}) as Dictionary).get(scene, ""))
	if dlg_id == "":
		push_error("Car: нет сцены %s" % scene)
		return null
	var dlg := DialogueLoader.load_dialogue(dlg_id)
	if dlg.is_empty():
		return null
	var rt := DialogueRuntime.new(ctx)
	rt.custom_event.connect(func(n: String): custom_event.emit(n))
	if custom != null and custom.has_method("minigame"):
		rt.minigame_provider = func(id: String) -> bool: return bool(custom.call("minigame", id))
	active_runtime = rt
	rt.ended.connect(func(): active_runtime = null)
	rt.start(dlg)
	return rt


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
	if custom != null and custom.has_method("minigame"):
		rt.minigame_provider = func(id: String) -> bool: return bool(custom.call("minigame", id))
	rt.ended.connect(func():
		active_runtime = null
		triggers.fire("dialogue_ended", {"npc": npc_id})
		dialogue_ended.emit(npc_id))
	active_runtime = rt
	dialogue_started.emit(npc_id, rt)
	rt.start(dlg)
	return rt
