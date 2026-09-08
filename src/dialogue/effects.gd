class_name DialogueEffects
extends RefCounted
## Язык эффектов данных (docs/data_format.md). Возвращает переход:
## {"goto": node_id | "", "end": bool}. Время уходит только через BeatClock,
## флаги — только через WorldState (и его реестр).


static func apply(effs: Variant, ctx: GameContext, emitter: Object = null) -> Dictionary:
	var result := {"goto": "", "end": false}
	if effs == null:
		return result
	for e in effs:
		if e.has("set_flag"):
			ctx.world.set_flag(e["set_flag"], e["value"])
		elif e.has("add_tag"):
			ctx.world.add_tag(e["add_tag"])
		elif e.has("add_minutes"):
			ctx.clock.spend(int(e["add_minutes"]), str(e.get("reason_key", "")))
		elif e.has("add_money"):
			ctx.world.money += int(e["add_money"])
			if ctx.character != null:
				ctx.character.money = ctx.world.money
		elif e.has("goto"):
			result["goto"] = str(e["goto"])
		elif e.has("end"):
			result["end"] = bool(e["end"])
		elif e.has("emit"):
			if emitter != null and emitter.has_signal("custom_event"):
				emitter.emit_signal("custom_event", str(e["emit"]))
		elif e.has("record_minutes_flag"):
			ctx.world.set_flag(e["record_minutes_flag"], ctx.clock.minutes_late())
		else:
			push_error("DialogueEffects: неизвестный эффект %s" % str(e))
	return result
