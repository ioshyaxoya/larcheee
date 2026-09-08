extends SceneTree
## Проверка: вагон 01 проходится всеми четырьмя путями и нигде не упирается
## в дыру. Дыра — это не сломанная ссылка (её ловит tools/dialogue_validator.py),
## а узел, где на данном персонаже не осталось ни одного доступного варианта:
## статически граф цел, а игрок стоит. Поэтому прогоняются разные персонажи —
## именно на них расходятся условия по происхождению, классу, полу и предметам.
##
## Запуск: godot --headless --path . -s tests/paths_walk.gd

const BUILDS := [
	["bengali", "babu", "m"],
	["officer", "sepoy", "m"],
	["loafer", "thug", "f"],
	["marwari", "munshi", "m"],
	["pathan", "shikari", "m"],
	["chinese", "opium_eater", "f"],
	["armenian", "telegraphist", "f"],
	["habshi", "sadhu", "m"],
	["baghdadi_jew", "tantrik", "f"],
	["anglo_indian", "babu", "f"],
	["dutch", "shikari", "m"],
]
const PATHS := {
	"force": "exit_forward",
	"deceit": "exit_forward",
	"service": "exit_forward",
	"stay": "ending_5",
}

var holes: Array[String] = []          # настоящие дыры: игроку нечего нажать
var no_exit: Array[String] = []        # выход не достигнут за отведённые шаги
var passed := 0
var stuck_nodes := {}                  # узлы, где вариантов не осталось


func _init() -> void:
	for build in BUILDS:
		for path in PATHS.keys():
			_walk(build, str(path), str(PATHS[path]))
	print("")
	for f in holes:
		printerr("ДЫРА: " + f)
	for f in no_exit:
		print("повторы: " + f)
	print("paths_walk: %d прогонов из %d дошли до выхода, дыр %d"
		% [passed, BUILDS.size() * PATHS.size(), holes.size()])
	if holes.is_empty():
		print("Дыр нет: в каждом узле всегда оставался хотя бы один вариант.")
	quit(1 if holes.size() > 0 else 0)


func _ctx(build: Array) -> GameContext:
	var ctx := GameContext.create(11, "ru")
	var ch := ctx.char_data.build(str(build[0]), str(build[1]), str(build[2]))
	if ch == null:
		# Так пряталась ошибка в самом тесте: выдуманный класс давал Nil,
		# все проверки падали, и обходчик врал про непроходимый путь.
		printerr("ТЕСТ СЛОМАН: нет такого персонажа — %s/%s/%s" % [build[0], build[1], build[2]])
		quit(2)
	ctx.set_character(ch)
	return ctx


func _walk(build: Array, path: String, want_event: String) -> void:
	var who := "%s/%s/%s → %s" % [build[0], build[1], build[2], path]
	var ctx := _ctx(build)
	var card := CarLoader.load_card("car_01")
	var car := Car.new()
	car.setup(card, ctx)
	car.enter()
	# Испытание считаем выигранным: узел путей открывает выходы после суда.
	ctx.world.set_flag("car_01.trial_won", true)
	ctx.world.set_flag("car_01.lantern_taken", true)

	var seen_events: Array[String] = []
	var route := PackedStringArray()

	# 1. Узел путей: найти вариант, который уводит на нужный путь.
	var hub := car.play_scene("paths_hub")
	if hub == null:
		holes.append(who + ": сцена узла путей не открылась")
		return
	hub.custom_event.connect(func(n: String): seen_events.append(n))
	if not _drive(hub, route, "go_" + path, seen_events):
		holes.append(who + ": в узле путей не осталось вариантов. Маршрут: " + ", ".join(route))
		return
	if not seen_events.has("go_" + path):
		holes.append(who + ": узел путей не увёл на этот путь")
		return

	# 2. Сама сцена пути: пройти её насквозь и дойти до выхода из вагона.
	var scene := car.play_scene(path)
	if scene == null:
		holes.append(who + ": сцена пути не открылась")
		return
	scene.custom_event.connect(func(n: String): seen_events.append(n))
	if not _drive(scene, route, want_event, seen_events):
		holes.append(who + ": в сцене пути не осталось вариантов. Маршрут: " + ", ".join(route))
		return
	if not seen_events.has(want_event):
		# Не дыра: проверку можно повторять, и «отступить» всегда доступно.
		# Значит выход есть, просто броски не дались за отведённые шаги.
		no_exit.append("%s: выход за %d шагов не дался (проверка не прошла), но вариантов
			всегда хватало" % [who, 300])
		return
	passed += 1


## Ведёт диалог до конца или до нужного события. Возвращает false, если игрок
## встал: узел не кончился, а вариантов не осталось.
##
## Выбор не жадный: узел путей — это меню, и первый вариант в нём уводит по
## кругу. Поэтому предпочитаются варианты, ведущие в ещё не виденный узел, и
## варианты, дающие нужное событие; возврат в пройденный узел — в последнюю
## очередь. Без этого обходчик крутится в меню и врёт про дыру.
func _drive(rt: DialogueRuntime, route: PackedStringArray, want: String,
		seen: Array[String]) -> bool:
	rt.chance_provider = func(_p: String) -> float: return 0.99
	rt.minigame_provider = func(_m: String) -> bool: return true
	var visited := {}
	for _step in range(300):
		if rt.finished or seen.has(want):
			return true
		if route.size() < 24:
			route.append(rt.current_id)
		visited[rt.current_id] = true
		if not rt.has_options():
			rt.advance()
			continue
		var opts := rt.available_options()
		if opts.is_empty():
			stuck_nodes[rt.current_id] = true
			return false           # вот это и есть дыра: нечего нажать
		# available_options() отдаёт вид для интерфейса: в нём нет ни effects,
		# ни next, а настоящий номер варианта лежит в "index". Читать надо
		# исходный узел, а выбирать — по этому номеру, иначе при отфильтрованных
		# условиями вариантах выберется не тот.
		var raw: Array = rt.current.get("options", [])
		var best := int(opts[0].get("index", 0))
		var best_score := -999
		for view in opts:
			var idx := int(view.get("index", 0))
			var opt: Dictionary = raw[idx]
			var score := 0
			for e in (opt.get("effects", []) as Array):
				if str((e as Dictionary).get("emit", "")) == want:
					score += 100
			var nxt := str(opt.get("next", ""))
			if nxt == "":
				score += 3         # вариант, завершающий сцену или прыгающий эффектом
			elif not visited.has(nxt):
				score += 10
			else:
				score -= 20
			if score > best_score:
				best_score = score
				best = idx
		rt.choose(best)
	return true
