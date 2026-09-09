from apps.warband.faction.messages.events.faction import FactionWasDefeated
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.handlers.events.faction import handle_determine_savegame_outcome
from apps.warband.savegame.messages.commands.savegame import DetermineSavegameOutcome
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


def test_handle_determine_savegame_outcome_maps_to_command():
    savegame = SavegameFactory.build()

    result = handle_determine_savegame_outcome(
        context=FactionWasDefeated(faction=FactionFactory.build(), savegame=savegame)
    )

    assert result == DetermineSavegameOutcome(savegame=savegame)
