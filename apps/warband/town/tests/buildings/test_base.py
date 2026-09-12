import pytest

from apps.warband.town.buildings import BUILDINGS
from apps.warband.town.buildings.hall import Hall, LargeHall


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


def test_the_first_paid_level_of_every_family_is_within_the_opening_purse():
    """
    A faction opens with 1000 silver, and the first building it puts up is meant to leave enough
    behind to pay a month's wages or hire a man - see Building.BUILDING_COSTS.
    """
    first_paid_costs = [family.get_levels()[1].BUILDING_COSTS for family in BUILDINGS.values()]

    assert max(first_paid_costs) == 600


def test_the_step_to_the_second_paid_level_is_the_steepest_one():
    """
    The opening purse buys one building and a decision about what to do next; everything above the
    first level is saved for across several months.
    """
    for family in BUILDINGS.values():
        _, first, second, third = family.get_levels()

        assert second.BUILDING_COSTS / first.BUILDING_COSTS == 3.5
        assert third.BUILDING_COSTS / second.BUILDING_COSTS == 2
