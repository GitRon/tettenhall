import pytest

from apps.town.handlers.commands.town import handle_upgrade_town_building
from apps.town.messages.commands.town import UpgradeTownBuilding
from apps.town.messages.events.town import TownBuildingUpgraded
from apps.town.models import Town
from apps.town.tests.factories.town import TownFactory


@pytest.mark.django_db
def test_handle_upgrade_town_building_raises_the_building_level():
    town = TownFactory(hall=Town.HallChoices.HALL_SMALL)

    result = handle_upgrade_town_building(
        context=UpgradeTownBuilding(
            town=town,
            faction=town.faction,
            building_type="hall",
            new_level=Town.HallChoices.HALL_MEDIUM,
            costs=2000,
            month=4,
        )
    )

    assert result == TownBuildingUpgraded(
        town=town,
        faction=town.faction,
        building_type="hall",
        new_level=Town.HallChoices.HALL_MEDIUM,
        costs=2000,
        month=4,
    )
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_MEDIUM


@pytest.mark.django_db
def test_handle_upgrade_town_building_records_the_construction_month():
    """
    The month is what the "one building per month" guard in the view compares against.
    """
    town = TownFactory(last_constructed_building_at=1)

    handle_upgrade_town_building(
        context=UpgradeTownBuilding(
            town=town,
            faction=town.faction,
            building_type="hall",
            new_level=Town.HallChoices.HALL_SMALL,
            costs=1000,
            month=4,
        )
    )

    town.refresh_from_db()
    assert town.last_constructed_building_at == 4


@pytest.mark.django_db
def test_handle_upgrade_town_building_ignores_a_second_upgrade_in_the_same_month():
    """
    The view checks the once-per-month rule too, but two overlapping requests both pass that check.
    The conditional UPDATE here is what stops the second one, so nobody is charged twice.
    """
    town = TownFactory(hall=Town.HallChoices.HALL_NONE, last_constructed_building_at=4)
    context = UpgradeTownBuilding(
        town=town,
        faction=town.faction,
        building_type="hall",
        new_level=Town.HallChoices.HALL_SMALL,
        costs=900,
        month=4,
    )

    result = handle_upgrade_town_building(context=context)

    # No event means no TownBuildingUpgraded and therefore no transaction
    assert result is None
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_NONE


@pytest.mark.django_db
def test_handle_upgrade_town_building_upgrades_the_building_named_by_the_message():
    """
    The building to raise arrives as a field name, so a message naming another one has to move that
    one instead of the hall.
    """
    town = TownFactory(weaponsmith=Town.WeaponsmithChoices.WEAPONSMITH_NONE)

    handle_upgrade_town_building(
        context=UpgradeTownBuilding(
            town=town,
            faction=town.faction,
            building_type="weaponsmith",
            new_level=Town.WeaponsmithChoices.WEAPONSMITH_SMALL,
            costs=1000,
            month=4,
        )
    )

    town.refresh_from_db()
    assert town.weaponsmith == Town.WeaponsmithChoices.WEAPONSMITH_SMALL
