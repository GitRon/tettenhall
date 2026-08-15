import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.handlers.commands.month import handle_create_player_month_log, handle_prepare_month
from apps.month.messages.commands.month import CreatePlayerMonthLog, PrepareMonth
from apps.month.messages.events.month import FactionMonthPrepared, PlayerMonthLogCreated
from apps.month.models.player_month_log import PlayerMonthLog
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


@pytest.mark.django_db
def test_handle_create_player_month_log_writes_the_line():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    result = handle_create_player_month_log(
        context=CreatePlayerMonthLog(
            title="The fyrd has grown by 1 new recruitee!", month=3, faction=savegame.player_faction
        )
    )

    player_month_log = PlayerMonthLog.objects.get()
    assert result == PlayerMonthLogCreated(player_month_log=player_month_log)
    assert player_month_log.title == "The fyrd has grown by 1 new recruitee!"


@pytest.mark.django_db
def test_handle_create_player_month_log_drops_the_line_of_a_rival_faction():
    """
    Recovery is faction-wide on purpose, so a rival's warriors produce these commands too. The
    choke point every producer passes through is the only place that can tell them apart - the
    producers are event handlers, where the traversal this does is blocked.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)

    result = handle_create_player_month_log(
        context=CreatePlayerMonthLog(title="Warrior RivalMan healed 2 HP.", month=3, faction=rival_faction)
    )

    assert result is None
    assert PlayerMonthLog.objects.exists() is False


@pytest.mark.django_db
def test_handle_create_player_month_log_without_a_player_faction():
    """
    Reachable before the player's faction exists: the savegame row is created first. Nobody to log
    for, so nothing is written rather than a row nobody can ever read.
    """
    savegame = SavegameFactory(player_faction=None)
    faction = FactionFactory(savegame=savegame)

    result = handle_create_player_month_log(
        context=CreatePlayerMonthLog(title="Buildings earned 50 silver this month.", month=3, faction=faction)
    )

    assert result is None
    assert PlayerMonthLog.objects.exists() is False
