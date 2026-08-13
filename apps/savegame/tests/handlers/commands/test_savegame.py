import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.handlers.commands.savegame import handle_determine_savegame_outcome
from apps.savegame.messages.commands.savegame import DetermineSavegameOutcome
from apps.savegame.messages.events.savegame import SavegameEnded
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_determine_savegame_outcome_is_lost_without_the_player():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame, is_defeated=True)
    savegame.save()
    FactionFactory(savegame=savegame)

    result = handle_determine_savegame_outcome(context=DetermineSavegameOutcome(savegame=savegame))

    assert result == SavegameEnded(
        savegame=savegame,
        outcome=Savegame.OutcomeChoices.OUTCOME_LOST,
        open_skirmish_list=[],
        month=savegame.current_month,
    )
    savegame.refresh_from_db()
    assert savegame.outcome == Savegame.OutcomeChoices.OUTCOME_LOST


@pytest.mark.django_db
def test_handle_determine_savegame_outcome_is_won_without_a_rival():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    FactionFactory(savegame=savegame, is_defeated=True)

    result = handle_determine_savegame_outcome(context=DetermineSavegameOutcome(savegame=savegame))

    assert result.outcome == Savegame.OutcomeChoices.OUTCOME_WON
    savegame.refresh_from_db()
    assert savegame.outcome == Savegame.OutcomeChoices.OUTCOME_WON


@pytest.mark.django_db
def test_handle_determine_savegame_outcome_stays_silent_while_rivals_remain():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    FactionFactory(savegame=savegame, is_defeated=True)
    FactionFactory(savegame=savegame)

    result = handle_determine_savegame_outcome(context=DetermineSavegameOutcome(savegame=savegame))

    assert result is None


@pytest.mark.django_db
def test_handle_determine_savegame_outcome_stays_silent_for_a_finished_game():
    """
    The guard that stops the chain looping: force-resolving the last fight captures warriors, which
    can defeat another leader's faction, which lands right back here.
    """
    savegame = SavegameFactory(outcome=Savegame.OutcomeChoices.OUTCOME_WON)
    savegame.player_faction = FactionFactory(savegame=savegame, is_defeated=True)
    savegame.save()

    result = handle_determine_savegame_outcome(context=DetermineSavegameOutcome(savegame=savegame))

    assert result is None


@pytest.mark.django_db
def test_handle_determine_savegame_outcome_carries_the_unresolved_skirmish():
    """
    The fight the game ended in is still open, and the event handler deciding it cannot go looking.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame, is_defeated=True)
    savegame.save()
    skirmish = SkirmishFactory(player_faction=savegame.player_faction)

    result = handle_determine_savegame_outcome(context=DetermineSavegameOutcome(savegame=savegame))

    assert result.open_skirmish_list == [skirmish]
