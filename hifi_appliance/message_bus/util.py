def keys_to_ascii(dict):
	return {key.encode('ascii'):value for (key, value) in dict.items()}


def decode_list_to_str(items):
	return [item.decode('ascii') for item in items]
