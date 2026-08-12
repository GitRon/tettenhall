import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.handlers.commands.month import handle_prepare_month
from apps.month.messages.commands.month import PrepareMonth
from apps.month.messages.events.month import FactionMonthPrepared
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_handle_prepare_month_advances_the_month():
    savegame = SavegameFactory(current_month=4)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    TrainingFactory(faction=savegame.player_faction)

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[0].current_month == 5
    savegame.refresh_from_db()
    assert savegame.current_month == 5


@pytest.mark.django_db
def test_handle_prepare_month_announces_the_month_for_every_faction():
    """
    The player's faction is announced like any other, so anything a faction does monthly reaches it
    without a second registration.
    """
    savegame = SavegameFactory(current_month=4)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[1:] == [
        FactionMonthPrepared(faction=savegame.player_faction, current_month=5),
        FactionMonthPrepared(faction=rival_faction, current_month=5),
    ]


@pytest.mark.django_db
def test_handle_prepare_month_leaves_out_the_factions_of_other_savegames():
    """
    Every savegame has its own factions, and the month of one player must not recover the warriors
    of somebody else's.
    """
    savegame = SavegameFactory(current_month=4, player_faction=None)
    FactionFactory()

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[1:] == []


@pytest.mark.django_db
def test_handle_prepare_month_takes_the_training_of_its_own_savegame():
    """
    Created first on purpose: an unscoped lookup takes whatever row comes first and would train the
    player's warriors according to this other savegame's training.
    """
    TrainingFactory()
    savegame = SavegameFactory(current_month=4)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    own_training = TrainingFactory(faction=savegame.player_faction)

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[0].training == own_training


@pytest.mark.django_db
def test_handle_prepare_month_takes_the_training_of_the_player_faction():
    """
    Every faction of the savegame owns a training row, so scoping to the savegame is not enough:
    the rival's row is created first here and would win a "first()" over the whole savegame.
    """
    savegame = SavegameFactory(current_month=4)
    rival_faction = FactionFactory(savegame=savegame)
    TrainingFactory(faction=rival_faction)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    own_training = TrainingFactory(faction=savegame.player_faction)

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[0].training == own_training


@pytest.mark.django_db
def test_handle_prepare_month_without_a_player_faction():
    """
    The training lookup needs a faction id. Reachable before the faction is set up, and the month
    still has to advance instead of answering with a 500.
    """
    savegame = SavegameFactory(current_month=4, player_faction=None)

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[0].training is None
    assert result[0].current_month == 5
