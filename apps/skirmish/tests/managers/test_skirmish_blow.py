import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.models import SkirmishBlow
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.skirmish_blow import SkirmishBlowFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_for_savegame_reaches_the_savegame_through_the_attacking_faction():
    blow = SkirmishBlowFactory()
    SkirmishBlowFactory()

    result = SkirmishBlow.objects.for_savegame(savegame_id=blow.skirmish.attacking_faction.savegame_id)

    assert list(result) == [blow]


@pytest.mark.django_db
def test_for_warrior_finds_him_at_either_end_of_the_blow():
    """
    Both halves of an exchange sit on one row, so a man's record is a query over two columns rather
    than a reverse relation over one.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    dealt = SkirmishBlowFactory(skirmish=skirmish, attacker=warrior)
    taken = SkirmishBlowFactory(skirmish=skirmish, defender=warrior)
    SkirmishBlowFactory(skirmish=skirmish)

    result = SkirmishBlow.objects.for_warrior(warrior_id=warrior.id)

    assert list(result) == [dealt, taken]


@pytest.mark.django_db
def test_create_record_unpacks_both_rolls_into_columns():
    skirmish = SkirmishFactory()

    blow = SkirmishBlow.objects.create_record(
        skirmish=skirmish,
        round_number=2,
        attacker=WarriorFactory(faction=skirmish.attacking_faction),
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=WarriorFactory(faction=skirmish.defending_faction),
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        outcome=BlowOutcomeChoices.OUTCOME_HIT,
        attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6", modifier=1), result=9), value=9),
        defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4", modifier=-1), result=2), value=2),
        damage=7,
    )

    assert (blow.attack_dice, blow.attack_modifier, blow.attack_roll, blow.attack_value) == ("2d6", 1, 9, 9)
    assert (blow.defense_dice, blow.defense_modifier, blow.defense_roll, blow.defense_value) == ("1d4", -1, 2, 2)


@pytest.mark.django_db
def test_create_record_leaves_the_attack_columns_empty_when_no_die_was_thrown():
    skirmish = SkirmishFactory()

    blow = SkirmishBlow.objects.create_record(
        skirmish=skirmish,
        round_number=1,
        attacker=WarriorFactory(faction=skirmish.attacking_faction),
        attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        defender=WarriorFactory(faction=skirmish.defending_faction),
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
        attack=ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN),
        defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4", modifier=0), result=3), value=3),
    )

    assert (blow.attack_dice, blow.attack_modifier, blow.attack_roll, blow.attack_value) == ("", None, None, 0)
    assert blow.damage == 0
