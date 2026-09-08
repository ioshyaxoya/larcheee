class_name ChanceProviders
extends RefCounted
## Провайдеры вероятности для бросков шанса. Бросок всегда виден игроку
## (Checks.roll_chance); здесь только формула, и она показывается в UI.


static func probability(provider: String, ctx: GameContext) -> float:
	match provider:
		"bridge_raised":
			# Понтонный мост разводят для судов: чем позже вы подошли, тем вероятнее.
			# 8 минут в бите 1 → 15 %, 12 минут → 75 %.
			var bit1 := int(ctx.world.get_flag("quest.last_half_hour.bit1_minutes", 8))
			return clampf(0.15 + (bit1 - 8) * 0.15, 0.15, 0.75)
		"coin":
			return 0.5
	push_error("ChanceProviders: неизвестный provider %s" % provider)
	return 0.5
