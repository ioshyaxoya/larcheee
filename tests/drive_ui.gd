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
	elif scenario == "scene":
		await _run_scene()
	elif scenario == "shani":
		await _run_shani()
	elif scenario == "glitchcheck":
		await _run_glitch_check()
	elif scenario == "letsplay":
		await _run_letsplay()
	elif scenario == "motion":
		await _run_motion()
	elif scenario == "film":
		await _run_film()
	elif scenario == "walk":
		await _run_walk()
	else:
		await _run()
	_write_log()
	get_tree().quit()


## Третий сценарий: только сцена, без интерфейса — смотреть на постановку.
func _run_scene() -> void:
	await _debug_press("Сразу в вагон")
	await _wait_options()
	main.dialogue_ui.visible = false
	main.hud.visible = false
	main.debug_panel.visible = false
	await _frames(10)
	await _shot("scene_lit", "Вагон при зажжённом фонаре, без интерфейса.")
	# Ближе к посту кондуктора
	main.camera.position = Vector3(0.0, 1.55, 2.6)
	main.camera.rotation_degrees = Vector3(-7.0, 0.0, 0.0)
	main.camera.size = 3.4
	await _frames(6)
	await _shot("scene_close", "Пост кондуктора вблизи: печка, штурвал, конторка, фигуры.")
	# Вид в глубину багажного корпуса
	main.camera.position = Vector3(0.0, 2.2, 0.0)
	main.camera.rotation_degrees = Vector3(-6.0, 0.0, 0.0)
	main.camera.size = 4.2
	await _frames(6)
	await _shot("scene_depth", "Стеллажи уходят в темноту.")
	# Тот же вагон в режиме испытания: монохром с дизерингом
	main.palette.enter_trial()
	main.palette.set_colour_return(0.0)
	main._apply_palette()
	main.camera.position = Vector3(0.0, 1.75, 4.6)
	main.camera.rotation_degrees = Vector3(-9.0, 0.0, 0.0)
	main.camera.size = 4.4
	await _frames(6)
	await _shot("scene_trial_mono", "Испытание: время стоит, цвета нет.")
	main.palette.set_colour_return(0.6)
	main._apply_palette()
	await _frames(6)
	await _shot("scene_trial_colour", "Два выигранных раунда: цвет возвращается.")


## Четвёртый сценарий: встреча с присутствием. Смотреть на удар, без интерфейса.
func _run_shani() -> void:
	await _debug_press("Сразу в вагон")
	await _wait_options()
	await _debug_press("Спор о часах")
	await _frames(12)
	main.dialogue_ui.visible = false
	main.trial_ui.visible = false
	main.hud.visible = false
	main.debug_panel.visible = false
	main.check_ui.visible = false
	await _frames(8)
	await _shot("shani_meeting", "Встреча: присутствие в три роста на вороне, мир в точках.")
	# Кадр одного присутствия с альфой: это же и есть «референс на сплошном
	# фоне», с которым работает трассировщик (tools/trace_to_contours.py).
	await RenderingServer.frame_post_draw
	var pres: Image = main.presence_viewport.get_texture().get_image()
	pres.save_png(SHOTS + "presence_alpha.png")
	log_lines.append("presence_alpha.png\n    Присутствие отдельно, с альфой — вход для трассировщика.")
	main.grade.set_glitch(0.0)
	main._apply_palette()
	await _frames(6)
	await _shot("shani_no_glitch", "Тот же кадр без сбоя: мир Шани держится.")
	main.grade.set_glitch(1.0)
	main._apply_palette()
	await _frames(6)
	await _shot("shani_glitch", "Сбой: сквозь мир полосами проступают стены вагона.")
	main.palette.set_colour_return(0.66)
	main.grade.set_glitch(0.2)
	main._apply_palette()
	await _frames(6)
	await _shot("shani_colour", "Два выигранных раунда: цвет возвращается в мир.")
	# Обойти сцену: присутствие видно и сбоку, как и обещает §5.
	main.grade.set_glitch(0.35)
	main.palette.set_colour_return(0.0)
	main._apply_palette()
	for cam in [main.trial_camera, main.presence_camera]:
		cam.position = Vector3(-6.6, 1.5, 6.4)
		cam.rotation_degrees = Vector3(8.0, -46.0, 0.0)
	await _frames(6)
	await _shot("shani_side", "Сцена застыла: её можно обойти. Тот же миг с другого угла.")
	for cam in [main.trial_camera, main.presence_camera]:
		cam.position = Vector3(0.0, 7.6, 7.2)
		cam.rotation_degrees = Vector3(-24.0, 0.0, 0.0)
	await _frames(6)
	await _shot("shani_above", "И сверху: у ворона видно, на чём он стоит.")


