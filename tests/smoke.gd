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
	test_cold_open()
	test_trial_soft_reset_and_win()
	test_four_paths()
	test_seeds_and_tail()
	test_palette_and_transition()
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
	var rt := car.play_scene("return")
	rt.advance()
	check(rt != null and rt.current_id == "greet_stranger", "Шани говорит: незнакомцу — «вы опоздали»")
	check(events.has("bir_singh_stirs") == false, "столкновение Бира Сингха не срабатывает на Шани")
	car.talk_to("npc_bir_singh")
	check(events.has("bir_singh_stirs"), "столкновение из data/encounters срабатывает на npc_approached")
	rt = DialogueRuntime.new(ctx)
	rt.start(DialogueLoader.load_dialogue("car_01_shani_first"))
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
	var rt2 := car2.play_scene("return")
	rt2.advance()
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


func _car_for(ctx: GameContext) -> Car:
	var car := Car.new()
	root.add_child(car)
	car.setup(CarLoader.load_card("car_01"), ctx)
	car.enter()
	return car


## Гонит диалог по предпочтениям (см. _run_route), но на сцене вагона.
func _drive(rt: DialogueRuntime, prefs: Array, max_steps: int = 60) -> void:
	var steps := 0
	while not rt.finished and steps < max_steps:
		steps += 1
		if not rt.has_options():
			rt.advance()
			continue
		var opts := rt.available_options()
		var pick: int = opts[0]["index"]
		for view in opts:
			if prefs.has(view["text_key"]):
				pick = view["index"]
				break
		rt.choose(pick)


func test_cold_open() -> void:
	var ctx := _make_ctx(21, "bengali", "munshi", "m", [])
	var car := _car_for(ctx)
	check(car.custom != null, "custom_script вагона подключён")
	var events: Array[String] = []
	car.custom_event.connect(func(n: String): events.append(n))
	var locks: Array[float] = []
	car.custom.control_locked.connect(func(s: float): locks.append(s))
	var titles: Array[String] = []
	car.custom.title_card.connect(func(k: String): titles.append(k))
	var rt := car.play_scene("cold_open")
	check(rt.available_options().size() == 1 and rt.available_options()[0]["text_key"] == "co.stand", "холодное открытие: первое действие — встать")
	rt.choose(0)
	check(rt.available_options()[0]["text_key"] == "co.lantern", "второе действие — зажечь фонарь")
	rt.choose(0)
	check(ctx.world.get_flag("car_01.lantern_lit") == true, "фонарь зажжён (флаг)")
	_drive(rt, [])
	check(locks.size() == 1 and is_equal_approx(locks[0], 3.0), "три секунды приоткрытой двери — управление отобрано на 3 с")
	check(titles == ["co.title"] and ctx.texts.t("co.title") == "ДЕСЯТЬЮ ЧАСАМИ РАНЬШЕ", "титр «ДЕСЯТЬЮ ЧАСАМИ РАНЬШЕ»")
	check(rt.finished and ctx.world.get_flag("car_01.cold_open_done") == true, "холодное открытие завершено")
	car.free()


