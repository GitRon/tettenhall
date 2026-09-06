from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
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


def test_level_for_an_untested_warrior():
    assert Warrior.level_for(experience=0) == 1


def test_level_for_one_point_short_of_the_first_threshold():
    assert Warrior.level_for(experience=99) == 1


def test_level_for_the_first_threshold():
    assert Warrior.level_for(experience=100) == 2


def test_level_for_one_point_short_of_the_second_threshold():
    assert Warrior.level_for(experience=399) == 2


def test_level_for_the_second_threshold():
    assert Warrior.level_for(experience=400) == 3


def test_level_reads_the_warriors_own_experience():
    warrior = WarriorFactory.build(experience=400)

    assert warrior.level == 3


def test_experience_for_next_level_is_the_threshold_ahead():
    warrior = WarriorFactory.build(experience=100)

    assert warrior.experience_for_next_level == 400


@pytest.mark.django_db
def test_roll_attack_hands_back_the_notation_it_rolled():
    """
    The notation travels with the number because the fight is about to blend the number away, and a
    recorded total on its own can never be measured against what the weapon could have done.
    """
    warrior = WarriorFactory(
        weapon=ItemFactory(type=ItemTypeFactory(base_value="2d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON))
    )

    with mock.patch("apps.common.domain.dice.random.randint", return_value=4):
        result = warrior.roll_attack()

    assert result == DiceRoll(notation=DiceNotation(dice_string="2d6"), result=8)


@pytest.mark.django_db
def test_roll_defense_hands_back_the_notation_it_rolled():
    warrior = WarriorFactory(
        armor=ItemFactory(
            type=ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR), modifier=2
        )
    )

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = warrior.roll_defense()

    assert result == DiceRoll(notation=DiceNotation(dice_string="1d4", modifier=2), result=5)
