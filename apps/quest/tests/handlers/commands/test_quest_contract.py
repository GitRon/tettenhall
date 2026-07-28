import pytest

from apps.quest.handlers.commands.quest_contract import handle_remove_quest_contract_as_active_quest
from apps.quest.messages.commands.quest_contract import RemoveQuestContractAsActiveQuest
from apps.quest.messages.events.quest_contract import QuestContractAsActiveQuestRemoved
from apps.quest.tests.factories.quest_contract import QuestContractFactory


@pytest.mark.django_db
def test_handle_remove_quest_contract_as_active_quest_takes_it_off_the_faction():
    quest_contract = QuestContractFactory()
    faction = quest_contract.faction
    faction.active_quests.add(quest_contract)

    result = handle_remove_quest_contract_as_active_quest(
        context=RemoveQuestContractAsActiveQuest(quest_contract=quest_contract, faction=faction)
    )

    assert result == QuestContractAsActiveQuestRemoved(quest_contract=quest_contract, faction=faction)
    assert list(faction.active_quests.all()) == []
