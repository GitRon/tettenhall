import re


def convert_string_based_two_level_dict_to_dict(data: dict) -> dict:
    # todo build properly and generic
    new_dict = {}
    for key, value in data.items():
        match = re.search(r"^([\w\-]+)\[(\w)+\]\[(\w+)\]$", key)
        if match:
            field_name = match.group(1)
            faction_id = int(match.group(2))
            warrior_id = int(match.group(3))
            skirmish_action = int(value)
            if field_name not in new_dict:
                new_dict[match.group(1)] = {}
            if faction_id not in new_dict[field_name]:
                new_dict[field_name][faction_id] = {}
            if warrior_id not in new_dict[field_name][faction_id]:
                new_dict[field_name][faction_id][warrior_id] = {}
            new_dict[field_name][faction_id][warrior_id] = skirmish_action

    return new_dict
