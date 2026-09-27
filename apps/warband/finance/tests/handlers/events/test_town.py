from apps.warband.finance.handlers.events.town import handle_pay_building_costs_for_town_buildings, handle_pay_for_feast
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.messages.events.town import FeastThrown, TownBuildingUpgraded
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


def test_handle_pay_for_feast_charges_the_whole_table_once():
    town = TownFactory.build()
    context = FeastThrown(
        town=town,
        faction=town.faction,
        warrior_list=WarriorFactory.build_batch(3),
        restored_share=0.1,
        costs=45,
        month=4,
    )

    result = handle_pay_for_feast(context=context)

    assert result == CreateTransaction(faction=town.faction, amount=-45, reason="Feast for 3 men", month=4)


def test_handle_pay_for_feast_words_a_table_of_one():
    town = TownFactory.build()
    context = FeastThrown(
        town=town,
        faction=town.faction,
        warrior_list=[WarriorFactory.build()],
        restored_share=0.1,
        costs=15,
        month=4,
    )

    result = handle_pay_for_feast(context=context)

    assert result.reason == "Feast for 1 man"
