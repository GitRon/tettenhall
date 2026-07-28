from apps.faction.handlers.events.faction import (
    handle_create_player_faction_for_new_savegame,
    handle_earn_money_from_buildings_for_new_month,
    handle_warriors_with_reduced_morale_determined,
)
from apps.faction.messages.commands.faction import CreateFactionsForNewSavegame, EarnMoneyFromBuildings
from apps.faction.messages.events.faction import FactionWarriorsWithReducedMoraleDetermined
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.messages.events.month import MonthPrepared
from apps.savegame.messages.events.savegame import NewSavegameCreated
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.training.tests.factories.training import TrainingFactory
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


def test_handle_earn_money_from_buildings_for_new_month_maps_to_command():
    faction = FactionFactory.build()
    context = MonthPrepared(
        faction=faction, savegame=SavegameFactory.build(), training=TrainingFactory.build(), current_month=7
    )

    result = handle_earn_money_from_buildings_for_new_month(context=context)

    assert result == EarnMoneyFromBuildings(faction=faction, month=7)
