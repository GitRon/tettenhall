from apps.warband.finance.handlers.events.town import handle_pay_building_costs_for_town_buildings
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.town.messages.events.town import TownBuildingUpgraded
from apps.warband.town.models import Town
from apps.warband.town.tests.factories.town import TownFactory


def test_handle_pay_building_costs_for_town_buildings_charges_the_faction():
    town = TownFactory.build()
    context = TownBuildingUpgraded(
        town=town,
        faction=town.faction,
        building_type="hall",
        new_level=Town.HallChoices.HALL_MEDIUM,
        costs=2000,
        month=4,
    )

    result = handle_pay_building_costs_for_town_buildings(context=context)

    assert result == CreateTransaction(
        faction=town.faction,
        amount=-2000,
        reason="Building 'hall' level 2 constructed",
        month=4,
    )
