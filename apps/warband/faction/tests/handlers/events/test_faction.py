from apps.warband.faction.handlers.events.faction import (
    handle_create_player_faction_for_new_savegame,
    handle_earn_money_from_buildings_for_new_month,
    handle_let_captives_flee_overfull_cells_for_new_month,
    handle_pay_monthly_warrior_salaries_for_new_month,
    handle_plan_faction_month_for_new_month,
    handle_prepare_faction_warriors_for_new_month,
    handle_replenish_fyrd_reserve_for_new_month,
    handle_upgrade_town_building_for_approved_upgrade,
)
from apps.warband.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    EarnMoneyFromBuildings,
    LetCaptivesFleeOverfullCells,
    PlanFactionMonth,
    PrepareFactionWarriorsForMonth,
    ReplenishFyrdReserve,
)
from apps.warband.faction.messages.commands.warrior import PayMonthlyWarriorSalaries
from apps.warband.faction.messages.events.faction import TownBuildingUpgradeApproved
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.messages.events.month import FactionMonthPrepared
from apps.warband.savegame.messages.events.savegame import NewSavegameCreated
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.town.messages.commands.town import UpgradeTownBuilding
from apps.warband.town.tests.factories.town import TownFactory


def test_handle_create_player_faction_for_new_savegame_maps_to_command():
    """
    Pure mapping: naming the rival factions needs the cultures, so the command handler reads them -
    an event handler cannot, strict mode blocks its database access.
    """
    savegame = SavegameFactory.build()

    result = handle_create_player_faction_for_new_savegame(
        context=NewSavegameCreated(
            savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=7
        )
    )

    assert result == CreateFactionsForNewSavegame(
        savegame=savegame, faction_name="Wessex", town_name="Winchester", faction_culture_id=7
    )


def test_handle_replenish_fyrd_reserve_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_replenish_fyrd_reserve_for_new_month(context=FactionMonthPrepared(faction=faction, current_month=7))

    assert result == [ReplenishFyrdReserve(faction=faction, month=7)]


def test_handle_pay_monthly_warrior_salaries_for_new_month_maps_to_command():
    """
    Every faction still in play pays its warriors, not only the player's - which is what makes a
    rival's purse mean anything.
    """
    faction = FactionFactory.build()

    result = handle_pay_monthly_warrior_salaries_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == PayMonthlyWarriorSalaries(faction=faction, month=7)


def test_handle_earn_money_from_buildings_for_new_month_maps_to_command():
    """
    On the event raised for every faction: a rival lives on its town the way the player does.
    """
    faction = FactionFactory.build()

    result = handle_earn_money_from_buildings_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == EarnMoneyFromBuildings(faction=faction, month=7)


def test_handle_upgrade_town_building_for_approved_upgrade_maps_to_command():
    faction = FactionFactory.build()
    town = TownFactory.build(faction=faction)

    result = handle_upgrade_town_building_for_approved_upgrade(
        context=TownBuildingUpgradeApproved(
            faction=faction, town=town, building_type="hall", new_level=1, costs=600, month=7
        )
    )

    assert result == UpgradeTownBuilding(
        town=town, faction=faction, building_type="hall", new_level=1, costs=600, month=7
    )


def test_handle_plan_faction_month_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_plan_faction_month_for_new_month(context=FactionMonthPrepared(faction=faction, current_month=7))

    assert result == PlanFactionMonth(faction=faction, month=7)


def test_handle_prepare_faction_warriors_for_new_month_maps_to_command():
    """
    Every faction's men get their month, not just the player's: this is registered on the event raised
    for all of them, and that registration is the whole of what makes a rival's war band recover.
    """
    faction = FactionFactory.build()

    result = handle_prepare_faction_warriors_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == PrepareFactionWarriorsForMonth(faction=faction, month=7)


def test_handle_let_captives_flee_overfull_cells_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_let_captives_flee_overfull_cells_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == LetCaptivesFleeOverfullCells(faction=faction, month=7)
