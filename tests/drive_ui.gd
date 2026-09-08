extends Node
## Драйвер интерфейса: гоняет настоящую сцену игры под экраном, нажимает кнопки
## и снимает кадры. Нужен, чтобы смотреть на игру, а не только на тесты.
##
## Запуск:
##   xvfb-run -s "-screen 0 1280x720x24" godot --path . \
##     --display-driver x11 --rendering-driver opengl3 tests/drive_ui.tscn
## Кадры: user://shots/NN_имя.png, разбор — user://shots/log.txt
##
## Драйвер ждёт появления вариантов, а не фиксированное число кадров: иначе он
## обгоняет титры и таймеры игры. Сценарий — сквозной проход среза.

const SHOTS := "user://shots/"
const WAIT_LIMIT := 900   # кадров на ожидание одного экрана

var main: Node
var shot_no: int = 0
var log_lines: Array[String] = []


var scenario: String = "slice"


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--scenario="):
			scenario = arg.trim_prefix("--scenario=")
	DirAccess.make_dir_recursive_absolute(SHOTS)
	main = load("res://src/main.tscn").instantiate()
	add_child(main)
	await _frames(10)
	if scenario == "paths":
		await _run_paths()
	else:
		await _run()
	_write_log()
	get_tree().quit()


## Второй сценарий: пути тормозного вагона и концовка 5 — через прямой вход.
func _run_paths() -> void:
	await _debug_press("Сразу в вагон")
	await _click_until(func(): return _has_option("Отработать смену"), 4)
	await _shot("paths_hub", "Узел путей: ложь о выходе, сила, обман, служба, фонарь.")
	await _click_text("Где здесь выход")
	await _shot("paths_exit_lie", "Ложь Шани о выходе: паровоз и терпение.")
	await _click_until(func(): return _has_option("Отработать смену"), 4)
	await _click_text("Отработать смену")
	await _shot("service_start", "Служба: три задачи тормозного вагона.")
	await _click_until(func(): return _dialogue_text().contains("опись дописана") or _dialogue_text().contains("открывает дверь"), 12)
	await _shot("service_done", "Смена отработана: вахана и дар без кражи, Шани открывает дверь сам.")
	await _click_until(func(): return main.transition_ui.visible, 4)
	await _wait_transition()
	await _shot("transition", "Ритуал перелезания: постановка без бросков, 20–40 секунд.")
	await _advance_transition()
	await _shot("after_transition", "Ритуал окончен, следующий вагон — заглушка M3.")
	# Фонарь: концовка 5 с настоящими титрами
	await _debug_press("Узел путей")
	await _click_until(func(): return _has_option("Снять фонарь"), 4)
	await _click_text("Снять фонарь с крюка")
	await _shot("stay_hook", "Фонарь на крюке: снять — значит держать момент.")
	await _click_text("Снять фонарь и повесить")
	await _shot("stay_question", "Один спокойный вопрос Шани.")
	await _click_text("Да")
	await _frames(20)
	await _shot("ending_5", "Концовка 5 «Фонарь»: настоящие титры с атрибуцией SRD.")


## Жмёт первый вариант, пока в реплике не появится нужный кусок текста.
func _advance_to(fragment: String, limit: int) -> void:
	for _i in range(limit):
		if _dialogue_text().contains(fragment):
			return
		await _click(0)
	if not _dialogue_text().contains(fragment):
		_note("до «%s» не дошли за %d нажатий (сейчас: %s)" % [fragment, limit, _dialogue_text().substr(0, 40)])


## Кнопки панели разработчика: она спрятана во время игры, показать по F1.
func _debug_press(fragment: String) -> void:
	main.debug_panel.visible = true
	await _frames(2)
	_press_text(fragment)
	main.debug_panel.visible = false
	await _frames(6)


func _has_option(fragment: String) -> bool:
	for b in main.dialogue_ui.option_buttons:
		if (b as Button).text.contains(fragment):
			return true
	return false


func _wait_transition() -> void:
	for _i in range(WAIT_LIMIT):
		if main.transition_ui.visible:
			return
		await get_tree().process_frame
	_note("ритуал перелезания не начался")


## Ритуал листается своей кнопкой, не вариантами диалога.
func _advance_transition() -> void:
	for _i in range(12):
		if not main.transition_ui.visible:
			return
		main.transition_ui.next_button.pressed.emit()
		await _frames(4)
	_note("ритуал не закончился за 12 шагов")


func _dialogue_text() -> String:
	return main.dialogue_ui.text_label.text


func _click_text(fragment: String) -> void:
	await _wait_options()
	for b in main.dialogue_ui.option_buttons:
		if (b as Button).text.contains(fragment):
			(b as Button).pressed.emit()
			await _frames(6)
			return
	_note("варианта с «%s» нет" % fragment)
	await _click(0)


# --- сценарий ----------------------------------------------------------------

