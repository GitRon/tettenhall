import pytest

from apps.warband.quest.handlers.events.skirmish import (
    handle_finish_quest_contract,
    handle_link_quest_contract_to_its_skirmish,
)
from apps.warband.quest.messages.commands.quest_contract import (
    AssignSkirmishToQuestContract,
    RemoveQuestContractAsActiveQuest,
)
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.messages.events.skirmish import SkirmishCreated, SkirmishFinished
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory


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
def test_handle_finish_quest_contract_closes_the_contract_behind_the_skirmish(django_assert_num_queries):
    """
    A skirmish fetched fresh, so nothing has cached its contract: an event handler that followed the
    relation would pass here only by running the query strict mode blocks in a flow.
    """
    quest_contract = QuestContractFactory(skirmish=SkirmishFactory())
    context = SkirmishFinished(
        skirmish=Skirmish.objects.get(pk=quest_contract.skirmish_id),
        incapacitated_warriors=[],
        defeated_unconscious_warriors=[],
        victorious_healthy_warriors=[],
        quest_name="Raid cattle",
        quest_loot=250,
        quest_contract=quest_contract,
        month=3,
    )

    with django_assert_num_queries(0):
        result = handle_finish_quest_contract(context=context)

    assert result == RemoveQuestContractAsActiveQuest(quest_contract=quest_contract)


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
            quest_contract=None,
            month=3,
        )
    )

    assert result is None
