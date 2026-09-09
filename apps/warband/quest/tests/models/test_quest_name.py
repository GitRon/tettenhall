from apps.warband.quest.models.quest_name import QuestName


def test_str_is_the_name():
    quest_name = QuestName(name="Raid cattle")

    assert str(quest_name) == "Raid cattle"
