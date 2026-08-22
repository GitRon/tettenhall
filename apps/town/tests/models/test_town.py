from apps.town.models import Town
from apps.town.tests.factories.town import TownFactory


def test_str_returns_the_name_of_the_owning_faction():
    town = TownFactory.build(faction__name="Tettenhall")

    assert str(town) == "Tettenhall"


def test_get_building_level_display_names_a_level_that_is_not_the_current_one():
    town = TownFactory.build(hall=Town.HallChoices.HALL_NONE)

    result = town.get_building_level_display(building_type="hall", level=Town.HallChoices.HALL_MEDIUM)

    assert result == "Great Hall"


def test_get_monthly_income_pays_the_baseline_of_a_town_without_a_hall():
    """
    Level 0 is a baseline rather than nothing, so a hall-less town is the case that has to earn.
    """
    town = TownFactory.build(hall=Town.HallChoices.HALL_NONE)

    assert town.get_monthly_income() == 50


def test_get_monthly_income_pays_the_revenue_of_the_hall_standing():
    town = TownFactory.build(hall=Town.HallChoices.HALL_MEDIUM)

    assert town.get_monthly_income() == 550
