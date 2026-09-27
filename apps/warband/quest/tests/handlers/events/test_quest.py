import pytest

from apps.warband.quest.handlers.events.quest import handle_create_skirmish_for_quest_contract
from apps.warband.quest.messages.events.quest import QuestAccepted
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def _quest_accepted(*, fortification_strength: int = 0) -> QuestAccepted:
    quest_contract = QuestContractFactory(quest__fortification_strength=fortification_strength)
    assigned_warrior = WarriorFactory(faction=quest_contract.faction)
    quest_contract.assigned_warriors.add(assigned_warrior)

    return QuestAccepted(
        accepting_faction=quest_contract.faction,
        target_faction=quest_contract.quest.target_faction,
        quest=quest_contract.quest,
        quest_contract=quest_contract,
        assigned_warriors=[assigned_warrior],
        target_warriors=[WarriorFactory(faction=quest_contract.quest.target_faction)],
        month=3,
    )


@pytest.mark.django_db
def test_handle_create_skirmish_for_quest_contract_stages_a_walled_errand_behind_its_wall():
    result = handle_create_skirmish_for_quest_contract(context=_quest_accepted(fortification_strength=20))

    assert result.fortification_strength == 20


@pytest.mark.django_db
def test_handle_create_skirmish_for_quest_contract_stages_an_open_errand_in_open_country():
    result = handle_create_skirmish_for_quest_contract(context=_quest_accepted(fortification_strength=0))

    assert result.fortification_strength == 0


@pytest.mark.django_db
def test_handle_create_skirmish_for_quest_contract_fields_the_men_the_event_carries(django_assert_num_queries):
    context = _quest_accepted()

    with django_assert_num_queries(0):
        result = handle_create_skirmish_for_quest_contract(context=context)

    assert result.warrior_list_1 == context.assigned_warriors
