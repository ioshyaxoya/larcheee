extends SceneTree
func _init() -> void:
	for build in [["marwari","trader","m"], ["pathan","guard","m"], ["chinese","carpenter","f"], ["officer","sepoy","m"]]:
		var ctx := GameContext.create(11, "ru")
		ctx.set_character(ctx.char_data.build(str(build[0]), str(build[1]), str(build[2])))
		for spec in [{"skill": "athletics", "dc": 16}, {"skill": "deception", "dc": 15}]:
			var rolls := PackedStringArray()
			var wins := 0
			for i in range(12):
				var r: CheckResult = ctx.checks.roll(ctx.character, spec)
				rolls.append(str(r.roll) + ("+" if r.success else "-"))
				if r.success: wins += 1
			print("%-24s %-10s СЛ%d: %s  успехов %d/12" % [
				"%s/%s/%s" % [build[0], build[1], build[2]], spec["skill"], spec["dc"],
				", ".join(rolls), wins])
	quit()
