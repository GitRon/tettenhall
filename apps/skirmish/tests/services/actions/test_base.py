from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.services.actions.base import AttackService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_get_pair_matching_points_is_the_dexterity():
    result = AttackService.get_pair_matching_points(warrior_dexterity=7)

    assert result == 7


@pytest.mark.django_db
def test_get_attack_value_for_a_warrior_at_his_own_baseline():
    """
    A man of his kind's average strength deals what his weapon rolls and nothing more, whatever that
    average happens to be - here a levy's five rather than the mercenary ten.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=5, strength_baseline=5)
    service = AttackService(skirmish=skirmish, warrior=warrior)

    # Patched at the boundary: the die behind "roll_attack()"
    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = service.get_attack_value()

    assert result == ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3), value=3)


@pytest.mark.django_db
def test_get_attack_value_for_a_warrior_below_his_baseline():
    """
    The same strength and the same roll against a higher baseline is a weaker blow: strength is a
    comparison against his own kind, not a number with a meaning of its own. The die is kept as it
    fell either way, so the blend stays readable as its parts.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=5, strength_baseline=10)
    service = AttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = service.get_attack_value()

    assert result == ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3), value=2)


@pytest.mark.django_db
def test_get_defense_value_announces_the_roll():
    """
    Defence is the armour's own roll and nothing else - no strength, and so no baseline either.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction, strength=5, strength_baseline=10)
    service = AttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        result = service.get_defense_value()

    assert result == ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d2"), result=2), value=2)