func test_trial_soft_reset_and_win() -> void:
	# Проигрыш: шесть проигранных раундов → мягкий откат, вагон на час раньше за каждый.
	var ctx := _make_ctx(22, "officer", "sepoy", "m", [])
	var car := _car_for(ctx)
	var resets: Array[String] = []
	car.custom.soft_reset_requested.connect(func(k: String): resets.append(k))
	var rt := car.play_scene("return")
	_drive(rt, [])
	check(car.custom.trial != null, "возврат в вагон запускает спор о часах")
	var trial: TrialRuntime = car.custom.trial
	var golds: Array[int] = []
	trial.gold_flash.connect(func(): golds.append(1))
	check(trial.current_round()["id"] == "name", "первый раунд — «имя»")
	trial.choose(2)   # крик — автоматический проигрыш
	check(trial.hours_lost == 1 and car.hours_lost == 1 and ctx.world.get_flag("car_01.clock_hours_lost") == 1, "проигранный раунд: стрелка на час назад, вагон на час раньше")
	check(golds.size() == 1, "золотая вспышка на повороте стрелки")
	check(trial.current_round()["id"] == "lateness", "второй раунд — «опоздание»")
	trial.choose(2)   # «на минуту!» — проигрыш
	check(trial.current_round()["id"] == "haste", "третий раунд — «спешка»")
	trial.choose(1)   # спорить — автоматический проигрыш
	check(trial.hours_lost == 3 and (car.npcs["npc_bir_singh"] as NpcNode).state == "patrol", "минус три часа: Бир Сингх делает обход")
	trial.choose(2); trial.choose(2); trial.choose(2)
	check(trial.finished and trial.outcome == "soft_reset", "минус шесть часов — мягкий откат, не смерть и не загрузка")
	check(resets.size() == 1 and car.hours_lost == 0 and ctx.world.get_flag("car_01.soft_resets") == 1, "откат сброшен: вагон снова на 20:30, счётчик откатов 1")
	check((car.npcs["npc_bir_singh"] as NpcNode).state == "default", "после отката NPC вернулись в исходное состояние")
	# Выигрыш: уступка в «спешке» побеждает; спор — проигрывает; критический аргумент — сразу.
	var t2: TrialRuntime = car.custom.start_trial()
	t2.choose(2)  # имя — проигрыш
	t2.choose(2)  # опоздание — проигрыш
	var s0 := t2.streak
	t2.choose(0)  # спешка — уступить
	check(t2.streak == s0 + 1 and t2.hours_lost == 2, "раунд «спешка» выигрывается только уступкой")
	ctx.world.set_flag("car_01.journal_seen", true)
	ctx.world.set_flag("ticket.smear_noticed", true)
	var opts := t2.options()
	check(opts[opts.size() - 1]["auto"] == "critical", "критический аргумент появляется при прочитанном журнале и замеченном затирании")
	t2.choose(-1)
	check(t2.finished and t2.outcome == "won" and ctx.world.get_flag("car_01.trial_won") == true, "критический аргумент обходит всё: испытание выиграно")
	# Ритм: попадание в такт — видимый модификатор проверки.
	var t3: TrialRuntime = car.custom.start_trial()
	t3.choose(0, 2)
	check(t3.last_check != null and t3.last_check.modifiers.size() >= 2 and int(t3.last_check.modifiers[t3.last_check.modifiers.size() - 1]["value"]) == 2, "модификатор такта раскрыт в разборе броска")
	var track := RhythmTrack.new()
	track.configure({"bpm": 60, "window_ms": 200})
	track.start(0)
	check(track.judge(1000)["hit"] and not track.judge(1400)["hit"], "ритм: попадание в окно и мимо")
	car.free()


