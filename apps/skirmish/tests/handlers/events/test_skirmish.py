import pytest

from apps.skirmish.handlers.events.skirmish import handle_round_finished
from apps.skirmish.messages.commands.skirmish import WinSkirmish
from apps.skirmish.messages.events.skirmish import RoundFinished
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_round_finished_wins_the_skirmish_for_the_victor():
    skirmish = SkirmishFactory()

    result = handle_round_finished(context=RoundFinished(skirmish=skirmish, victor=skirmish.player_faction, month=3))

    assert result == WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.player_faction, month=3)


@pytest.mark.django_db
def test_handle_round_finished_does_nothing_without_a_victor():
    skirmish = SkirmishFactory()

    result = handle_round_finished(context=RoundFinished(skirmish=skirmish, victor=None, month=3))

    assert result is None
