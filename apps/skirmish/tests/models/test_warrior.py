from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.services.nickname import STRENGTH_HIGH_NICKNAME


def test_str_leaves_the_epithet_off():
    """
    Every generated string the game persists flows through "__str__" - the battle history, the
    monthly log, the reasons on transactions - and those rows outlive an epithet derived from
    attributes that move.
    """
    warrior = WarriorFactory.build(name="Collum", strength=20)

    assert str(warrior) == "Collum"


def test_nickname_reads_the_attributes_against_the_warriors_own_distribution():
    warrior = WarriorFactory.build(strength=20)

    assert warrior.nickname == STRENGTH_HIGH_NICKNAME


def test_display_name_carries_the_epithet():
    warrior = WarriorFactory.build(name="Collum", strength=20)

    assert warrior.display_name == f"Collum {STRENGTH_HIGH_NICKNAME}"


def test_display_name_for_an_ordinary_man():
    warrior = WarriorFactory.build(name="Collum")

    assert warrior.display_name == "Collum"


def test_is_dead_for_a_killed_warrior():
    warrior = WarriorFactory.build(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert warrior.is_dead is True


def test_is_unconscious_for_an_incapacitated_warrior():
    warrior = WarriorFactory.build(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    assert warrior.is_unconscious is True


def test_is_fleeing_for_a_warrior_out_of_morale():
    warrior = WarriorFactory.build(condition=Warrior.ConditionChoices.CONDITION_FLEEING)

    assert warrior.is_fleeing is True


def test_hiring_price_inverts_the_share_a_wage_is_priced_with():
    warrior = WarriorFactory.build(monthly_salary=90)

    assert warrior.hiring_price == 180


def test_hiring_price_ignores_the_price_he_was_rolled_at():
    """
    "recruitment_price" describes the levy a man was generated as, so a veteran whose levels raised
    his wage would otherwise be the cheapest strong man in the game.
    """
    warrior = WarriorFactory.build(monthly_salary=200, recruitment_price=96)

    assert warrior.hiring_price == 400


def test_severance_pay_is_a_month_of_wages():
    warrior = WarriorFactory.build(monthly_salary=120)

    assert warrior.severance_pay == 120


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
def test_roll_attack_hands_back_the_notation_and_the_gear_it_rolled():
    """
    Both halves travel with the number, because the fight is about to blend the number away: a
    recorded total alone can be measured against neither what the weapon could have done nor what
    kind of weapon it was.
    """
    weapon_type = ItemTypeFactory(base_value="2d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON)
    warrior = WarriorFactory(weapon=ItemFactory(type=weapon_type))

    with mock.patch("apps.common.domain.dice.random.randint", return_value=4):
        result = warrior.roll_attack()

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=8), item_type=weapon_type, value=8
    )


@pytest.mark.django_db
def test_roll_defense_hands_back_the_notation_and_the_gear_it_rolled():
    armor_type = ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR)
    warrior = WarriorFactory(armor=ItemFactory(type=armor_type, modifier=2))

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = warrior.roll_defense()

    assert result == ActionRoll(
        roll=DiceRoll(notation=DiceNotation(dice_string="1d4", modifier=2), result=5), item_type=armor_type, value=5
    )


@pytest.mark.django_db
def test_roll_attack_names_bare_hands_as_the_fallback_type():
    """
    A man with no weapon still swings something, and the row says which. Without the type, an unarmed
    blow is a "1d3" indistinguishable from a real 1d3 weapon.
    """
    warrior = WarriorFactory(weapon=None)

    result = warrior.roll_attack()

    assert result.item_type.is_fallback is True
