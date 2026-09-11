import pytest

from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory


def test_str_returns_the_name():
    skirmish = SkirmishFactory.build(name="Raid on Tettenhall")

    assert str(skirmish) == "Raid on Tettenhall"


def test_rounds_fought_counts_what_is_behind_the_fight():
    skirmish = SkirmishFactory.build(current_round=4)

    assert skirmish.rounds_fought == 3


def test_rounds_fought_is_nothing_before_the_first_blow():
    skirmish = SkirmishFactory.build()

    assert skirmish.rounds_fought == 0


@pytest.mark.django_db
def test_quest_reward_for_pays_nothing_for_a_fight_that_is_nobody_s_errand():
    """
    A march on a rival carries no contract, so there is no name to report and no purse to hand over.
    """
    skirmish = SkirmishFactory()

    assert skirmish.quest_reward_for(victorious_faction=skirmish.attacking_faction) == (None, 0)


@pytest.mark.django_db
def test_quest_reward_for_keeps_the_purse_from_a_victor_who_signed_nothing():
    """
    The rival who took the field hears what he interrupted and is paid none of it - the reward is
    handed to whoever won further down the chain, so a purse carried regardless of the outcome funded
    the man who beat the signatory out of his own quest.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction, skirmish=skirmish, quest__loot=250)

    assert skirmish.quest_reward_for(victorious_faction=skirmish.defending_faction) == (
        quest_contract.quest.name,
        0,
    )


@pytest.mark.django_db
def test_quest_reward_for_pays_the_signatory_the_face_value():
    """
    Signed price, paid in full: the purse was priced against the opposition when the quest was pinned
    to the board, so what the player accepted is what he collects.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction, skirmish=skirmish, quest__loot=250)

    assert skirmish.quest_reward_for(victorious_faction=skirmish.attacking_faction) == (
        quest_contract.quest.name,
        250,
    )
