class_name SeededRng
extends RefCounted
## RNG с seed. Состояние сохраняется в world_state.json, чтобы загрузка
## воспроизводила те же броски.

var _rng := RandomNumberGenerator.new()
var seed_value: int = 0


func _init(seed_v: int = 0) -> void:
	reseed(seed_v)


func reseed(seed_v: int) -> void:
	seed_value = seed_v
	_rng.seed = seed_v


func d20() -> int:
	return _rng.randi_range(1, 20)


func randi_range(from: int, to: int) -> int:
	return _rng.randi_range(from, to)


func randf() -> float:
	return _rng.randf()


func get_state() -> int:
	return _rng.state


func set_state(state: int) -> void:
	_rng.state = state
