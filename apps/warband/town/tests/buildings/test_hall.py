import pytest

from apps.warband.town.buildings.base import BuildingEffect
from apps.warband.town.buildings.hall import Hall, LargeHall, MediumHall, NoHall, SmallHall
from apps.warband.town.models import Town


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


def test_get_effects_names_the_income_the_men_it_wants_the_mercenary_slots_and_the_feast():
    result = SmallHall.get_effects()

    assert result == (
        BuildingEffect(label="Monthly income", value="300 silver"),
        BuildingEffect(label="Men needed for full income", value="1"),
        BuildingEffect(label="Mercenaries in the pub", value="1"),
        BuildingEffect(label="A feast mends a cut ceiling by", value="10%"),
        BuildingEffect(label="Feast per man", value="15 silver"),
    )


def test_get_effects_says_a_town_without_a_hall_cannot_feast():
    assert NoHall.get_effects()[3] == BuildingEffect(label="A feast mends a cut ceiling by", value="No feasts")


def test_can_feast_is_refused_a_town_without_a_hall():
    assert NoHall.can_feast() is False


def test_can_feast_in_any_hall_standing():
    assert all(level.can_feast() for level in Hall.get_levels()[1:])


def test_feast_restored_share_grows_with_the_hall():
    """
    A bigger hall is a better repair - the reason to build the level income alone never pays for.
    """
    shares = [level.FEAST_RESTORED_SHARE for level in Hall.get_levels()]

    assert shares == sorted(shares)
    assert len(set(shares)) == len(shares)


def test_get_feast_price_charges_every_head_at_the_table():
    assert MediumHall.get_feast_price(head_count=6) == 6 * Hall.FEAST_PRICE_PER_HEAD


def test_get_revenue_for_war_band_pays_a_hall_less_town_whatever_it_fields():
    """
    Level 0 asks for nobody: its baseline is what a town earns before anything is built, and a rule
    about manning a hall cannot apply to a town without one.
    """
    assert NoHall.get_revenue_for_war_band(warriors_on_payroll=0) == 50


def test_get_revenue_for_war_band_pays_in_full_at_the_men_the_level_asks_for():
    assert LargeHall.get_revenue_for_war_band(warriors_on_payroll=3) == 750


def test_get_revenue_for_war_band_pays_no_more_for_a_war_band_beyond_it():
    assert LargeHall.get_revenue_for_war_band(warriors_on_payroll=5) == 750


def test_get_revenue_for_war_band_pays_a_share_of_a_short_war_band():
    assert LargeHall.get_revenue_for_war_band(warriors_on_payroll=2) == 500


def test_get_revenue_for_war_band_falls_back_to_the_baseline_for_a_band_of_nobody():
    """
    The floor, and the case #192 is about: a leader alone draws no wage, so the hall he bought in
    month one pays him what a town with no hall earns.
    """
    assert LargeHall.get_revenue_for_war_band(warriors_on_payroll=0) == NoHall.REVENUE_PER_ROUND
