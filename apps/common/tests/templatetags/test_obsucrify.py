from apps.common.templatetags.obsucrify import obscurify


def test_obscurify_well_above_the_average():
    result = obscurify(13, 10)

    assert result == "High"


def test_obscurify_well_below_the_average():
    result = obscurify(7, 10)

    assert result == "Low"


def test_obscurify_close_to_the_average():
    result = obscurify(10, 10)

    assert result == "Mediocre"
