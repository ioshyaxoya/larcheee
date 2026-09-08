extends Node
## Автозагрузка Game: держит текущий GameContext для сцен.
## Тесты и модули контекст получают явно; сцены — отсюда.

var ctx: GameContext


func _ready() -> void:
	if ctx == null:
		ctx = GameContext.create(0, "ru")


func new_game(seed_v: int, lang: String = "ru") -> GameContext:
	ctx = GameContext.create(seed_v, lang)
	return ctx
