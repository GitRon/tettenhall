from apps.quest.tests.factories.quest import QuestFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory


def test_str_returns_the_quest_name():
    quest_contract = QuestContractFactory.build(quest=QuestFactory.build(name="Pillage village"))

    assert str(quest_contract) == "Pillage village"
