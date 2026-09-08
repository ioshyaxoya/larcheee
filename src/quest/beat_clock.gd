class_name BeatClock
extends RefCounted
## Битовые часы (A5): двигаются поступками, не таймером. Каждая потеря
## показывается в минутах в тот же момент — через сигнал time_spent.

signal time_spent(minutes: int, reason_key: String, now_minutes: int)

var world: WorldState
var start_minutes: int = 20 * 60
var deadline_minutes: int = 20 * 60 + 30
var log: Array[Dictionary] = []


func _init(world_state: WorldState) -> void:
	world = world_state


func configure(start: int, deadline: int) -> void:
	start_minutes = start
	deadline_minutes = deadline
	world.clock_minutes = start
	log.clear()


func now() -> int:
	return world.clock_minutes


func spend(minutes: int, reason_key: String) -> void:
	if minutes <= 0:
		return
	world.clock_minutes += minutes
	log.append({"minutes": minutes, "reason_key": reason_key, "now": world.clock_minutes})
	time_spent.emit(minutes, reason_key, world.clock_minutes)


func spent() -> int:
	return world.clock_minutes - start_minutes


func minutes_late() -> int:
	return maxi(0, world.clock_minutes - deadline_minutes)


static func format_time(minutes: int) -> String:
	return "%02d:%02d" % [int(minutes / 60.0) % 24, minutes % 60]


func now_string() -> String:
	return format_time(world.clock_minutes)
