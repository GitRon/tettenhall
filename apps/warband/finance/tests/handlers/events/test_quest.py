import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.handlers.events.quest import handle_quest_silver
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_quest_silver_pays_every_man_who_came_home():
    faction = FactionFactory()
    warriors = WarriorFactory.create_batch(2, faction=faction)
    outcome = HarvestHands.OUTCOMES[0]

    result = handle_quest_silver(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=warriors,
            outcome=outcome,
            month=3,
        )
    )

    assert result == CreateTransaction(
        faction=faction, amount=outcome.silver_per_man * 2, reason=outcome.title, month=3
    )


@pytest.mark.django_db
def test_handle_quest_silver_for_an_outcome_paying_none():
    faction = FactionFactory()

    result = handle_quest_silver(
        context=QuestContractReturned(
            faction=faction,
            quest_contract=QuestContractFactory(faction=faction),
            warriors=[WarriorFactory(faction=faction)],
            outcome=KingsSummons.OUTCOMES[0],
            month=3,
        )
    )

    assert result is None
