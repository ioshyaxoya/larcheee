class_name GameContext
extends RefCounted
## Связка сервисов одной игры: тексты, реестр флагов, RNG, состояние мира,
## проверки, данные персонажей, битовые часы. Модули получают контекст явно —
## так их можно гонять в headless-тесте без сцены и автозагрузок.

const SAVE_PATH := "user://world_state.json"

var texts: Texts
var registry: FlagRegistry
var rng: SeededRng
var world: WorldState
var checks: Checks
var char_data: CharacterData
var character: Character
var clock: BeatClock


static func create(seed_v: int = 0, lang: String = "ru") -> GameContext:
	var ctx := GameContext.new()
	ctx.texts = Texts.new(lang)
	ctx.registry = FlagRegistry.new()
	ctx.rng = SeededRng.new(seed_v)
	ctx.world = WorldState.new(ctx.registry)
	ctx.world.rng_seed = seed_v
	ctx.char_data = CharacterData.new()
	ctx.checks = Checks.new(ctx.rng, ctx.char_data)
	ctx.clock = BeatClock.new(ctx.world)
	return ctx


func set_character(ch: Character) -> void:
	character = ch
	world.character = ch.to_dict()
	world.money = ch.money
	for flag in ch.origin_flags:
		world.set_flag(flag, true)


func save(path: String = SAVE_PATH) -> bool:
	world.rng_state = rng.get_state()
	if character != null:
		character.money = world.money
		world.character = character.to_dict()
	return world.save(path)


func load_from(path: String = SAVE_PATH) -> bool:
	if not world.load_from(path):
		return false
	rng.reseed(world.rng_seed)
	rng.set_state(world.rng_state)
	if not world.character.is_empty():
		character = Character.from_dict(world.character)
		character.money = world.money
	return true
