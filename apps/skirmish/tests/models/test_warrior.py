from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_is_dead_for_a_killed_warrior():
    warrior = WarriorFactory.build(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert warrior.is_dead is True


def test_is_unconscious_for_an_incapacitated_warrior():
    warrior = WarriorFactory.build(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    assert warrior.is_unconscious is True


def test_is_fleeing_for_a_warrior_out_of_morale():
    warrior = WarriorFactory.build(condition=Warrior.ConditionChoices.CONDITION_FLEEING)

    assert warrior.is_fleeing is True
