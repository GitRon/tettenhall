from apps.warband.quest.projections.board_quest import BoardQuest
from apps.warband.quest.quests.base import Quest, QuestOutcome
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.fetch_a_good_warrior import FetchAGoodWarrior
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.quests.merchant_guard import MerchantGuard
from apps.warband.quest.quests.seek_a_good_blade import SeekAGoodBlade
from apps.warband.quest.tests.factories.quest import QuestFactory


def _board_quest(entry) -> BoardQuest:
    return BoardQuest(quest=QuestFactory.build(), entry=entry)


def test_board_quest_leans_on_label():
    board_quest = _board_quest(KingsSummons)

    assert board_quest.leans_on_label == "Maximum morale"


def test_board_quest_leans_on_hint_names_the_attribute():
    board_quest = _board_quest(MerchantGuard)

    assert board_quest.leans_on_hint == (
        "The more dexterity the men you send have between them, the likelier it goes well."
    )


def test_board_quest_silver_per_man_label_spans_the_outcomes():
    board_quest = _board_quest(MerchantGuard)

    assert board_quest.silver_per_man_label == "5\N{EN DASH}45"


def test_board_quest_silver_per_man_label_where_an_outcome_pays_nothing():
    board_quest = _board_quest(DriveOffWolves)

    assert board_quest.silver_per_man_label == "up to 15"


def test_board_quest_silver_per_man_label_for_a_quest_that_pays_none():
    board_quest = _board_quest(KingsSummons)

    assert board_quest.silver_per_man_label is None


def test_board_quest_renown_per_man_label_where_every_outcome_pays_the_same():
    """Every outcome the same amount: one figure, not a range from it to itself."""

    class SteadyRenown(Quest):
        OUTCOMES = (
            QuestOutcome(key="well", weight=1, is_success=True, title="", body="", renown_per_man=4),
            QuestOutcome(key="badly", weight=1, is_success=False, title="", body="", renown_per_man=4),
        )

    board_quest = _board_quest(SteadyRenown)

    assert board_quest.renown_per_man_label == "4"


def test_board_quest_renown_per_man_label_of_a_renown_only_quest():
    board_quest = _board_quest(KingsSummons)

    assert board_quest.renown_per_man_label == "up to 6"


def test_board_quest_item_labels_name_the_gear_it_can_find():
    board_quest = _board_quest(SeekAGoodBlade)

    assert board_quest.item_labels == ["Weapon"]


def test_board_quest_item_labels_of_a_quest_that_finds_none():
    board_quest = _board_quest(MerchantGuard)

    assert board_quest.item_labels == []


def test_board_quest_brings_a_man():
    board_quest = _board_quest(FetchAGoodWarrior)

    assert board_quest.brings_a_man is True


def test_board_quest_brings_no_man():
    board_quest = _board_quest(MerchantGuard)

    assert board_quest.brings_a_man is False
