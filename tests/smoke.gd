extends SceneTree
## Headless smoke-тест BOMBAY MAIL. Запуск: godot --headless --path . -s tests/smoke.gd
## Приёмка задачи 1: вагон грузится из car_01.json, NPC говорит, проверка d20
## катится с видимым результатом, сейв/лоад работают.
## Приёмка задачи 2: квест проходится тремя маршрутами, все три опаздывают,
## все три дают разный набор флагов; цена каждого выбора видна до выбора.

var failures: Array[String] = []
var passed: int = 0


func check(cond: bool, what: String) -> void:
	if cond:
		passed += 1
	else:
		failures.append(what)
		printerr("FAIL: " + what)


func _init() -> void:
	test_core_and_save()
	test_character()
	test_checks_visible()
	test_car()
	test_quest_three_routes()
	print("\nsmoke: %d проверок пройдено, %d провалено" % [passed, failures.size()])
	for f in failures:
		print("  - " + f)
	quit(0 if failures.is_empty() else 1)


func _make_ctx(seed_v: int, origin: String, class_id: String, sex: String, tags: Array) -> GameContext:
	var ctx := GameContext.create(seed_v, "ru")
	ctx.set_character(ctx.char_data.build(origin, class_id, sex))
	for t in tags:
		ctx.world.add_tag(t)
	return ctx


func test_core_and_save() -> void:
	var ctx := _make_ctx(7, "officer", "sepoy", "m", ["union_seed"])
	check(ctx.registry.has_flag("prologue.detainer_id"), "реестр флагов загружен")
	check(not ctx.world.set_flag("no.such.flag", true), "незарегистрированный флаг отвергается")
	check(not ctx.world.set_flag("prologue.detainer_id", "nobody"), "enum-флаг отвергает чужое значение")
	check(ctx.world.set_flag("prologue.detainer_id", "horipod"), "enum-флаг принимает своё значение")
	check(ctx.world.has_tag("union_seed"), "тег пролога = флаг prologue.union_seed")
	ctx.clock.configure(1200, 1230)
	ctx.clock.spend(11, "lhh.reason.road_ghat")
	ctx.rng.d20()
	var path := "user://smoke_world_state.json"
	check(ctx.save(path), "сейв записан")
	var loaded := GameContext.create(0, "ru")
	check(loaded.load_from(path), "сейв прочитан")
	check(loaded.world.get_flag("prologue.detainer_id") == "horipod", "флаг пережил сейв/лоад")
	check(loaded.world.clock_minutes == 1211, "часы пережили сейв/лоад")
	check(loaded.character != null and loaded.character.origin_id == "officer", "персонаж пережил сейв/лоад")
	check(loaded.rng.d20() == ctx.rng.d20(), "RNG продолжает ту же последовательность после лоада")
	check(loaded.world.ticket.has("ticket_name") and loaded.world.detonation.has("pressure"), "поля WorldState по B4 присутствуют")


func test_character() -> void:
	var ctx := GameContext.create(1, "ru")
	check(ctx.char_data.origins.size() == 11, "11 происхождений")
	check(ctx.char_data.classes.size() == 9, "9 классов")
	var ch := ctx.char_data.build("marwari", "babu", "f")
	check(ch.abilities["cha"] == 15 and ch.abilities["int"] == 16, "стандартный массив + прибавки происхождения (cha 15, int 14+2)")
	check(ch.modifier("int") == 3, "модификатор int 16 = +3")
	check(ch.is_proficient("persuasion") and ch.is_proficient("insight"), "навыки происхождения и класса")
	check(ch.skill_modifier("persuasion", ctx.char_data) == 4, "Убеждение: +2 (cha) +2 (мастерство)")
	check(ch.axes["sex"] == "woman" and ch.axes["credit"] == "solvent", "оси отношения заполнены")
	check(Character.from_dict(ch.to_dict()).skill_modifier("insight", ctx.char_data) == ch.skill_modifier("insight", ctx.char_data), "персонаж сериализуется без потерь")


