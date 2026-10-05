import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
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
def test_can_be_fled_by_an_attacker():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    assert skirmish.can_be_fled_by(warrior=warrior) is True


@pytest.mark.django_db
def test_can_be_fled_by_is_refused_to_a_defending_leader():
    """
    The leader is the one a flight would matter for, and he is refused like every other defender: his
    town is occupied a click later, and the occupation takes him where he stands.
    """
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_faction.leader = leader
    skirmish.defending_faction.save()
    skirmish.defending_warriors.add(leader)

    assert skirmish.can_be_fled_by(warrior=leader) is False


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