func _run() -> void:
	await _shot("start_screen", "Стартовый экран: происхождение, класс, пол, теги пролога, seed.")
	_press_text("Начать")

	await _wait_options()
	await _shot("cold_open_dark", "Холодное открытие: темнота, никого не видно. Единственное действие — встать.")
	await _click(0)
	await _shot("cold_open_lantern", "Второе действие — фонарь на крюке.")
	await _click(0)
	await _shot("cold_open_lit", "Фонарь зажжён: свет, спящий кондуктор, часы, стеллажи. Люди стали видны.")
	await _click(0)
	await _shot("cold_open_silhouette", "Силуэт в глубине.")
	await _click(0)
	await _shot("cold_open_door", "Дверь приоткрыта: за ней дневной свет. Управление отобрано.")
	await _click_until(func(): return main.title_card.visible, 6)
	await _shot("cold_open_title", "Титр «ДЕСЯТЬЮ ЧАСАМИ РАНЬШЕ». Пролог начнётся после него.")

	await _wait_options()
	await _shot("prologue_intro", "Пролог: часы 20:00, поезд в 20:30. «Успеваем».")
	await _click(0)
	await _shot("prologue_detainer", "Бит 1: задерживающий по тегам пролога. Цена каждого варианта в минутах.")
	await _click(1)   # отвязаться: проверка, у провала своя цена
	await _shot("prologue_check", "Видимая проверка d20: кубик, модификаторы, СЛ, исход.")
	await _dismiss_check()
	await _shot("prologue_after_check", "Часы в HUD сдвинулись, слева видно, что именно съело минуты.")
	await _advance_to("Хугли", 6)
	await _shot("prologue_crossing", "Бит 2: переправа. У моста показан шанс, что он разведён.")
	await _click(0)
	await _shot("prologue_chance", "Бросок шанса виден так же, как проверка.")
	await _dismiss_check()
	await _advance_to("святилище", 6)
	await _shot("prologue_shrine", "Бит 3: святилище. Три цены: 7, 3 и 5 минут.")
	await _click(0)
	await _advance_to("Хаура", 6)
	await _shot("prologue_howrah", "Бит 4: Хаура. Трение зависит от происхождения и пола.")
	await _advance_to("Имя смазало", 8)
	await _shot("prologue_dcruz", "Контролёр Д’Круз смотрит на билет и не может прочесть имя.")
	await _advance_to("Часы над платформой", 8)
	await _shot("prologue_platform", "Бит 5: платформа, поезд уже идёт.")
	await _advance_to("Прыжок", 6)
	await _shot("prologue_jump", "Прыжок — единственные полторы секунды без управления.")

	await _click_until(func(): return _dialogue_text().contains("силуэт") or _dialogue_text().contains("Темнота"), 6)
	await _shot("return_to_car", "Возврат в вагон: тот же кадр, силуэт поворачивается.")
	await _click_until(func(): return main.trial_ui.visible and not main.trial_ui._buttons.is_empty(), 12)
	await _shot("trial_shani", "Спор о часах: регулятор, раунды подряд, ритм-шкала, варианты с СЛ.")
	await _click_trial(main.trial_ui._buttons.size() - 1)
	await _shot("trial_clock_turned", "Проигранный раунд: стрелка на час назад, вагон стал на час раньше.")
	await _click_trial(0)
	await _shot("trial_round_two", "Следующий раунд идёт в такт колёс.")


# --- ожидания ---------------------------------------------------------------

func _frames(n: int) -> void:
	for _i in range(n):
		await get_tree().process_frame


## Ждёт, пока в панели диалога появятся варианты (или всплывёт панель броска,
## или начнётся испытание — тогда диалог уже не при делах).
func _wait_options() -> bool:
	for _i in range(WAIT_LIMIT):
		if main.check_ui.visible:
			return true
		if main.trial_ui.visible and not main.trial_ui._buttons.is_empty():
			return false
		if main.dialogue_ui.visible and not main.dialogue_ui.option_buttons.is_empty():
			return true
		await get_tree().process_frame
	_note("варианты не появились за %d кадров" % WAIT_LIMIT)
	return false


## Жмёт «Дальше» до нужного состояния: титра, испытания и прочих переходов.
func _click_until(is_ready: Callable, limit: int) -> void:
	for _i in range(limit):
		if bool(is_ready.call()):
			return
		await _click(0)
	if not bool(is_ready.call()):
		_note("состояние не наступило за %d нажатий" % limit)


# --- действия ---------------------------------------------------------------

func _click(index: int) -> void:
	if not await _wait_options():
		return
	if main.check_ui.visible:
		await _dismiss_check()
		if not await _wait_options():
			return
	var buttons: Array = main.dialogue_ui.option_buttons
	if index >= buttons.size():
		_note("варианта %d нет (всего %d) — жму первый" % [index, buttons.size()])
		index = 0
	if buttons.is_empty():
		return
	(buttons[index] as Button).pressed.emit()
	await _frames(4)


func _click_trial(index: int) -> void:
	var buttons: Array = main.trial_ui._buttons
	if index < 0 or index >= buttons.size():
		_note("варианта испытания %d нет (всего %d)" % [index, buttons.size()])
		return
	(buttons[index] as Button).pressed.emit()
	await _frames(6)
	if main.check_ui.visible:
		await _dismiss_check()


func _dismiss_check() -> void:
	if main.check_ui.visible:
		main.check_ui.hide_result()
	await _frames(4)


func _press_text(fragment: String) -> void:
	var found := _find_button(get_tree().root, fragment)
	if found != null:
		found.pressed.emit()
	else:
		_note("кнопка «%s» не найдена" % fragment)


func _find_button(node: Node, fragment: String) -> Button:
	if node is Button and (node as Button).visible and (node as Button).text.contains(fragment):
		return node
	for c in node.get_children():
		var b := _find_button(c, fragment)
		if b != null:
			return b
	return null


func _shot(shot_name: String, note: String = "") -> void:
	shot_no += 1
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png("%s%02d_%s.png" % [SHOTS, shot_no, shot_name])
	log_lines.append("%02d_%s.png" % [shot_no, shot_name])
	if note != "":
		log_lines.append("    " + note)


func _note(text: String) -> void:
	log_lines.append("    ! " + text)


func _write_log() -> void:
	var f := FileAccess.open(SHOTS + "log.txt", FileAccess.WRITE)
	if f != null:
		f.store_string("\n".join(log_lines))
		f.close()
	print("\n".join(log_lines))
	print("\nкадров: %d" % shot_no)
