import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.models import SkirmishBlow
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_blow import SkirmishBlowFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


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
    weapon_type = ItemTypeFactory(base_value="2d6")
    armor_type = ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR)

    blow = SkirmishBlow.objects.create_record(
        skirmish=skirmish,
        round_number=2,
        attacker=WarriorFactory(faction=skirmish.attacking_faction),
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=WarriorFactory(faction=skirmish.defending_faction),
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        outcome=BlowOutcomeChoices.OUTCOME_HIT,
        attack=ActionRoll(
            roll=DiceRoll(notation=DiceNotation(dice_string="2d6", modifier=1), result=9),
            item_type=weapon_type,
            value=9,
        ),
        defense=ActionRoll(
            roll=DiceRoll(notation=DiceNotation(dice_string="1d4", modifier=-1), result=2),
            item_type=armor_type,
            value=2,
        ),
        damage=7,
    )

    assert (blow.attack_dice, blow.attack_modifier, blow.attack_roll, blow.attack_value) == ("2d6", 1, 9, 9)
    assert (blow.attack_item_type, blow.defense_item_type) == (weapon_type, armor_type)


@pytest.mark.django_db
def test_create_record_leaves_the_attack_columns_empty_when_no_die_was_thrown():
    skirmish = SkirmishFactory()
    armor_type = ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR)

    blow = SkirmishBlow.objects.create_record(
        skirmish=skirmish,
        round_number=1,
        attacker=WarriorFactory(faction=skirmish.attacking_faction),
        attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        defender=WarriorFactory(faction=skirmish.defending_faction),
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
        attack=ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN),
        defense=ActionRoll(
            roll=DiceRoll(notation=DiceNotation(dice_string="1d4", modifier=0), result=3),
            item_type=armor_type,
            value=3,
        ),
    )

    # No die and no weapon: nothing was swung, so the row claims nothing about one
    assert (blow.attack_item_type, blow.attack_dice, blow.attack_roll, blow.attack_value) == (None, "", None, 0)
    assert blow.defense_item_type == armor_type
