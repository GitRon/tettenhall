import pytest

from apps.savegame.messages.events.savegame import SavegameEnded
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.handlers.events.savegame import handle_win_open_skirmishes_when_the_game_ends
from apps.skirmish.messages.commands.skirmish import WinSkirmish
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_win_open_skirmishes_when_the_game_ends_gives_a_won_game_to_the_player():
    skirmish = SkirmishFactory()

    result = handle_win_open_skirmishes_when_the_game_ends(
        context=SavegameEnded(
            savegame=SavegameFactory.build(),
            outcome=Savegame.OutcomeChoices.OUTCOME_WON,
            open_skirmish_list=[skirmish],
            month=3,
        )
    )

    assert result == [WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.player_faction, month=3)]


@pytest.mark.django_db
def test_handle_win_open_skirmishes_when_the_game_ends_gives_a_lost_game_to_the_opponent():
    skirmish = SkirmishFactory()

    result = handle_win_open_skirmishes_when_the_game_ends(
        context=SavegameEnded(
            savegame=SavegameFactory.build(),
            outcome=Savegame.OutcomeChoices.OUTCOME_LOST,
            open_skirmish_list=[skirmish],
            month=3,
        )
    )

    assert result == [WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.non_player_faction, month=3)]


def test_handle_win_open_skirmishes_when_the_game_ends_without_an_open_fight():
    result = handle_win_open_skirmishes_when_the_game_ends(
        context=SavegameEnded(
            savegame=SavegameFactory.build(),
            outcome=Savegame.OutcomeChoices.OUTCOME_WON,
            open_skirmish_list=[],
            month=3,
        )
    )

    assert result == []
