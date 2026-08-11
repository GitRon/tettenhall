import pytest

from apps.quest.handlers.commands.quest_contract import (
    handle_assign_skirmish_to_quest_contract,
    handle_remove_quest_contract_as_active_quest,
)
from apps.quest.messages.commands.quest_contract import AssignSkirmishToQuestContract, RemoveQuestContractAsActiveQuest
from apps.quest.messages.events.quest_contract import QuestContractAsActiveQuestRemoved, SkirmishToQuestContractAssigned
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_assign_skirmish_to_quest_contract_stores_the_link():
    """
    This handler is the only writer of the link, so nothing but a flow test on the quest view would
    notice it regressing - and that one would blame the view rather than the handler.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.player_faction)

    result = handle_assign_skirmish_to_quest_contract(
        context=AssignSkirmishToQuestContract(quest_contract=quest_contract, skirmish=skirmish)
    )

    assert result == SkirmishToQuestContractAssigned(quest_contract=quest_contract)
    quest_contract.refresh_from_db()
    assert quest_contract.skirmish == skirmish


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
