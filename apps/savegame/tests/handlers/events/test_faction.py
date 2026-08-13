from apps.faction.messages.events.faction import FactionWasDefeated
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.handlers.events.faction import handle_determine_savegame_outcome
from apps.savegame.messages.commands.savegame import DetermineSavegameOutcome
from apps.savegame.tests.factories.savegame import SavegameFactory


def test_handle_determine_savegame_outcome_maps_to_command():
    savegame = SavegameFactory.build()

    result = handle_determine_savegame_outcome(
        context=FactionWasDefeated(faction=FactionFactory.build(), savegame=savegame)
    )

    assert result == DetermineSavegameOutcome(savegame=savegame)
