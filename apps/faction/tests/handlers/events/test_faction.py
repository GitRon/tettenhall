from apps.faction.handlers.events.faction import (
    handle_consider_fyrd_draft_for_new_month,
    handle_create_player_faction_for_new_savegame,
    handle_determine_injured_warriors_for_new_month,
    handle_determine_warriors_with_reduced_morale_for_new_month,
    handle_earn_money_from_buildings_for_new_month,
    handle_earn_monthly_faction_income_for_new_month,
    handle_pay_monthly_warrior_salaries_for_new_month,
    handle_replenish_fyrd_reserve_for_new_month,
    handle_warriors_with_reduced_morale_determined,
)
from apps.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    DetermineInjuredWarriors,
    DetermineWarriorsWithReducedMorale,
    EarnMoneyFromBuildings,
    EarnMonthlyFactionIncome,
    PayMonthlyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.messages.commands.warrior import ConsiderFyrdDraft
from apps.faction.messages.events.faction import FactionWarriorsWithReducedMoraleDetermined
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.messages.events.month import FactionMonthPrepared
from apps.savegame.messages.events.savegame import NewSavegameCreated
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale


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


def test_handle_warriors_with_reduced_morale_determined_with_warriors():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_warriors_with_reduced_morale_determined(
        context=FactionWarriorsWithReducedMoraleDetermined(faction=faction, warrior_list=[warrior], month=3)
    )

    assert result == [ReplenishWarriorMorale(warrior=warrior, month=3)]


def test_handle_warriors_with_reduced_morale_determined_without_warriors():
    faction = FactionFactory.build()

    result = handle_warriors_with_reduced_morale_determined(
        context=FactionWarriorsWithReducedMoraleDetermined(faction=faction, warrior_list=[], month=3)
    )

    assert result == []


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
    faction = FactionFactory.build()

    result = handle_earn_money_from_buildings_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == EarnMoneyFromBuildings(faction=faction, month=7)


def test_handle_earn_monthly_faction_income_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_earn_monthly_faction_income_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == EarnMonthlyFactionIncome(faction=faction, month=7)


def test_handle_consider_fyrd_draft_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_consider_fyrd_draft_for_new_month(context=FactionMonthPrepared(faction=faction, current_month=7))

    assert result == ConsiderFyrdDraft(faction=faction, month=7)


def test_handle_determine_warriors_with_reduced_morale_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_determine_warriors_with_reduced_morale_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == [DetermineWarriorsWithReducedMorale(faction=faction, month=7)]


def test_handle_determine_injured_warriors_for_new_month_maps_to_command():
    faction = FactionFactory.build()

    result = handle_determine_injured_warriors_for_new_month(
        context=FactionMonthPrepared(faction=faction, current_month=7)
    )

    assert result == [DetermineInjuredWarriors(faction=faction, month=7)]
