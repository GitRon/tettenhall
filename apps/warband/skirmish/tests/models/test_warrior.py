from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.nickname import (
    HEALTH_NICKNAMES,
    MORALE_NICKNAMES,
    STATS_FLOOR_NICKNAMES,
    STRENGTH_NICKNAMES,
)


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

    assert warrior.nickname == STRENGTH_NICKNAMES[0]


def test_nickname_reads_health_off_its_own_baseline_and_spread():
    """
    Six baseline and spread columns feed one rule, and a pairing that reaches for the wrong two is
    invisible from the attributes alone - so each of the three distributions gets a test that only
    passes while its own pair is the one being read. Forty against a mean of twenty and a spread of
    ten is two spreads out; read against any other pair on the row it is four, or nothing.
    """
    warrior = WarriorFactory.build(max_health=40, health_baseline=20, health_spread=10)

    assert warrior.nickname == HEALTH_NICKNAMES[0]


def test_nickname_reads_morale_off_its_own_baseline_and_spread():
    warrior = WarriorFactory.build(max_morale=30, morale_baseline=20, morale_spread=5)

    assert warrior.nickname == MORALE_NICKNAMES[0]


def test_nickname_hands_the_stats_floor_to_both_arm_draws():
    """
    The floor is a column of its own and only strength and dexterity pass it - health and morale take
    the default of one. Three is the floor here, so a man on it in both arms earns the epithet; were
    the column not reaching the draws, three would sit above a floor of one and he would earn nothing.
    """
    warrior = WarriorFactory.build(strength=3, dexterity=3, stats_minimum=3)

    assert warrior.nickname == STATS_FLOOR_NICKNAMES[0]


def test_display_name_carries_the_epithet():
    warrior = WarriorFactory.build(name="Collum", strength=20)

    assert warrior.display_name == f"Collum {STRENGTH_NICKNAMES[0]}"


def test_display_name_phrases_the_epithet_by_the_warriors_own_variant():
    warrior = WarriorFactory.build(name="Collum", strength=20, nickname_variant=1)

    assert warrior.display_name == f"Collum {STRENGTH_NICKNAMES[1]}"


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
