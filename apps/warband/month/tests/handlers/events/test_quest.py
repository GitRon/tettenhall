import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.events.quest import (
    handle_write_lapsed_quest_to_month_log,
    handle_write_returned_quest_to_month_log,
)
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.quest.messages.events.quest_contract import QuestContractLapsed, QuestContractReturned
from apps.warband.quest.quests.base import Quest
from apps.warband.quest.quests.harvest_hands import HarvestHands
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
        kind=PlayerMonthLog.KindChoices.KIND_QUEST_RETURNED,
        month=3,
        faction=faction,
    )


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