func test_four_paths() -> void:
	var card := CarLoader.load_card("car_01")
	# Сила: кристальный резак, дверь выломана, Шани обижен, выход вперёд.
	var ctx := _make_ctx(23, "habshi", "sepoy", "m", [])
	var car := _car_for(ctx)
	var exits: Array[String] = []
	car.custom.exit_requested.connect(func(d: String): exits.append(d))
	car.custom._on_event("force_round"); car.custom._on_event("force_round")
	check(car.hours_lost == 1, "сила: по часу за каждые два раунда взлома")
	ctx.world.add_item("crystal_cutter")
	_drive(car.play_scene("force"), ["force.cutter"])
	check(ctx.world.get_flag("car_01.forced_door") == true and ctx.world.get_flag("car_01.shani_attitude") == "offended" and exits == ["forward"], "путь «сила»: дверь выломана, Шани обижен, выход вперёд")
	check(ctx.world.tail_order == ["car_01"] and ctx.world.progress == 1, "вагон ушёл в хвост, окно +1")
	car.free()
	# Обман: форма Бира Сингха снижает СЛ до 12; провал переводит часы; успех даёт дар.
	var ctx2 := _make_ctx(24, "loafer", "thug", "f", [])
	var car2 := _car_for(ctx2)
	_drive(car2.talk_to("npc_bir_singh"), ["bir_singh.uniform"])
	check(ctx2.world.has_item("conductor_uniform"), "форма кондуктора снята со спящего")
	var rt := car2.play_scene("deceit")
	var first := rt.available_options()[0]
	check(first["text_key"] == "deceit.relief_uniform" and int(first["check"]["dc"]) == 12, "с формой — СЛ 12")
	var tries := 0
	while not rt.finished and tries < 12:
		if rt.has_options():
			tries += 1
			rt.choose(0)
		else:
			rt.advance()
	check(rt.finished and ctx2.world.get_flag("car_01.shani_attitude") == "amused" and ctx2.world.has_item("gift_hour_ago"), "путь «обман»: Шани позабавлен, дар «Час назад» (попыток: %d, часов назад: %d)" % [tries, car2.hours_lost])
	check(car2.hours_lost == tries - 1, "каждый провал обмана — стрелка на час назад")
	car2.free()
	# Служба: три задачи, Ратан облегчает, журнал прочитан, вахана и дар без кражи.
	var ctx3 := _make_ctx(25, "anglo_indian", "telegraphist", "m", [])
	var car3 := _car_for(ctx3)
	_drive(car3.talk_to("npc_ratan"), ["ratan.ask_work", "ratan.leave"], 4)
	check(ctx3.world.get_flag("car_01.ratan_taught") == true, "Ратан научил работе вагона")
	car3.custom.simulated_inputs = {"mg_brake_wheel": [0.0, 0.1, 0.9], "mg_signal_lamps": {"rear": "red", "side": "green"}, "mg_ledger": {"notice": true}}
	_drive(car3.play_scene("service"), ["service.brake.go", "service.lamps.go", "service.ledger.go"])
	check(ctx3.world.get_flag("car_01.shift_worked") == true and ctx3.world.get_flag("car_01.journal_seen") == true, "путь «служба»: смена отработана, журнал прочитан")
	check(ctx3.world.has_item("vahana_crow_feather") and ctx3.world.has_item("gift_hour_ago") and ctx3.world.get_flag("car_01.shani_attitude") == "respectful", "служба: вахана и дар без кражи, Шани уважает")
	check(ctx3.world.get_flag("car_01.signal_error", false) == false, "стёкла поставлены верно")
	var ctx3b := _make_ctx(26, "dutch", "scholar" if false else "munshi", "m", [])
	var car3b := _car_for(ctx3b)
	car3b.custom.simulated_inputs = {"mg_brake_wheel": [0.0, 0.0, 0.0], "mg_signal_lamps": {"rear": "green", "side": "red"}, "mg_ledger": {"notice": false}}
	_drive(car3b.play_scene("service"), ["service.brake.go", "service.lamps.go", "service.ledger.go"])
	check(ctx3b.world.get_flag("car_01.signal_error") == true and ctx3b.world.get_flag("car_01.shift_worked") == true, "ошибка со стёклами записана флагом, смена всё равно отработана")
	car3.free(); car3b.free()
	# Остаться: фонарь = концовка 5, титры настоящие.
	var ctx4 := _make_ctx(27, "marwari", "babu", "f", [])
	var car4 := _car_for(ctx4)
	var endings_seen: Array[String] = []
	car4.custom.ending_requested.connect(func(e: String): endings_seen.append(e))
	_drive(car4.play_scene("stay"), ["stay.take", "stay.yes"])
	check(endings_seen == ["ending_5"], "путь «остаться»: снять фонарь — концовка 5")
	var endings := Endings.new(ctx4)
	var def := endings.play("ending_5")
	check(ctx4.world.get_flag("ending.reached") == 5 and ctx4.world.get_flag("car_01.lantern_taken") == true, "концовка 5 записана, фонарь снят")
	var lines := endings.credits_lines(def)
	check(lines.size() == 8 and lines[6].contains("Wizards of the Coast") and lines[6].contains("Creative Commons Attribution 4.0"), "титры: атрибуция SRD 5.2 (CC-BY-4.0)")
	check(def.get("detonation", true) == false, "концовка 5 — без детонации")
	check(car4.tail_scene_keys() == ["car_01.tail.lantern_taken"], "хвоста после фонаря нет")
	car4.free()


