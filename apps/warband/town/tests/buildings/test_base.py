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


def test_the_second_paid_level_is_only_a_little_dearer_than_the_first():
    """
    A faction spends down to its wage bill every month, so a level is only reached by a few months of
    holding back - the second is priced for that, and the third doubles it.
    """
    for family in BUILDINGS.values():
        _, first, second, third = family.get_levels()

        assert first.BUILDING_COSTS < second.BUILDING_COSTS < 1.5 * first.BUILDING_COSTS
        assert third.BUILDING_COSTS == 2 * second.BUILDING_COSTS
