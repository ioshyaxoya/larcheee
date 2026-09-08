class_name Texts
extends RefCounted
## Тексты по ключам. Русский основной, английский второй.
## Строк в коде нет: любой видимый текст берётся отсюда по ключу.

const TEXTS_DIR := "res://data/texts/"

var lang: String = "ru"
var _primary: Dictionary = {}
var _fallback: Dictionary = {}


func _init(language: String = "ru") -> void:
	set_language(language)


func set_language(language: String) -> void:
	lang = language
	_primary = _load(language)
	_fallback = _load("ru") if language != "ru" else _primary


static func _load(language: String) -> Dictionary:
	var path := TEXTS_DIR + language + ".json"
	if not FileAccess.file_exists(path):
		push_error("Texts: нет файла %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Texts: %s — невалидный JSON" % path)
		return {}
	return parsed


func has(key: String) -> bool:
	return _primary.has(key) or _fallback.has(key)


## Возвращает текст по ключу с подстановкой {параметров}.
## Отсутствующий ключ возвращается как «[key]» — это видно и не прячется.
func t(key: String, params: Dictionary = {}) -> String:
	var raw: String
	if _primary.has(key):
		raw = _primary[key]
	elif _fallback.has(key):
		raw = _fallback[key]
	else:
		return "[%s]" % key
	return raw.format(params) if not params.is_empty() else raw