## Прогулка по вагону: игрок идёт сам, камера идёт за ним и меняет кадр по
## зонам. Ввод подаётся действиями, как от живого игрока, а не телепортом.
func _run_walk() -> void:
	await _debug_press("Сразу в вагон")
	await _wait_options()
	main.dialogue_ui.visible = false
	main.hud.visible = false
	main.debug_panel.visible = false
	await _frames(10)
	if main.player == null:
		_note("игрока нет — движение не подключено")
		return
	main.player.locked = false
	await _roll(16)
	# Вглубь вагона: тамбур → пост → багажный корпус → глубина.
	await _hold("ui_up", 190)
	await _roll(20)
	# Вправо к штурвалу, влево к печке — камера ведёт за игроком.
	await _hold("ui_right", 46)
	await _roll(14)
	await _hold("ui_left", 92)
	await _roll(14)
	# И назад к тамбуру: кадр меняется в обратную сторону.
	await _hold("ui_down", 150)
	await _roll(24)
	log_lines.append("film_*.jpg\n    Прогулка: %d кадров." % film_no)


## Держать действие n кадров, записывая каждый: так ходит живой игрок.
func _hold(action: String, frames: int) -> void:
	Input.action_press(action)
	await _roll(frames)
	Input.action_release(action)


## Настоящая запись прохода: не по кадру на реплику, а подряд, чтобы было
## видно движение — качку вагона, качание ламп, мигание топки, расхаживание
## ворона и набор текста по буквам. Кадры пишутся в JPEG на 960×540, иначе
## полутора тысячам PNG не хватит ни места, ни времени.
var film_no := 0


func _roll(n: int) -> void:
	for _i in range(n):
		await RenderingServer.frame_post_draw
		var img: Image = get_viewport().get_texture().get_image()
		img.resize(960, 540, Image.INTERPOLATE_LANCZOS)
		img.save_jpg(SHOTS + "film_%05d.jpg" % film_no, 0.86)
		film_no += 1


## Реплика: дать машинке допечатать, дать прочесть, нажать. Всё это в кадрах.
func _film_beat(hold: int = 30) -> bool:
	await _roll(10)
	for _i in range(90):
		if not main.dialogue_ui.typing:
			break
		await _roll(2)
	await _roll(hold)
	if main.check_ui.visible:
		await _roll(14)
		await _dismiss_check()
		await _roll(8)
		return true
	if main.dialogue_ui.option_buttons.is_empty():
		return false
	main.dialogue_ui.option_buttons[0].pressed.emit()
	await _roll(4)
	return true


func _run_film() -> void:
	_pick_option("Патан")
	_pick_option("Бабу")
	await _frames(6)
	await _roll(24)
	_press_text("Начать")
	await _wait_options()

	# Холодное открытие целиком.
	for _i in range(9):
		if main.title_card.visible or not await _film_beat(26):
			break
	if main.title_card.visible:
		await _roll(40)
		main.title_dismissed.emit()
		await _frames(8)

	# Пролог промотан без записи: эта запись про вагон.
	for _i in range(140):
		if main.trial_ui.visible:
			break
		var txt := _dialogue_text()
		if txt.contains("силуэт") or txt.contains("Темнота") or txt.contains("Хромой"):
			break
		if main.check_ui.visible:
			await _dismiss_check()
			continue
		if main.transition_ui.visible:
			await _advance_transition()
			continue
		if not await _wait_options():
			await _frames(4)
			continue
		await _click(0)
	await _frames(8)
	await _roll(30)

	# Суд: длинные планы, тут и смотреть.
	await _click_until(_trial_ready, 14)
	var guard := 0
	while main.trial_ui.visible and guard < 14:
		guard += 1
		await _roll(46)
		if main.trial_ui._buttons.is_empty():
			await _click(0)
			continue
		var pick := _trial_index_for([
			"бахи", "долг", "Ничего не сказать", "Билет продали мне", "Вы говорите о себе"])
		if pick < 0:
			pick = 0
		(main.trial_ui._buttons[pick] as Button).pressed.emit()
		await _roll(10)
		if main.check_ui.visible:
			await _roll(16)
			await _dismiss_check()
		await _roll(22)
	await _roll(36)

	# Узел путей и служба.
	await _click_until(func(): return _has_option("Отработать смену"), 10)
	await _roll(44)
	_click_option_text("Отработать смену")
	for _i in range(16):
		if main.transition_ui.visible or not await _film_beat(24):
			break
	await _click_until(func(): return main.transition_ui.visible, 10)
	if main.transition_ui.visible:
		await _roll(70)
		await _advance_transition()
		await _roll(30)
	log_lines.append("film_*.jpg\n    Непрерывная запись прохода: %d кадров." % film_no)