func test_checks_visible() -> void:
	var ctx := _make_ctx(3, "bengali", "babu", "m", [])
	var seen: Array[CheckResult] = []
	ctx.checks.check_rolled.connect(func(r: CheckResult): seen.append(r))
	var ui := CheckUi.new()
	root.add_child(ui)
	ui.bind(ctx)
	var r := ctx.checks.roll(ctx.character, {"skill": "persuasion", "dc": 12, "label_key": "lhh.check.persuasion"})
	check(seen.size() == 1 and seen[0] == r, "каждый бросок уходит сигналом check_rolled")
	check(r.die >= 1 and r.die <= 20, "d20 в пределах 1–20")
	check(r.modifiers.size() == 2, "модификаторы раскрыты (характеристика + мастерство)")
	check(r.total == r.die + r.modifier_sum(), "итог = кубик + модификаторы")
	check(ui.visible and ui.die_label.text == str(r.die) and ui.mods_label.text.length() > 0, "UI проверки показывает кубик и модификаторы")
	check(ui.total_label.text.contains("12"), "UI показывает СЛ")
	var c := ctx.checks.roll_chance("lhh.chance.bridge", 0.75)
	check(c.kind == "chance" and c.threshold == 15 and ui.title_label.text.contains("75"), "бросок шанса виден с порогом и процентом")
	var described := r.describe(ctx.texts)
	check(described.contains("d20") and described.contains("СЛ 12"), "текстовый разбор проверки: " + described)
	ui.free()


func test_car() -> void:
	var ctx := _make_ctx(5, "loafer", "thug", "m", [])
	var card := CarLoader.load_card("car_01")
	check(card.get("id", "") == "car_01" and card.get("palette", "") == "bollywood_dark", "карточка car_01 загружена")
	var car := Car.new()
	root.add_child(car)
	car.setup(card, ctx)
	car.enter()
	check(car.npcs.size() == 6, "6 NPC заспавнены; пёс и Монимала скрыты условиями (%d)" % car.npcs.size())
	check(ctx.world.location["car"] == "car_01" and ctx.world.cars["car_01"]["visited"], "вход в вагон записан в состояние")
	var events: Array[String] = []
	car.custom_event.connect(func(n: String): events.append(n))
	var rt := car.talk_to("god_shani")
	check(rt != null and rt.current_id == "greet_stranger", "Шани говорит: незнакомцу — «вы опоздали»")
	check(events.has("bir_singh_stirs") == false, "столкновение Бира Сингха не срабатывает на Шани")
	car.talk_to("npc_bir_singh")
	check(events.has("bir_singh_stirs"), "столкновение из data/encounters срабатывает на npc_approached")
	rt.advance()
	check(rt.current_id == "who" and rt.has_options(), "диалог дошёл до выбора")
	rt.choose(0)
	check(rt.last_check != null and rt.last_check.skill_used == "insight", "проверка внутри реплики: Проницательность")
	check(rt.finished and (rt.current_id == "look_ok" or rt.current_id == "look_fail"), "провал не прячется: своя ветка у успеха и провала")
	check(ctx.world.get_flag("car_01.shani_greeted") == true, "on_enter выставил флаг")
	# С shrine_stopped первая реплика Шани другая (жемчужина)
	var ctx2 := _make_ctx(5, "loafer", "thug", "m", [])
	ctx2.world.set_flag("prologue.shrine_stopped", true)
	var car2 := Car.new()
	root.add_child(car2)
	car2.setup(card, ctx2)
	var rt2 := car2.talk_to("god_shani")
	check(rt2.current_id == "greet_known", "при shrine_stopped Шани здоровается как со знакомым")
	# Монимала едет в тормозном только при helped
	var ctx3 := _make_ctx(5, "loafer", "thug", "f", [])
	ctx3.world.set_flag("prologue.detainer_id", "widow_monimala")
	ctx3.world.set_flag("prologue.detainer_resolution", "helped")
	ctx3.world.set_flag("prologue.dog_followed", true)
	var car3 := Car.new()
	root.add_child(car3)
	car3.setup(card, ctx3)
	check(car3.npcs.has("npc_monimala") and car3.npcs.has("npc_dog"), "условные NPC появляются по флагам пролога")
	car.free()
	car2.free()
	car3.free()


