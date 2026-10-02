import pytest

from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory


@pytest.mark.django_db
def test_quest_contract_str():
    quest_contract = QuestContractFactory(title="A thegn wants hands.")

    assert str(quest_contract) == "A thegn wants hands."
