from apps.warband.faction.messages.events.faction import FactionWasDefeated
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.handlers.events.faction import handle_determine_savegame_outcome
from apps.warband.savegame.messages.commands.savegame import DetermineSavegameOutcome
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_determine_savegame_outcome_maps_to_command():
    savegame = SavegameFactory.build()

    result = handle_determine_savegame_outcome(
        context=FactionWasDefeated(
            faction=FactionFactory.build(),
            savegame=savegame,
            player_faction=FactionFactory.build(),
            leader=WarriorFactory.build(),
            leader_was_killed=True,
            month=3,
        )
    )

    assert result == DetermineSavegameOutcome(savegame=savegame)
