from apps.common.utils import querydict_to_nested_dict


def test_querydict_to_nested_dict_groups_the_fields_by_index():
    querydict = {
        "participant[0][warrior_id]": "1",
        "participant[0][skirmish_action]": "2",
        "participant[1][warrior_id]": "3",
    }

    result = querydict_to_nested_dict(querydict=querydict, prefix="participant")

    assert result == {0: {"warrior_id": "1", "skirmish_action": "2"}, 1: {"warrior_id": "3"}}


def test_querydict_to_nested_dict_ignores_keys_without_the_prefix():
    querydict = {"csrfmiddlewaretoken": "irrelevant", "participant[0][warrior_id]": "1"}

    result = querydict_to_nested_dict(querydict=querydict, prefix="participant")

    assert result == {0: {"warrior_id": "1"}}
