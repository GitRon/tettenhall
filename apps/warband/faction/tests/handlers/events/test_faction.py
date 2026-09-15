from apps.warband.faction.handlers.events.faction import (
    handle_consider_fyrd_draft_for_new_month,
    handle_create_player_faction_for_new_savegame,
    handle_earn_money_from_buildings_for_new_month,
    handle_earn_monthly_faction_income_for_new_month,
    handle_pay_monthly_warrior_salaries_for_new_month,
    handle_prepare_faction_warriors_for_new_month,
    handle_replenish_fyrd_reserve_for_new_month,
)
from apps.warband.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    EarnMoneyFromBuildings,
    EarnMonthlyFactionIncome,
    PrepareFactionWarriorsForMonth,
    ReplenishFyrdReserve,
)
from apps.warband.faction.messages.commands.warrior import ConsiderFyrdDraft, PayMonthlyWarriorSalaries
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.messages.events.month import FactionMonthPrepared, PlayerMonthPrepared
from apps.warband.savegame.messages.events.savegame import NewSavegameCreated
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


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
    On the player-only event: the town economy is the thing a rival has no equivalent of, and being
    registered there is the whole of what keeps a rival off the hall's revenue.
    """
    faction = FactionFactory.build()
    context = PlayerMonthPrepared(faction=faction, savegame=SavegameFactory.build(), current_month=7)

    result = handle_earn_money_from_buildings_for_new_month(context=context)

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
