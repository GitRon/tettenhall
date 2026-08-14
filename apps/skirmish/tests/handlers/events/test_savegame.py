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
            savegame=SavegameFactory.build(player_faction=skirmish.attacking_faction),
            outcome=Savegame.OutcomeChoices.OUTCOME_WON,
            open_skirmish_list=[skirmish],
            month=3,
        )
    )

    assert result == [WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)]


@pytest.mark.django_db
def test_handle_win_open_skirmishes_when_the_game_ends_gives_a_lost_game_to_the_opponent():
    skirmish = SkirmishFactory()

    result = handle_win_open_skirmishes_when_the_game_ends(
        context=SavegameEnded(
            savegame=SavegameFactory.build(player_faction=skirmish.attacking_faction),
            outcome=Savegame.OutcomeChoices.OUTCOME_LOST,
            open_skirmish_list=[skirmish],
            month=3,
        )
    )

    assert result == [WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.defending_faction, month=3)]


@pytest.mark.django_db
def test_handle_win_open_skirmishes_when_the_game_ends_gives_a_won_game_to_the_defending_player():
    """
    The player is on the defending side here, so a won game has to go to the defender.

    Reading the player off side one would have handed the fight to the faction that marched against
    him - the reason this asks the savegame rather than the skirmish row.
    """
    skirmish = SkirmishFactory()

    result = handle_win_open_skirmishes_when_the_game_ends(
        context=SavegameEnded(
            savegame=SavegameFactory.build(player_faction=skirmish.defending_faction),
            outcome=Savegame.OutcomeChoices.OUTCOME_WON,
            open_skirmish_list=[skirmish],
            month=3,
        )
    )

    assert result == [WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.defending_faction, month=3)]


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
