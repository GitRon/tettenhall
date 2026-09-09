from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_get_attack_value_doubles_the_damage_on_a_hit():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10)
    service = RiskyAttackService(skirmish=skirmish, warrior=warrior)

    # Patched at the boundary: the coin flip deciding hit or miss, and the die behind "roll_attack()"
    with (
        mock.patch("apps.warband.skirmish.services.actions.risky_attack.random.getrandbits", return_value=1),
        mock.patch("apps.common.domain.dice.random.randint", return_value=3),
    ):
        result = service.get_attack_value()

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        value=6,
    )


@pytest.mark.django_db
def test_get_attack_value_deals_nothing_on_a_miss():
    """
    A swing that went wide throws no die at all, and says so rather than handing back a bare zero -
    the armour taking a whole blow is the same zero and a different thing.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10)
    service = RiskyAttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.warband.skirmish.services.actions.risky_attack.random.getrandbits", return_value=0):
        result = service.get_attack_value()

    assert result == ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_MISSED)


@pytest.mark.django_db
def test_get_attack_value_doubles_a_blow_measured_against_a_lower_baseline():
    """
    The doubling sits on top of the strength comparison, the same way the fast attack's halving does.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10, strength_baseline=5)
    service = RiskyAttackService(skirmish=skirmish, warrior=warrior)

    with (
        mock.patch("apps.warband.skirmish.services.actions.risky_attack.random.getrandbits", return_value=1),
        mock.patch("apps.common.domain.dice.random.randint", return_value=3),
    ):
        result = service.get_attack_value()

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d3"), result=3),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        value=12,
    )
