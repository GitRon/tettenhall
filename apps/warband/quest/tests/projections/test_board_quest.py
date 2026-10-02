from apps.warband.quest.projections.board_quest import BoardQuest
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.tests.factories.quest import QuestFactory


def test_board_quest_leans_on_label():
    board_quest = BoardQuest(quest=QuestFactory.build(), entry=KingsSummons)

    assert board_quest.leans_on_label == "Maximum morale"
