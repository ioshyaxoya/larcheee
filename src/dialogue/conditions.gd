class_name DialogueConditions
extends RefCounted
## Язык условий данных (docs/data_format.md). Общий для диалогов, триггеров,
## NPC и предметов. Все условия чистые: читают контекст, ничего не меняют.


static func all(conds: Variant, ctx: GameContext) -> bool:
	if conds == null:
		return true
	for c in conds:
		if not evaluate(c, ctx):
			return false
	return true


static func evaluate(c: Dictionary, ctx: GameContext) -> bool:
	if c.has("not"):
		return not evaluate(c["not"], ctx)
	if c.has("any"):
		for sub in c["any"]:
			if evaluate(sub, ctx):
				return true
		return false
	if c.has("all"):
		return all(c["all"], ctx)
	if c.has("flag"):
		var name: String = c["flag"]
		if c.has("set"):
			return ctx.world.has_flag(name) == bool(c["set"])
		if c.has("equals"):
			return ctx.world.get_flag(name) == c["equals"]
		if c.has("in"):
			return (c["in"] as Array).has(ctx.world.get_flag(name))
		return ctx.world.get_flag(name, false) == c.get("is", true)
	if c.has("tag"):
		return ctx.world.has_tag(c["tag"]) == c.get("is", true)
	if c.has("origin"):
		return ctx.character != null and ctx.character.origin_id == c["origin"]
	if c.has("origin_in"):
		return ctx.character != null and (c["origin_in"] as Array).has(ctx.character.origin_id)
	if c.has("class"):
		return ctx.character != null and ctx.character.class_id == c["class"]
	if c.has("sex"):
		return ctx.character != null and ctx.character.sex == c["sex"]
	if c.has("axis"):
		return ctx.character != null and ctx.character.axes.get(c["axis"], "") == c.get("pole", "")
	if c.has("has_item"):
		return ctx.world.has_item(c["has_item"]) == c.get("is", true)
	if c.has("money_min"):
		return ctx.world.money >= int(c["money_min"])
	if c.has("minutes_spent_min"):
		return ctx.clock.spent() >= int(c["minutes_spent_min"])
	push_error("DialogueConditions: неизвестное условие %s" % str(c))
	return false
