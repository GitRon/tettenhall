from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.services.actions.assault_fortification import AssaultFortificationService
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_get_pair_matching_points_never_makes_the_warrior_the_attacker():
    result = AssaultFortificationService.get_pair_matching_points(warrior_dexterity=7)

    assert result == 0


@pytest.mark.django_db
def test_get_attack_value_throws_nothing_at_a_man():
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    result = AssaultFortificationService(skirmish=skirmish, warrior=warrior).get_attack_value()

    assert result == ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)


@pytest.mark.django_db
def test_get_assault_value_is_the_weapon_scaled_by_strength():
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=20, strength_baseline=10)

    # Patched at the boundary: the die behind "roll_attack()"
    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = AssaultFortificationService(skirmish=skirmish, warrior=warrior).get_assault_value()

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        value=6,
    )
