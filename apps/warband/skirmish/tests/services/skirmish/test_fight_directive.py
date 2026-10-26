import pytest

from apps.warband.skirmish.choices.fight_directive import FightDirectiveChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.choices.turning_point import TurningPointChoices
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.services.skirmish.fight_directive import get_directed_action, get_offered_directives
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_get_directed_action_gives_nothing_for_fighting_on():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    result = get_directed_action(directive=FightDirectiveChoices.FIGHT_ON, warrior=warrior, skirmish=skirmish)

    assert result is None


@pytest.mark.django_db
def test_get_directed_action_orders_the_leader():
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_faction.leader = leader
    skirmish.attacking_faction.save()
    skirmish.attacking_warriors.add(leader)

    result = get_directed_action(directive=FightDirectiveChoices.RALLY, warrior=leader, skirmish=skirmish)

    assert result == SkirmishActionChoices.RALLY


@pytest.mark.django_db
def test_get_directed_action_leaves_out_a_man_an_order_for_the_leader_does_not_mean():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    result = get_directed_action(directive=FightDirectiveChoices.LEAVE_THE_FIELD, warrior=warrior, skirmish=skirmish)

    assert result is None


@pytest.mark.django_db
def test_get_directed_action_never_hands_out_an_action_the_man_is_not_offered():
    """
    The defender has nowhere to flee to, so the retreat orders him nothing and he decides for himself.
    """
    skirmish = SkirmishFactory()
    defender = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(defender)

    result = get_directed_action(directive=FightDirectiveChoices.SOUND_THE_RETREAT, warrior=defender, skirmish=skirmish)

    assert result is None


@pytest.mark.django_db
def test_get_offered_directives_drops_what_nobody_on_the_side_can_do():
    """
    A side of novices cannot press the attack, so the stop offers it no button for it.
    """
    skirmish = SkirmishFactory()
    novice = WarriorFactory(faction=skirmish.attacking_faction, experience=0)
    skirmish.attacking_warriors.add(novice)

    result = get_offered_directives(
        turning_point=TurningPointChoices.ENEMY_LEADER_EXPOSED, skirmish=skirmish, roster=[novice]
    )

    assert result == []


@pytest.mark.django_db
def test_get_offered_directives_keeps_what_one_man_on_the_side_can_do():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    result = get_offered_directives(turning_point=TurningPointChoices.MAN_DOWN, skirmish=skirmish, roster=[warrior])

    assert result == [FightDirectiveChoices.SOUND_THE_RETREAT]


@pytest.mark.django_db
def test_get_offered_directives_asks_only_the_men_still_standing():
    skirmish = SkirmishFactory()
    fallen = WarriorFactory(faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    skirmish.attacking_warriors.add(fallen)

    result = get_offered_directives(turning_point=TurningPointChoices.MAN_DOWN, skirmish=skirmish, roster=[fallen])

    assert result == []
