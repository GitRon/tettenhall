import pytest

from apps.town.buildings.hall import Hall, LargeHall, MediumHall, NoHall, SmallHall
from apps.town.models import Town


def test_get_building_by_type_without_a_hall():
    result = Hall.get_building_by_type(building_type=Town.HallChoices.HALL_NONE)

    assert isinstance(result, NoHall)


def test_get_building_by_type_small():
    result = Hall.get_building_by_type(building_type=Town.HallChoices.HALL_SMALL)

    assert isinstance(result, SmallHall)


def test_get_building_by_type_medium():
    result = Hall.get_building_by_type(building_type=Town.HallChoices.HALL_MEDIUM)

    assert isinstance(result, MediumHall)


def test_get_building_by_type_large():
    result = Hall.get_building_by_type(building_type=Town.HallChoices.HALL_LARGE)

    assert isinstance(result, LargeHall)


def test_get_building_by_type_unknown_level():
    with pytest.raises(RuntimeError, match="Unknown hall type: 4"):
        Hall.get_building_by_type(building_type=4)


def test_get_levels_matches_the_model_choices():
    """
    The level is written straight into a choices-constrained column and Django validates choices only
    in forms, so a variant added here without its counterpart on the model would store a level the
    display and the admin cannot handle.
    """
    assert len(Hall.get_levels()) == len(Town.HallChoices)
