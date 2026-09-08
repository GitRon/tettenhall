import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.models.player_month_log import PlayerMonthLog
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_for_player_faction_excludes_the_logs_of_rival_factions():
    """
    A savegame holds the player's faction plus its rivals, so scoping by savegame would still let
    the id from the URL reach a rival's log line.
    """
    savegame = SavegameFactory()
    player_month_log = PlayerMonthLogFactory(faction__savegame=savegame)
    PlayerMonthLogFactory(faction__savegame=savegame)

    result = PlayerMonthLog.objects.for_player_faction(faction_id=player_month_log.faction_id)

    assert list(result) == [player_month_log]


@pytest.mark.django_db
def test_create_record_derives_the_category_from_the_kind():
    """
    A producer names the kind and nothing else, so the two halves of how a line is read cannot be
    set against each other.
    """
    faction = FactionFactory()

    result = PlayerMonthLog.objects.create_record(
        title="Oswine left the war band over unpaid wages.",
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_WALKED_OUT,
        month=3,
        faction_id=faction.id,
    )

    assert result.category == PlayerMonthLog.CategoryChoices.CATEGORY_ATTENTION


@pytest.mark.django_db
def test_create_record_writes_the_body_a_chronicle_entry_carries():
    """
    The room the title has not got, filled only by the producers that have a second sentence to say.
    """
    faction = FactionFactory()

    result = PlayerMonthLog.objects.create_record(
        title="Wighelm has lost his spear in the moor.",
        body="He reports a revenant. Others report beer.",
        kind=PlayerMonthLog.KindChoices.KIND_INCIDENT,
        month=3,
        faction_id=faction.id,
    )

    assert result.body == "He reports a revenant. Others report beer."


@pytest.mark.django_db
def test_create_record_leaves_the_body_empty_for_every_other_producer():
    faction = FactionFactory()

    result = PlayerMonthLog.objects.create_record(
        title="Monthly salaries of 300 silver paid.",
        kind=PlayerMonthLog.KindChoices.KIND_SALARIES_PAID,
        month=3,
        faction_id=faction.id,
    )

    assert result.body == ""
