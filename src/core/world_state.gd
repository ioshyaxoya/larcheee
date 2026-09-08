class_name WorldState
extends RefCounted
## Состояние мира (ТЗ B4): флаги, вагоны, хвост, прогресс, партия, билет,
## репутация фракций, линия Маллика, детонация, оседлость, боги, часы.
## Сохраняется целиком в единый world_state.json.

signal flag_changed(name: String, value: Variant)

const SAVE_VERSION := 1

var registry: FlagRegistry
var flags: Dictionary = {}
var clock_minutes: int = 20 * 60
var money: int = 0
var character: Dictionary = {}
var location: Dictionary = {"car": "", "quest": ""}
var cars: Dictionary = {}                 # car_id → {state: {...}}
var tail_order: Array = []
var progress: int = 0
var party: Dictionary = {"core": [], "flow": [], "left_behind": []}
var ticket: Dictionary = {"ticket_class": 3, "ticket_name": "???", "ticket_origin": "", "berth_ledger": "overwritten"}
var faction_rep: Dictionary = {"aryan": 0, "union": 0, "national_mod": 0, "national_rad": 0, "revival": 0}
var mallick_outcome: String = "none"
var detonation: Dictionary = {"pressure": 0, "state": "sealed", "form": "", "beat": 0}
var settled_in: Array = []
var god_states: Dictionary = {}
var inventory: Array = []
var rng_seed: int = 0
var rng_state: int = 0


func _init(flag_registry: FlagRegistry) -> void:
	registry = flag_registry


func set_flag(name: String, value: Variant) -> bool:
	if not registry.has_flag(name):
		push_error("WorldState: флаг «%s» не зарегистрирован в data/flags.json" % name)
		return false
	if not registry.validate(name, value):
		push_error("WorldState: флаг «%s» (%s) не принимает %s" % [name, registry.flag_type(name), str(value)])
		return false
	if registry.flag_type(name) == "int":
		value = int(value)
	flags[name] = value
	flag_changed.emit(name, value)
	return true


func get_flag(name: String, default: Variant = null) -> Variant:
	return flags.get(name, default)


func has_flag(name: String) -> bool:
	return flags.has(name)


## Тег пролога = флаг prologue.<tag> со значением true.
func add_tag(tag: String) -> bool:
	return set_flag(FlagRegistry.TAG_PREFIX + tag, true)


func has_tag(tag: String) -> bool:
	return get_flag(FlagRegistry.TAG_PREFIX + tag, false) == true


func has_item(item_id: String) -> bool:
	return inventory.has(item_id)


func add_item(item_id: String) -> void:
	if not inventory.has(item_id):
		inventory.append(item_id)


func remove_item(item_id: String) -> void:
	inventory.erase(item_id)


func car_state(car_id: String) -> Dictionary:
	if not cars.has(car_id):
		cars[car_id] = {"state": {}, "visited": false}
	return cars[car_id]


func to_dict() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"flags": flags.duplicate(true),
		"clock": {"minutes": clock_minutes},
		"money": money,
		"character": character.duplicate(true),
		"location": location.duplicate(true),
		"cars": cars.duplicate(true),
		"tail_order": tail_order.duplicate(),
		"progress": progress,
		"party": party.duplicate(true),
		"ticket": ticket.duplicate(true),
		"faction_rep": faction_rep.duplicate(true),
		"mallick_outcome": mallick_outcome,
		"detonation": detonation.duplicate(true),
		"settled_in": settled_in.duplicate(true),
		"god_states": god_states.duplicate(true),
		"inventory": inventory.duplicate(),
		"rng_seed": rng_seed,
		"rng_state": rng_state,
	}


func from_dict(data: Dictionary) -> void:
	flags = {}
	var saved_flags: Dictionary = data.get("flags", {})
	for name in saved_flags.keys():
		set_flag(name, saved_flags[name])
	clock_minutes = int(data.get("clock", {}).get("minutes", 20 * 60))
	money = int(data.get("money", 0))
	character = (data.get("character", {}) as Dictionary).duplicate(true)
	location = (data.get("location", {"car": "", "quest": ""}) as Dictionary).duplicate(true)
	cars = (data.get("cars", {}) as Dictionary).duplicate(true)
	tail_order = (data.get("tail_order", []) as Array).duplicate()
	progress = int(data.get("progress", 0))
	party = (data.get("party", party) as Dictionary).duplicate(true)
	ticket = (data.get("ticket", ticket) as Dictionary).duplicate(true)
	faction_rep = (data.get("faction_rep", faction_rep) as Dictionary).duplicate(true)
	mallick_outcome = str(data.get("mallick_outcome", "none"))
	detonation = (data.get("detonation", detonation) as Dictionary).duplicate(true)
	settled_in = (data.get("settled_in", []) as Array).duplicate(true)
	god_states = (data.get("god_states", {}) as Dictionary).duplicate(true)
	inventory = (data.get("inventory", []) as Array).duplicate()
	rng_seed = int(data.get("rng_seed", 0))
	rng_state = int(data.get("rng_state", 0))


func save(path: String) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("WorldState: не удалось открыть %s для записи" % path)
		return false
	file.store_string(JSON.stringify(to_dict(), "  "))
	file.close()
	return true


func load_from(path: String) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("WorldState: %s — невалидный сейв" % path)
		return false
	from_dict(parsed)
	return true
