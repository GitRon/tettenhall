from collections import defaultdict


def querydict_to_nested_dict(*, querydict: dict, prefix: str) -> dict:
    result = defaultdict(dict)

    for key, value in querydict.items():
        if not key.startswith(prefix):
            continue

        # Extract index and name. The key is part of the request body just like the value is, so a
        # hand-crafted one is bad input and gets dropped - parsing it eagerly raised ValueError or
        # IndexError out of the view, which answered 500 before it could validate anything.
        parts = key[len(prefix) :].strip("[]").split("][")
        if len(parts) != 2 or not parts[0].isdigit():
            continue

        result[int(parts[0])][parts[1]] = value

    return dict(result)
