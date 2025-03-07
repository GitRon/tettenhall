from collections import defaultdict


def querydict_to_nested_dict(*, querydict: dict, prefix: str) -> dict:
    result = defaultdict(dict)

    for key, value in querydict.items():
        if key.startswith(prefix):
            # Extract index and name
            parts = key[len(prefix) :].strip("[]").split("][")
            index, field_name = int(parts[0]), parts[1]
            result[index][field_name] = value

    return dict(result)
