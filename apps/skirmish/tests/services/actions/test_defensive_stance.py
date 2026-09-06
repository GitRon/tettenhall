from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.item.models.item_type import ItemType
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.services.actions.defensive_stance import DefensiveStanceService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_get_pair_matching_points_never_makes_the_warrior_the_attacker():
    result = DefensiveStanceService.get_pair_matching_points(warrior_dexterity=7)

    assert result == 0


@pytest.mark.django_db
def test_get_attack_value_never_deals_damage():
    """
    Nothing is swung, so no die is thrown - and the row says that rather than a zero, which the
    armour stopping a whole blow would also be.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    service = DefensiveStanceService(skirmish=skirmish, warrior=warrior)

    result = service.get_attack_value()

    assert result == ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)


@pytest.mark.django_db
def test_get_defense_value_doubles_the_defense():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    service = DefensiveStanceService(skirmish=skirmish, warrior=warrior)

    # Patched at the boundary: the die behind "roll_defense()"
    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        result = service.get_defense_value()

    # The die is kept as it fell, so the doubling stays visible as a doubling
    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d2"), result=2),
        item_type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_ARMOR),
        value=4,
    )