func test_seeds_and_tail() -> void:
	var ctx := _make_ctx(28, "chinese", "thug", "m", [])
	var car := _car_for(ctx)
	check(car.seed_items_present().size() == 12 and car.items.has("seed_mallick_notebook"), "12 семян на стеллажах, включая тетрадь Маллика")
	check(car.take_item("seed_mail_sack") and car.take_item("seed_child_shoe") and car.take_item("seed_mallick_notebook"), "три семени взяты")
	check(not car.take_item("seed_ice_box") and ctx.world.get_flag("car_01.seeds_taken") == 3, "четвёртое семя не берётся")
	check(not car.take_item("conductor_lantern"), "фонарь не берётся как предмет — только через «остаться»")
	var ctx2 := _make_ctx(28, "chinese", "thug", "m", [])
	ctx2.world.set_flag("prologue.mallick_notebook_taken", true)
	var car2 := _car_for(ctx2)
	check(car2.seed_items_present().size() == 11 and not car2.items.has("seed_mallick_notebook"), "тетрадь взята в прологе — на стеллаже её нет")
	ctx2.world.set_flag("car_01.forced_door", true)
	car2.apply_hour_state(2, {})
	check(car2.tail_scene_keys() == ["car_01.tail.forced_door", "car_01.tail.clock_hours_lost"], "хвостовой вариант по tail_rules: выломанная дверь + часы")
	ctx2.world.set_flag("car_01.forced_door", false)
	ctx2.world.set_flag("car_01.shift_worked", true)
	car2.apply_hour_state(0, {})
	check(car2.tail_scene_keys() == ["car_01.tail.shift_worked"], "хвостовой вариант: отработанная смена")
	# Хафиз: сказать вслух — вагон меняется.
	var rt := car2.talk_to("npc_hafiz")
	_drive(rt, ["hafiz.leave"], 3)
	rt = car2.talk_to("npc_hafiz")
	rt.advance()
	check(rt.current_id == "dead", "вторая попытка заговорить с Хафизом открывает правду")
	_drive(rt, ["hafiz.say"])
	check(ctx2.world.get_flag("car_01.hafiz_named") == true and (car2.npcs["npc_kanu"] as NpcNode).state == "crying", "сказано вслух: Кану плачет")
	var saved := ctx2.save("user://smoke_car_state.json")
	var loaded := GameContext.create(0, "ru")
	check(saved and loaded.load_from("user://smoke_car_state.json") and loaded.world.has_item("seed_mail_sack") == false and loaded.world.get_flag("car_01.hafiz_named") == true, "состояние вагона и инвентарь переживают сейв")
	car.free(); car2.free()


