class_name RhythmTrack
extends RefCounted
## Ритм номера (A10, модуль performance): такт задаётся стуком колёс.
## Нажатие в окне попадания даёт видимый модификатор к броску; мимо — штраф.
## Никакой скрытой математики: окно и модификаторы берутся из данных испытания.

var bpm: float = 72.0
var window_ms: float = 160.0
var hit_modifier: int = 2
var miss_modifier: int = -2
var start_msec: int = 0
var track_name: String = ""


func configure(data: Dictionary) -> void:
	bpm = float(data.get("bpm", 72))
	window_ms = float(data.get("window_ms", 160))
	hit_modifier = int(data.get("hit_modifier", 2))
	miss_modifier = int(data.get("miss_modifier", -2))
	track_name = str(data.get("track", ""))


func beat_ms() -> float:
	return 60000.0 / bpm


func start(now_msec: int) -> void:
	start_msec = now_msec


## Фаза такта 0..1 для UI-маркера.
func phase(now_msec: int) -> float:
	var t := float(now_msec - start_msec)
	return fmod(t, beat_ms()) / beat_ms()


## Судит нажатие: расстояние до ближайшего удара в мс.
func judge(input_msec: int) -> Dictionary:
	var t := float(input_msec - start_msec)
	var b := beat_ms()
	var off := fmod(t, b)
	if off > b / 2.0:
		off = off - b
	var hit := absf(off) <= window_ms / 2.0
	return {"offset_ms": off, "hit": hit, "modifier": hit_modifier if hit else miss_modifier}


## Для тестов и для автоигры: судить по точности −1..1 (0 — в такт).
func judge_accuracy(accuracy: float) -> Dictionary:
	var off := accuracy * beat_ms() / 2.0
	var hit := absf(off) <= window_ms / 2.0
	return {"offset_ms": off, "hit": hit, "modifier": hit_modifier if hit else miss_modifier}
