import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.events.quest import (
    handle_write_lapsed_quest_to_month_log,
    handle_write_returned_quest_to_month_log,
)
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.messages.events.quest_contract import QuestContractLapsed, QuestContractReturned
from apps.warband.quest.quests.base import Quest, QuestOutcome
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.fetch_a_good_warrior import FetchAGoodWarrior
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.quests.merchant_guard import MerchantGuard
from apps.warband.quest.quests.seek_a_good_blade import SeekAGoodBlade
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_write_returned_quest_to_month_log():
    faction = FactionFactory()
    outcome = HarvestHands.OUTCOMES[0]

    result = handle_write_returned_quest_to_month_log(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=outcome,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title=outcome.title,
        body=outcome.body,
        tags=["35 silver"],
        kind=PlayerMonthLog.KindChoices.KIND_QUEST_RETURNED,
        month=3,
        faction=faction,
    )


def _returned(*, outcome: QuestOutcome, men_home: int) -> QuestContractReturned:
    faction = FactionFactory()
    return QuestContractReturned(
        faction=faction,
        quest_contract=QuestContractFactory(faction=faction),
        warriors=WarriorFactory.create_batch(men_home, faction=faction),
        outcome=outcome,
        month=3,
    )


@pytest.mark.django_db
def test_handle_write_returned_quest_to_month_log_counts_silver_over_the_men_who_came_home():
    """Three men home of however many were sent: the tag is the purse total, the ledger's own sum."""
    context = _returned(outcome=MerchantGuard.OUTCOMES[0], men_home=3)

    result = handle_write_returned_quest_to_month_log(context=context)

    assert result.tags == ["135 silver"]


@pytest.mark.django_db
def test_handle_write_returned_quest_to_month_log_tags_renown_a_man():
    context = _returned(outcome=KingsSummons.OUTCOMES[0], men_home=2)

    result = handle_write_returned_quest_to_month_log(context=context)

    assert result.tags == ["6 renown a man"]


@pytest.mark.django_db
def test_handle_write_returned_quest_to_month_log_tags_the_gear():
    context = _returned(outcome=SeekAGoodBlade.OUTCOMES[0], men_home=2)

    result = handle_write_returned_quest_to_month_log(context=context)

    assert result.tags == ["Weapon"]


@pytest.mark.django_db
def test_handle_write_returned_quest_to_month_log_tags_the_recruit():
    context = _returned(outcome=FetchAGoodWarrior.OUTCOMES[0], men_home=2)

    result = handle_write_returned_quest_to_month_log(context=context)

    assert result.tags == ["A man joins"]


@pytest.mark.django_db
def test_handle_write_returned_quest_to_month_log_of_an_outcome_that_pays_nothing():
    """No "0 silver": a lever the outcome does not pull says nothing."""
    context = _returned(outcome=DriveOffWolves.OUTCOMES[1], men_home=2)

    result = handle_write_returned_quest_to_month_log(context=context)

    assert result.tags == []


@pytest.mark.django_db
def test_handle_write_lapsed_quest_to_month_log():
    faction = FactionFactory()

    result = handle_write_lapsed_quest_to_month_log(
        context=QuestContractLapsed(faction=faction, quest_contract=QuestContractFactory(faction=faction), month=3)
    )

    assert result == CreatePlayerMonthLog(
        title=Quest.LAPSED_TITLE,
        body=Quest.LAPSED_BODY,
        kind=PlayerMonthLog.KindChoices.KIND_QUEST_RETURNED,
        month=3,
        faction=faction,
    )
