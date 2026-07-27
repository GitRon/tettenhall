from apps.common.templatetags.utils import lookup


def test_lookup_returns_the_value_behind_the_key():
    result = lookup({"silver": 100}, "silver")

    assert result == 100
