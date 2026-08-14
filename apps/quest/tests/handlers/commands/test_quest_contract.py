import pytest

from apps.faction.tests.factories.faction import FactionFactory
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
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction)

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
        context=RemoveQuestContractAsActiveQuest(quest_contract=quest_contract)
    )

    assert result == QuestContractAsActiveQuestRemoved(quest_contract=quest_contract, faction=faction)
    assert list(faction.active_quests.all()) == []


@pytest.mark.django_db
def test_handle_remove_quest_contract_as_active_quest_ignores_who_else_was_in_the_fight():
    """
    The signatory is the only faction that can hold the contract as an active quest.

    The command used to carry a faction of its own, filled with the skirmish's attacking side, and
    clearing the active quest of a faction that never signed is a silent no-op - so the holder kept a
    finished quest forever the moment the two came apart.
    """
    quest_contract = QuestContractFactory()
    signatory = quest_contract.faction
    signatory.active_quests.add(quest_contract)
    other_faction = FactionFactory(savegame=signatory.savegame)
    other_faction.active_quests.add(quest_contract)

    result = handle_remove_quest_contract_as_active_quest(
        context=RemoveQuestContractAsActiveQuest(quest_contract=quest_contract)
    )

    assert result == QuestContractAsActiveQuestRemoved(quest_contract=quest_contract, faction=signatory)
    assert list(signatory.active_quests.all()) == []
