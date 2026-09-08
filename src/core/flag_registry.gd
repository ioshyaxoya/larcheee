class_name FlagRegistry
extends RefCounted
## Реестр флагов из data/flags.json (B5): имя → описание (строка) или
## имя → {description, type, values}. Незарегистрированный флаг не записывается.
## Теги пролога (B6) хранятся флагами prologue.<tag>.

const PATH := "res://data/flags.json"
const TAG_PREFIX := "prologue."

var flags: Dictionary = {}


func _init() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("FlagRegistry: %s — невалидный JSON" % PATH)
		return
	for name in parsed.keys():
		if String(name).begins_with("_"):
			continue
		var spec = parsed[name]
		if typeof(spec) == TYPE_DICTIONARY:
			flags[name] = {"type": spec.get("type", "any"), "values": spec.get("values", []), "description": spec.get("description", "")}
		else:
			flags[name] = {"type": "any", "values": [], "description": str(spec)}


func has_flag(name: String) -> bool:
	return flags.has(name)


func has_tag(tag: String) -> bool:
	return flags.has(TAG_PREFIX + tag)


func flag_type(name: String) -> String:
	return flags.get(name, {}).get("type", "any")


func validate(name: String, value: Variant) -> bool:
	if not has_flag(name):
		return false
	match flag_type(name):
		"bool":
			return typeof(value) == TYPE_BOOL
		"int":
			return typeof(value) == TYPE_INT or (typeof(value) == TYPE_FLOAT and is_equal_approx(value, floor(value)))
		"string":
			return typeof(value) == TYPE_STRING
		"enum":
			return typeof(value) == TYPE_STRING and (flags[name]["values"] as Array).has(value)
		_:
			return true
