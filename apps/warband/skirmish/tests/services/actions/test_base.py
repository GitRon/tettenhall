from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.services.actions.base import AttackService
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.injury_type import InjuryType
from apps.warband.warrior.tests.factories.injury import InjuryFactory
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


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

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        value=3,
    )


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

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        value=2,
    )


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

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d2"), result=2),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_ARMOR),
        value=2,
    )


@pytest.mark.django_db
def test_get_attack_value_is_weakened_by_a_lasting_injury():
    """
    The one method the three attack services all reach, so a ruined shoulder is felt in every swing
    the fight has - see docs/patterns/attribute-modifiers.md.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10, strength_baseline=10)
    InjuryFactory(
        warrior=warrior,
        type=InjuryTypeFactory(attribute=InjuryType.AttributeChoices.ATTRIBUTE_STRENGTH, magnitude=5),
    )
    service = AttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = service.get_attack_value()

    assert result.value == 2


@pytest.mark.django_db
def test_get_defense_value_behind_the_wall():
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(warrior)
    service = AttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        result = service.get_defense_value()

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d2"), result=2),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_ARMOR),
        value=3,
    )


@pytest.mark.django_db
def test_get_defense_value_of_an_attacker_has_no_wall_at_his_back():
    """
    The defender of an exchange is only whoever lost the initiative roll. An attacker is that in half
    his exchanges, and the wall still belongs to the other side.
    """
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)
    service = AttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        result = service.get_defense_value()

    assert result.value == 2
