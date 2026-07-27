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


def test_querydict_to_nested_dict_ignores_a_non_numeric_index():
    """
    The keys arrive in the request body, so a hand-crafted one is bad input. Parsing it with a bare
    int() raised ValueError before the caller got a chance to answer 400.
    """
    querydict = {"participant[abc][warrior_id]": "1", "participant[0][warrior_id]": "2"}

    result = querydict_to_nested_dict(querydict=querydict, prefix="participant")

    assert result == {0: {"warrior_id": "2"}}


def test_querydict_to_nested_dict_ignores_a_key_without_a_field_name():
    """
    Same for a key that stops after the index: indexing the missing second part raised IndexError.
    """
    querydict = {"participant[0]": "1", "participant[1][warrior_id]": "2"}

    result = querydict_to_nested_dict(querydict=querydict, prefix="participant")

    assert result == {1: {"warrior_id": "2"}}
