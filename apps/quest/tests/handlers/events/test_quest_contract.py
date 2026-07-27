import pytest

from apps.quest.handlers.events.quest_contract import handle_finish_quest_contract
from apps.quest.messages.commands.quest_contract import RemoveQuestContractAsActiveQuest
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_finish_quest_contract_closes_the_contract_behind_the_skirmish():
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.player_faction, skirmish=skirmish)

    result = handle_finish_quest_contract(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_conscious_warriors=[],
            quest_name="Raid cattle",
            quest_loot=250,
            month=3,
        )
    )

    assert result == RemoveQuestContractAsActiveQuest(quest_contract=quest_contract, faction=skirmish.player_faction)


@pytest.mark.django_db
def test_handle_finish_quest_contract_stays_silent_for_a_skirmish_without_a_contract():
    skirmish = SkirmishFactory()

    result = handle_finish_quest_contract(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_conscious_warriors=[],
            quest_name="Raid cattle",
            quest_loot=250,
            month=3,
        )
    )

    assert result is None