func _click_option_text(fragment: String) -> void:
	for b in main.dialogue_ui.option_buttons:
		if (b as Button).text.containsn(fragment):
			b.pressed.emit()
			return
	if not main.dialogue_ui.option_buttons.is_empty():
		main.dialogue_ui.option_buttons[0].pressed.emit()


## Сколько в кадре движения: 90 подряд идущих кадров вагона и столько же
## испытания. Если между ними нет разницы — двигаться в игре нечему, и это
## измерение, а не впечатление.
func _run_motion() -> void:
	await _debug_press("Сразу в вагон")
	await _wait_options()
	main.dialogue_ui.visible = false
	main.hud.visible = false
	main.debug_panel.visible = false
	await _frames(20)
	for i in range(90):
		await RenderingServer.frame_post_draw
		var img: Image = get_viewport().get_texture().get_image()
		img.save_png(SHOTS + "motion_car_%03d.png" % i)
	await _debug_press("Спор о часах")
	await _frames(20)
	main.trial_ui.visible = false
	main.debug_panel.visible = false
	for i in range(90):
		await RenderingServer.frame_post_draw
		var img2: Image = get_viewport().get_texture().get_image()
		img2.save_png(SHOTS + "motion_trial_%03d.png" % i)
	log_lines.append("motion_*.png\n    По 90 кадров подряд: вагон и испытание.")


## Запись прохода вагона целиком — чтобы миссию можно было посмотреть, а не
## только пройти. Кадр снимается после каждого шага, включая реплики: из этих
## кадров tools/make_letsplay.py собирает видео. Персонаж — марвари-бабу: у
## него в первом раунде суда есть довод «по бахи-хате», и суд читается без
## случайных провалов на первом же шаге.
func _run_letsplay() -> void:
	# Патан-бабу выбран не случайно: у патана во втором раунде суда есть довод
	# «опоздание — долг» (победа без броска), а бабу даёт преимущество в первом.
	# Так суд читается как суд, а не как серия неудачных бросков.
	_pick_option("Патан")
	_pick_option("Бабу")
	await _frames(6)
	await _shot("00_начало", "Персонаж: патан-кабуливала, бабу.")
	_press_text("Начать")

	# --- Акт 1: холодное открытие -------------------------------------------
	await _wait_options()
	await _beats("холодное", 8, "Темнота тормозного вагона. Единственное действие — встать.")
	if main.title_card.visible:
		await _shot("титр", "«Десятью часами раньше». Дальше пролог.")
		main.title_dismissed.emit()
		await _frames(8)

	# --- Пролог проматывается: эта запись про вагон, не про Калькутту -------
	await _shot("пролог_начало", "Пролог начался — в этой записи он промотан.")
	for _i in range(140):
		if main.trial_ui.visible:
			break
		var txt := _dialogue_text()
		if txt.contains("силуэт") or txt.contains("Темнота") or txt.contains("Хромой"):
			break
		if main.check_ui.visible:
			await _dismiss_check()
			continue
		if main.transition_ui.visible:
			await _advance_transition()
			continue
		if not await _wait_options():
			await _frames(4)
			continue
		await _click(0)
	await _frames(8)
	await _shot("возврат", "Возврат в вагон: тот же кадр, силуэт в глубине поворачивается.")

	# --- Акт 2: суд Шани ----------------------------------------------------
	await _click_until(_trial_ready, 14)
	var guard := 0
	while main.trial_ui.visible and guard < 20:
		guard += 1
		await _frames(4)
		if main.trial_ui._buttons.is_empty():
			await _click(0)
			continue
		await _shot("суд_%d" % guard, _trial_line())
		var pick := _trial_index_for([
			"бахи", "долг", "Ничего не сказать", "Билет продали мне", "Вы говорите о себе"])
		if pick < 0:
			pick = 0
		await _click_trial(pick)
		await _shot("суд_%d_исход" % guard, "Исход раунда.")
	await _frames(10)
	await _shot("суд_окончен", "Суд окончен.")

	# --- Акт 3: узел путей и выход службой ----------------------------------
	await _click_until(func(): return _has_option("Отработать смену"), 10)
	await _shot("четыре_пути", "Четыре пути: сила, обман, служба, остаться.")
	await _click_text("Отработать смену")
	await _beats("служба", 16, "Служба: три задачи тормозного вагона.")
	await _click_until(func(): return main.transition_ui.visible, 10)
	if main.transition_ui.visible:
		await _shot("переход", "Ритуал перелезания: постановка, без бросков.")
		await _wait_transition()
		await _shot("переход_конец", "Ритуал окончен.")
		await _advance_transition()
		await _frames(8)
		await _shot("вагон_пройден", "Вагон пройден. Окно сдвинулось на два.")

	# --- Кода: тот же вагон, путь «остаться» и концовка 5 -------------------
	main.debug_panel.visible = true
	await _frames(4)
	_press_text("Сразу в вагон")
	await _wait_options()
	main.debug_panel.visible = false
	await _frames(6)
	await _shot("кода_путь", "Тот же вагон заново: путь «остаться».")
	await _click_until(func(): return _has_option("фонарь"), 8)
	await _click_text("фонарь")
	await _beats("остаться", 10, "Снять фонарь с крюка — сменить Шани в удержании момента.")
	await _click_until(func(): return main.credits_ui.visible, 12)
	if main.credits_ui.visible:
		await _shot("концовка_5", "Концовка 5 «ФОНАРЬ»: настоящие титры, игра окончена.")