## Гонит квест по предпочтениям: на каждом выборе берёт первый вариант из prefs,
## иначе первый доступный. Возвращает снимок флагов.
func _run_route(ctx: GameContext, prefs: Array, label: String) -> Dictionary:
	var quest := QuestRuntime.new(ctx)
	var rt := quest.start("quest_last_half_hour")
	var ui := DialogueUi.new()
	root.add_child(ui)
	ui.bind(ctx)
	ui.attach(rt)
	var captions: Array[String] = []
	var steps := 0
	while not rt.finished and steps < 200:
		steps += 1
		if not rt.has_options():
			rt.advance()
			continue
		var opts := rt.available_options()
		var pick: int = opts[0]["index"]
		for view in opts:
			if prefs.has(view["text_key"]):
				pick = view["index"]
				captions.append(ui.option_caption(view))
				break
		rt.choose(pick)
	check(rt.finished, label + ": квест дошёл до конца за %d шагов" % steps)
	check(ctx.world.get_flag("prologue.completed") == true, label + ": prologue.completed")
	check(ctx.clock.minutes_late() >= 1, label + ": опоздал на %d мин (часы %s)" % [ctx.clock.minutes_late(), ctx.clock.now_string()])
	check(int(ctx.world.get_flag("prologue.minutes_late", 0)) == ctx.clock.minutes_late(), label + ": опоздание записано флагом")
	var priced := 0
	for c in captions:
		if c.contains("мин"):
			priced += 1
	check(priced >= 3 and captions.size() >= 4, label + ": цена в минутах видна до выбора (%d из %d подписей с ценой)" % [priced, captions.size()])
	check(captions.size() > 0 and captions[0].contains("мин"), label + ": бит 1 — цена в подписи: " + (captions[0] if captions.size() > 0 else ""))
	ui.free()
	var snap := quest.output_snapshot()
	print("  %s → %s, поздно на %d: %s" % [label, snap["clock"], snap["minutes_late"], str(snap.get("prologue.detainer_id")) + "/" + str(snap.get("prologue.detainer_resolution")) + "/" + str(snap.get("prologue.crossing")) + "/" + str(snap.get("prologue.howrah_friction"))])
	return snap


func test_quest_three_routes() -> void:
	var a := _run_route(_make_ctx(11, "officer", "sepoy", "m", ["union_seed"]),
		["lhh.d.nibaron_das.hide", "lhh.crossing.bridge", "lhh.shrine.stop_oil", "lhh.howrah.jumma.extra", "lhh.platform.run"], "A офицер/Нибарон")
	var b := _run_route(_make_ctx(12, "loafer", "thug", "f", ["widow_saved", "census_answered"]),
		["lhh.d.widow_monimala.carry", "lhh.crossing.ferry", "lhh.shrine.pass_by", "lhh.howrah.jumma.decline", "lhh.platform.barrow"], "B лоафер♀/Монимала")
	var c := _run_route(_make_ctx(13, "chinese", "telegraphist", "m", []),
		["lhh.d.horipod.steal", "lhh.crossing.boat_pay", "lhh.shrine.speak_leave", "lhh.howrah.jumma.hire", "lhh.platform.climb"], "C китаец/Хорипод")
	check(a["prologue.detainer_id"] == "nibaron_das" and b["prologue.detainer_id"] == "widow_monimala" and c["prologue.detainer_id"] == "horipod", "задерживающий выбран по тегам, без тегов — Хорипод")
	check(b["prologue.detainer_resolution"] == "helped" and c["prologue.detainer_resolution"] == "pushed", "исход задерживающего записан")
	check(a["prologue.shrine_stopped"] == true and b.get("prologue.dog_followed") == true and c.get("prologue.shrine_spoke") == true, "святилище: три разных следа")
	check(a["prologue.ferry_companion"] == "none" and b["prologue.ferry_companion"] == "bipin", "попутчик: мостом — никого, паромом — Бипин")
	check(a["prologue.howrah_friction"] == "acquaintance" and b["prologue.howrah_friction"] == "ladies_entrance" and c["prologue.howrah_friction"] == "unrecorded", "трение Хауры по происхождению и полу")
	check(a.get("prologue.knows_sealed_crate") == true and not c.has("prologue.knows_sealed_crate"), "Джумма: лишняя анна — знание об опечатанном ящике")
	check(a != b and b != c and a != c, "три маршрута — три разных набора флагов")
	var a_flags := a.duplicate(); a_flags.erase("minutes_late"); a_flags.erase("clock")
	var b_flags := b.duplicate(); b_flags.erase("minutes_late"); b_flags.erase("clock")
	check(a_flags != b_flags, "разница не только в минутах, но и в поезде")
	# Приоритет задерживающих: при двух тегах берётся первый в таблице
	check(b["prologue.detainer_id"] == "widow_monimala", "при widow_saved + census_answered приходит Монимала (порядок таблицы)")