func test_palette_and_transition() -> void:
	var pal := Palette.new()
	check(pal.has("bollywood_dark") and pal.has("void") and pal.has("raj"), "палитры A10 зарегистрированы")
	pal.set_palette("bollywood_dark")
	# Числа палитры живут в data/palettes.json — тест сверяется с данными, не с копией.
	var authored := float(pal.params("bollywood_dark")["saturation"])
	check(is_equal_approx(float(pal.effective()["saturation"]), authored), "bollywood_dark: насыщенность из данных (%.2f)" % authored)
	pal.enter_trial()
	check(is_equal_approx(float(pal.effective()["saturation"]), 0.0) and pal.effective()["dither"] == "1bit", "испытание: время стоит — цвета нет, дизеринг")
	pal.set_colour_return(0.5)
	check(is_equal_approx(float(pal.effective()["saturation"]), authored * 0.5), "выигранные раунды возвращают цвет по шкале")
	pal.exit_trial()
	var env := Environment.new()
	pal.apply(env)
	check(not env.adjustment_enabled and is_equal_approx(env.ambient_light_energy, 0.045), "цвет кадра доводит шейдер, окружение даёт только рассеянный свет")
	# Слой грейдинга: базовый шейдер в обычном режиме, дизеринг в испытании.
	var grade := GradeLayer.new()
	grade.bind(pal)
	check(grade.rect.material == grade.theatrical_mat, "базовый режим — theatrical.gdshader")
	check(is_equal_approx(float(grade.theatrical_mat.get_shader_parameter("saturation")), authored), "палитра доехала до шейдера")
	pal.enter_trial()
	grade.refresh()
	check(grade.rect.material == grade.dither_mat, "режим испытания — dither_1bit.gdshader")
	check(is_equal_approx(float(grade.dither_mat.get_shader_parameter("colour_return")), 0.0), "цвета нет: время стоит")
	pal.set_colour_return(1.0)
	grade.refresh()
	check(is_equal_approx(float(grade.dither_mat.get_shader_parameter("colour_return")), 1.0), "цвет вернулся по выигранным раундам")
	grade.free()
	# Постановка и силуэты описаны данными, а не кодом
	var card := CarLoader.load_card("car_01")
	var st: Dictionary = card.get("stage", {})
	check(st.has("camera") and (st.get("layers", []) as Array).size() >= 6 and (st.get("props", []) as Array).size() >= 12, "театральная постановка в данных вагона: камера, кулисы, реквизит")
	var shani := CarLoader.load_npc("god_shani")
	var fig: Dictionary = shani.get("figure", {})
	check((fig.get("parts", []) as Array).size() >= 6, "силуэт Шани — сплошная фигура из %d контуров, а не прямоугольник" % (fig.get("parts", []) as Array).size())
	var smooth_contours := 0
	for p in fig["parts"] as Array:
		var pts: PackedVector2Array = StageBuilder.points_of(p)
		if pts.size() >= 16 and StageBuilder.polygon_mesh(pts).get_surface_count() > 0:
			smooth_contours += 1
	check(smooth_contours >= 6, "фигура нарисована кривыми: %d контуров по 16+ точек триангулируются" % smooth_contours)
	var figures := 0
	for npc_file in ["god_shani", "npc_ratan", "npc_bir_singh", "npc_hafiz", "npc_saraswati", "npc_monimala", "npc_kanu", "npc_dog"]:
		var doc := CarLoader.load_npc(npc_file)
		if (doc.get("figure", {}).get("parts", []) as Array).size() >= 4 and doc.has("silhouette"):
			figures += 1
	check(figures == 8, "нарисованы все восемь фигур вагона (%d)" % figures)
	var drawn_props := 0
	for pr in card.get("stage", {}).get("props", []):
		if (pr as Dictionary).has("parts"):
			drawn_props += 1
	check(drawn_props >= 15, "реквизит нарисован контурами: %d предметов" % drawn_props)
	# Встреча с присутствием: мир и бог живут на разных слоях видимости, иначе
	# монохром съедает бога, а бог светится сквозь скалы.
	var trial_def := TrialRuntime.load_def("trial_shani")
	var tst: Dictionary = trial_def.get("stage", {})
	check(tst.has("camera") and String(tst["camera"].get("projection", "")) == "perspective",
		"встреча снята длинным объективом снизу вверх")
	# Ниже уровня глаз человека (≈1,55 м) и с наклоном вверх: на присутствие
	# смотрят снизу, потому что смотрит ошарашенный человек.
	check(float(tst["camera"]["pos"][1]) < 1.55 and float(tst["camera"]["rot"][0]) > 5.0,
		"камера ниже уровня глаз и смотрит вверх: на присутствие смотрят снизу")
	var presence: Array = tst.get("presence", [])
	check(presence.size() >= 2, "присутствие — ворон и Шани: %d фигуры" % presence.size())
	var presence_parts := 0
	var presence_top := 0.0
	for pdef in presence:
		presence_parts += ((pdef as Dictionary).get("parts", []) as Array).size()
		check(StageBuilder.layer_mask(pdef) == 2, "присутствие на слое 2 (в цвете): %s" % pdef.get("id", "?"))
		for pt in (pdef as Dictionary).get("parts", []):
			var pts: PackedVector2Array = StageBuilder.points_of(pt)
			presence_top = maxf(presence_top, pts[pts.size() / 2].y)
	check(presence_parts >= 180, "присутствие нарисовано подробно: %d контуров" % presence_parts)
	# Присутствие рисуется по другому закону, чем люди (visual_direction §3.1):
	# лицо есть, иконография обязательна, и три тона с бликом на каждой форме.
	var deity: Dictionary = {}
	for pdef in presence:
		if String((pdef as Dictionary).get("id", "")) == "shani":
			deity = pdef
	check(not deity.is_empty(), "присутствие названо: группа «shani» есть в постановке")
	var tones := {}
	for pt in deity.get("parts", []):
		tones[var_to_str((pt as Dictionary).get("color", []))] = true
	check(tones.size() >= 14, "глазурь: %d тонов на фигуре, а не плоский силуэт" % tones.size())
	var deity_pts := 0
	for pt in deity.get("parts", []):
		deity_pts += (StageBuilder.points_of(pt)).size()
	check(deity_pts >= 1200, "фигура присутствия из %d точек кривых" % deity_pts)
	# Масштаб задают собака и человек: без них три роста не читаются.
	# Стилевой префикс генератора: он один держит сорок вагонов в одном стиле,
	# поэтому его наличие и содержание — тест, а не договорённость на словах.
	var tpl_path := "res://docs/asset_prompt_template.md"
	check(FileAccess.file_exists(tpl_path), "шаблон промпта генератора на месте")
	if FileAccess.file_exists(tpl_path):
		# Переносы строк в блоке промпта рвут фразы, поэтому сверяем по склеенному
		# тексту — так же, как их склеивает tools/asset_gen.py перед вызовом.
		var tpl := FileAccess.get_file_as_string(tpl_path).replace("\n", " ")
		check(tpl.contains("<!-- style-prefix -->"), "у шаблона есть якорь стилевого префикса")
		var flat_rules := 0
		for rule in ["no gradients", "no textures", "Flat vector illustration",
					 "no 3D render look", "Limited palette"]:
			if tpl.contains(rule):
				flat_rules += 1
		check(flat_rules == 5, "префикс запрещает градиенты, текстуры и объём: %d/5 правил" % flat_rules)
		check(tpl.contains("kind: presence") and tpl.contains("kind: person")
			and tpl.contains("kind: prop") and tpl.contains("kind: backdrop"),
			"в шаблоне описаны присутствие, человек, реквизит и задник")
		check(tpl.contains("Never a transparent") or tpl.contains("прозрачный фон не просить")
			or tpl.contains("Никогда не просить прозрачный фон"),
			"записано правило про прозрачный фон: генератор впечатает шахматку")

	# Контуры, полученные трассировкой референса, обязаны триангулироваться —
	# иначе движок молча не нарисует ничего (StageBuilder.polygon_mesh).
	var traced_dir := DirAccess.open("res://data/traced")
	if traced_dir != null:
		var traced_files := 0
		var traced_parts := 0
		var bad := 0
		for fname in traced_dir.get_files():
			if not fname.ends_with(".json"):
				continue
			traced_files += 1
			var parsed = JSON.parse_string(
				FileAccess.get_file_as_string("res://data/traced/" + fname))
			for pt in (parsed as Dictionary).get("parts", []):
				traced_parts += 1
				var pts: PackedVector2Array = StageBuilder.points_of(pt)
				if pts.size() < 3 or StageBuilder.polygon_mesh(pts).get_surface_count() == 0:
					bad += 1
		if traced_files > 0:
			check(bad == 0, "трассированные контуры триангулируются: %d из %d негодных"
				% [bad, traced_parts])
			check(traced_parts >= 40, "в трассировке есть чем рисовать: %d контуров" % traced_parts)

	var scale_cues := 0
	for pr in tst.get("props", []):
		var pid := String((pr as Dictionary).get("id", ""))
		if pid == "dog" or pid.begins_with("bystander") or pid == "witness":
			scale_cues += 1
	check(scale_cues >= 2, "в кадре есть собака и человек для масштаба: %d" % scale_cues)
	check(presence_top > 5.2, "Шани выше трёх человеческих ростов: %.1f м" % presence_top)
	var world_layers := 0
	for wl in tst.get("layers", []) + tst.get("props", []):
		if StageBuilder.layer_mask(wl) == 4:
			world_layers += 1
	check(world_layers >= 15, "мир Шани на слое 3 (в точках): %d планов" % world_layers)
	var ctx := _make_ctx(29, "armenian", "babu", "m", [])
	var tr := TransitionRuntime.new(ctx)
	var steps: Array[String] = []
	tr.step.connect(func(k: String, _s: float, _i: int): steps.append(k))
	var done: Array[String] = []
	tr.finished.connect(func(v: String): done.append(v))
	var rolls_before := ctx.checks.history.size()
	tr.play("night_bengal")
	check(not tr.can_skip(), "первый просмотр ритуала не пропускается")
	while done.is_empty():
		tr.next_step()
	check(steps.size() == 5 and done == ["night_bengal"] and ctx.checks.history.size() == rolls_before, "ритуал перелезания: 5 шагов, без единого броска")
	check(tr.total_seconds() >= 20.0 and tr.total_seconds() <= 40.0, "ритуал 20–40 секунд")
	tr.play("night_bengal")
	check(tr.can_skip(), "после первого просмотра вариант можно пропустить")
	ctx.world.set_flag("car_01.forced_door", true)
	check(tr.pick_variant("night_bengal") == "night_bengal_forced", "выломанная дверь меняет вариант ритуала")