## Нажать вариант и снять кадр, n раз. Так проход и записывается целиком.
func _beats(tag: String, n: int, note: String) -> void:
	for i in range(n):
		if main.title_card.visible or main.transition_ui.visible or main.trial_ui.visible:
			return
		await _shot("%s_%d" % [tag, i], note if i == 0 else _dialogue_text().substr(0, 110))
		if not await _wait_options():
			return
		await _click(0)


## Отдельной функцией, потому что многострочная лямбда в аргументе вызова
## GDScript не разбирает.
func _trial_ready() -> bool:
	return main.trial_ui.visible and not main.trial_ui._buttons.is_empty()


func _trial_line() -> String:
	return main.trial_ui.argument_label.text.substr(0, 110)


## Номер варианта суда по фрагменту текста: индексы зависят от условий,
## поэтому по номеру нажимать нельзя.
func _trial_index_for(fragments: Array) -> int:
	var buttons: Array = main.trial_ui._buttons
	for f in fragments:
		for i in range(buttons.size()):
			if (buttons[i] as Button).text.containsn(str(f)):
				return i
	return -1


func _pick_option(fragment: String) -> void:
	for node in _all_nodes(get_tree().root):
		if node is OptionButton:
			var ob := node as OptionButton
			for i in range(ob.item_count):
				if ob.get_item_text(i).containsn(fragment):
					ob.select(i)
					ob.item_selected.emit(i)
					return


func _all_nodes(root: Node) -> Array:
	var out: Array = [root]
	for c in root.get_children():
		out += _all_nodes(c)
	return out


## Проверка послойности: присутствие не должно дизериться вместе с миром.
## Кадр со сбоем и кадр без сбоя обязаны совпасть пиксель в пиксель внутри
## силуэта присутствия. Разбор — в tools/check_presence_layer.py.
func _run_glitch_check() -> void:
	await _debug_press("Сразу в вагон")
	await _wait_options()
	await _debug_press("Спор о часах")
	await _frames(12)
	main.dialogue_ui.visible = false
	main.trial_ui.visible = false
	main.hud.visible = false
	main.debug_panel.visible = false
	main.check_ui.visible = false
	main.palette.set_colour_return(0.0)
	await _frames(8)
	await RenderingServer.frame_post_draw
	var chk_pres: Image = main.presence_viewport.get_texture().get_image()
	chk_pres.save_png(SHOTS + "chk_presence_alpha.png")
	main.grade.set_glitch(0.0)
	main._apply_palette()
	await _frames(8)
	await RenderingServer.frame_post_draw
	var chk_a: Image = get_viewport().get_texture().get_image()
	chk_a.save_png(SHOTS + "chk_no_glitch.png")
	main.grade.set_glitch(1.0)
	main._apply_palette()
	await _frames(8)
	await RenderingServer.frame_post_draw
	var chk_b: Image = get_viewport().get_texture().get_image()
	chk_b.save_png(SHOTS + "chk_glitch.png")
	log_lines.append("chk_presence_alpha.png / chk_no_glitch.png / chk_glitch.png\n    Проверка послойности присутствия.")


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
## Дождаться, пока реплика допечатается: варианты приходят только после этого.
func _wait_typing() -> void:
	for _i in range(240):
		if not main.dialogue_ui.typing:
			return
		await get_tree().process_frame
	main.dialogue_ui.skip_typing()


func _wait_options() -> bool:
	await _wait_typing()
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
