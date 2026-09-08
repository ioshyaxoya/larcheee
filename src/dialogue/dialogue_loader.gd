class_name DialogueLoader
extends RefCounted
## Загрузка графа диалога из data/dialogues/<id>.json.

const DIR := "res://data/dialogues/"


static func load_dialogue(id: String) -> Dictionary:
	var path := DIR + id + ".json"
	if not FileAccess.file_exists(path):
		push_error("DialogueLoader: нет файла %s" % path)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("DialogueLoader: %s — невалидный JSON" % path)
		return {}
	return parsed
