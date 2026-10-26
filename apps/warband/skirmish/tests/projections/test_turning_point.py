import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.choices.fight_directive import FightDirectiveChoices
from apps.warband.skirmish.choices.turning_point import TurningPointChoices
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.projections.turning_point import PendingTurningPoint
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_is_leader_threatened():
    pending = PendingTurningPoint(
        turning_point=TurningPointChoices.LEADER_THREATENED, directives=[], fallen=[], leader=None
    )

    assert pending.is_leader_threatened is True


def test_is_man_down():
    pending = PendingTurningPoint(
        turning_point=TurningPointChoices.ENEMY_LEADER_EXPOSED, directives=[], fallen=[], leader=None
    )

    assert pending.is_man_down is False


@pytest.mark.django_db
def test_for_skirmish_without_a_stop_is_nothing():
    skirmish = SkirmishFactory()

    result = PendingTurningPoint.for_skirmish(skirmish=skirmish, player_faction_id=skirmish.attacking_faction_id)

    assert result is None


@pytest.mark.django_db
def test_for_skirmish_that_is_decided_is_nothing():
    skirmish = SkirmishFactory(turning_point=TurningPointChoices.MAN_DOWN)
    skirmish.victorious_faction = skirmish.defending_faction
    skirmish.save()

    result = PendingTurningPoint.for_skirmish(skirmish=skirmish, player_faction_id=skirmish.attacking_faction_id)

    assert result is None


@pytest.mark.django_db
def test_for_skirmish_the_player_has_no_side_in_is_nothing():
    skirmish = SkirmishFactory(turning_point=TurningPointChoices.MAN_DOWN)
    bystander = FactionFactory(savegame=skirmish.attacking_faction.savegame)

    result = PendingTurningPoint.for_skirmish(skirmish=skirmish, player_faction_id=bystander.id)

    assert result is None


@pytest.mark.django_db
def test_for_skirmish_names_the_fallen_and_what_the_side_can_still_do():
    skirmish = SkirmishFactory(turning_point=TurningPointChoices.MAN_DOWN)
    standing = WarriorFactory(faction=skirmish.attacking_faction)
    fallen = WarriorFactory(faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    skirmish.attacking_warriors.add(standing, fallen)
    skirmish.turning_point_warriors.add(fallen)

    result = PendingTurningPoint.for_skirmish(skirmish=skirmish, player_faction_id=skirmish.attacking_faction_id)

    assert result == PendingTurningPoint(
        turning_point=TurningPointChoices.MAN_DOWN,
        directives=[FightDirectiveChoices.SOUND_THE_RETREAT],
        fallen=[fallen],
        leader=None,
    )


@pytest.mark.django_db
def test_for_skirmish_names_the_enemy_leader_exposed_to_the_defending_player():
    skirmish = SkirmishFactory(turning_point=TurningPointChoices.ENEMY_LEADER_EXPOSED)
    enemy_leader = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_faction.leader = enemy_leader
    skirmish.attacking_faction.save()
    skirmish.attacking_warriors.add(enemy_leader)

    result = PendingTurningPoint.for_skirmish(skirmish=skirmish, player_faction_id=skirmish.defending_faction_id)

    assert result.leader == enemy_leader
