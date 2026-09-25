import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


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


@pytest.mark.django_db
def test_can_be_assaulted_by_an_attacker_while_the_wall_stands():
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    assert skirmish.can_be_assaulted_by(warrior=warrior) is True


@pytest.mark.django_db
def test_can_be_assaulted_by_is_refused_to_a_defender():
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(warrior)

    assert skirmish.can_be_assaulted_by(warrior=warrior) is False


@pytest.mark.django_db
def test_can_be_rallied_by_the_leader_of_the_attacking_side():
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_faction.leader = leader
    skirmish.attacking_faction.save()
    skirmish.attacking_warriors.add(leader)

    assert skirmish.can_be_rallied_by(warrior=leader) is True


@pytest.mark.django_db
def test_can_be_rallied_by_the_leader_of_the_defending_side():
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_faction.leader = leader
    skirmish.defending_faction.save()
    skirmish.defending_warriors.add(leader)

    assert skirmish.can_be_rallied_by(warrior=leader) is True


@pytest.mark.django_db
def test_can_be_rallied_by_is_refused_to_a_man_who_leads_nobody_here():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    assert skirmish.can_be_rallied_by(warrior=warrior) is False


@pytest.mark.django_db
def test_can_be_rallied_by_is_refused_to_a_recruited_rival_leader():
    """
    A captured leader recruited into the war band that took him still stands as "leader" of the faction
    he came from, and leads nobody on the side he fights for now.
    """
    skirmish = SkirmishFactory()
    rival = FactionFactory(savegame=skirmish.attacking_faction.savegame)
    former_leader = WarriorFactory(faction=skirmish.attacking_faction)
    rival.leader = former_leader
    rival.save()
    skirmish.attacking_warriors.add(former_leader)

    assert skirmish.can_be_rallied_by(warrior=former_leader) is False


@pytest.mark.django_db
def test_can_be_rallied_by_is_refused_to_a_man_not_in_the_fight():
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_faction.leader = leader
    skirmish.attacking_faction.save()

    assert skirmish.can_be_rallied_by(warrior=leader) is False


@pytest.mark.django_db
def test_can_be_assaulted_by_is_refused_once_the_wall_has_fallen():
    skirmish = SkirmishFactory(fortification_strength=0)
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    assert skirmish.can_be_assaulted_by(warrior=warrior) is False
