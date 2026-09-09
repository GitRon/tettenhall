import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.commands.month import handle_create_player_month_log, handle_prepare_month
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog, PrepareMonth
from apps.warband.month.messages.events.month import FactionMonthPrepared, PlayerMonthLogCreated
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_handle_prepare_month_advances_the_month():
    savegame = SavegameFactory(current_month=4)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

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
def test_handle_prepare_month_without_a_player_faction():
    """
    Reachable before the faction is set up, and the month still has to advance instead of answering
    with a 500.
    """
    savegame = SavegameFactory(current_month=4, player_faction=None)

    result = handle_prepare_month(context=PrepareMonth(savegame=savegame))

    assert result[0].faction is None
    assert result[0].current_month == 5


@pytest.mark.django_db
def test_handle_create_player_month_log_writes_the_line():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    result = handle_create_player_month_log(
        context=CreatePlayerMonthLog(
            title="The fyrd has grown by 1 new recruit!",
            kind=PlayerMonthLog.KindChoices.KIND_FYRD_GROWTH,
            month=3,
            faction=savegame.player_faction,
        )
    )

    player_month_log = PlayerMonthLog.objects.get()
    assert result == PlayerMonthLogCreated(player_month_log=player_month_log)
    assert player_month_log.title == "The fyrd has grown by 1 new recruit!"


@pytest.mark.django_db
def test_handle_create_player_month_log_derives_the_category_from_the_kind():
    """
    The producer names one thing, so a line cannot be filed under a weight that contradicts what it
    reports.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    handle_create_player_month_log(
        context=CreatePlayerMonthLog(
            title="Oswine left the war band over unpaid wages.",
            kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_WALKED_OUT,
            month=3,
            faction=savegame.player_faction,
        )
    )

    assert PlayerMonthLog.objects.get().category == PlayerMonthLog.CategoryChoices.CATEGORY_ATTENTION


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
        context=CreatePlayerMonthLog(
            title="Warrior RivalMan healed 2 HP.",
            kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
            month=3,
            faction=rival_faction,
        )
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
        context=CreatePlayerMonthLog(
            title="Buildings earned 50 silver this month.",
            kind=PlayerMonthLog.KindChoices.KIND_BUILDING_INCOME,
            month=3,
            faction=faction,
        )
    )

    assert result is None
    assert PlayerMonthLog.objects.exists() is False
