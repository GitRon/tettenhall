from apps.common.tests.html import parse, render_component
from apps.warband.quest.projections.board_quest import BoardQuest
from apps.warband.quest.quests.fetch_a_good_warrior import FetchAGoodWarrior
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.quests.merchant_guard import MerchantGuard
from apps.warband.quest.quests.seek_a_good_blade import SeekAGoodBlade
from apps.warband.quest.tests.factories.quest import QuestFactory

REWARD_TAGS_TAG = '<c-quest.reward-tags :board_quest="board_quest" />'


def _text(*, entry) -> str:
    html = render_component(
        tag=REWARD_TAGS_TAG, context={"board_quest": BoardQuest(quest=QuestFactory.build(), entry=entry)}
    )
    return " ".join(parse(html).get_text(" ").split())


def test_reward_tags_of_an_odd_job_name_its_silver_alone():
    result = _text(entry=MerchantGuard)

    assert result == "Silver 5\N{EN DASH}45 a man"


def test_reward_tags_of_a_renown_only_quest_name_no_silver():
    result = _text(entry=KingsSummons)

    assert result == "Renown up to 6 a man"


def test_reward_tags_of_an_item_quest_name_the_gear():
    result = _text(entry=SeekAGoodBlade)

    assert result == "Weapon"


def test_reward_tags_of_a_recruit_quest_say_a_man_joins():
    result = _text(entry=FetchAGoodWarrior)

    assert result == "A man joins"
