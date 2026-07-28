from apps.town.models import Town
from apps.town.tests.factories.town import TownFactory


def test_str_returns_the_name_of_the_owning_faction():
    town = TownFactory.build(faction__name="Tettenhall")

    assert str(town) == "Tettenhall"


def test_get_building_level_display_names_a_level_that_is_not_the_current_one():
    town = TownFactory.build(hall=Town.HallChoices.HALL_NONE)

    result = town.get_building_level_display(building_type="hall", level=Town.HallChoices.HALL_MEDIUM)

    assert result == "Great Hall"
