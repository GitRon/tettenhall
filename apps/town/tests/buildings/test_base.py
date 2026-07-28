import pytest

from apps.town.buildings.hall import Hall, LargeHall


def test_get_max_level_is_the_last_variant():
    assert Hall.get_max_level() == 3


def test_get_building_by_type_returns_the_variant_for_the_level():
    result = Hall.get_building_by_type(building_type=Hall.get_max_level())

    assert isinstance(result, LargeHall)


def test_get_building_by_type_below_the_first_level():
    """
    Indexing the variants with a negative number would count from the end and quietly hand back the
    largest building instead of failing.
    """
    with pytest.raises(RuntimeError, match="Unknown hall type: -1"):
        Hall.get_building_by_type(building_type=-1)
