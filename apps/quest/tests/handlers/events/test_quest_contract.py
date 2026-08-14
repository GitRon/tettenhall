import pytest

from apps.quest.handlers.events.quest_contract import (
    handle_finish_quest_contract,
    handle_link_quest_contract_to_its_skirmish,
)
from apps.quest.messages.commands.quest_contract import AssignSkirmishToQuestContract, RemoveQuestContractAsActiveQuest
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.messages.events.skirmish import SkirmishCreated, SkirmishFinished
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_link_quest_contract_to_its_skirmish_assigns_the_contract():
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction)

    result = handle_link_quest_contract_to_its_skirmish(
        context=SkirmishCreated(skirmish=skirmish, quest_contract=quest_contract)
    )

    assert result == AssignSkirmishToQuestContract(quest_contract=quest_contract, skirmish=skirmish)


@pytest.mark.django_db
def test_handle_link_quest_contract_to_its_skirmish_stays_silent_without_a_contract():
    skirmish = SkirmishFactory()

    result = handle_link_quest_contract_to_its_skirmish(context=SkirmishCreated(skirmish=skirmish, quest_contract=None))

    assert result is None


@pytest.mark.django_db
def test_handle_finish_quest_contract_closes_the_contract_behind_the_skirmish():
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction, skirmish=skirmish)

    result = handle_finish_quest_contract(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid cattle",
            quest_loot=250,
            month=3,
        )
    )

    assert result == RemoveQuestContractAsActiveQuest(quest_contract=quest_contract, faction=skirmish.attacking_faction)


@pytest.mark.django_db
def test_handle_finish_quest_contract_stays_silent_for_a_skirmish_without_a_contract():
    skirmish = SkirmishFactory()

    result = handle_finish_quest_contract(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid cattle",
            quest_loot=250,
            month=3,
        )
    )

    assert result is None
