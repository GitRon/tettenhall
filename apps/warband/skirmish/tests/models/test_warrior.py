from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.domain.attribute_draw import AttributeDraw
from apps.warband.warrior.services.nickname import MORALE_FAR_NICKNAMES, STRENGTH_NICKNAMES


def test_str_leaves_the_epithet_off():
    """
    Every generated string the game persists flows through "__str__" - the battle history, the
    monthly log, the reasons on transactions - and a man who earns his epithet in month twenty would
    otherwise be carrying it in rows written in month three.
    """
    warrior = WarriorFactory.build(name="Collum", nickname_state=NicknameStateChoices.STRENGTH)

    assert str(warrior) == "Collum"


def test_attribute_draws_pairs_each_attribute_with_its_own_distribution():
    """
    Six baseline and spread columns feed one rule, and a pairing that reaches for the wrong two is
    invisible from the attributes alone. Every number here is distinct, so any draw built off the
    wrong column is a different object than the one asserted.

    The arms share the stats trio down to the floor, which is a column only they pass: health and
    morale take the default of one, their generator refusing a zero rather than flooring them.
    """
    warrior = WarriorFactory.build(
        strength=11,
        dexterity=12,
        strength_baseline=13,
        stats_spread=14,
        stats_minimum=4,
        max_health=21,
        health_baseline=22,
        health_spread=23,
        max_morale=31,
        morale_baseline=32,
        morale_spread=33,
    )

    assert warrior.attribute_draws == {
        "strength": AttributeDraw(value=11, baseline=13, spread=14, minimum=4),
        "dexterity": AttributeDraw(value=12, baseline=13, spread=14, minimum=4),
        "health": AttributeDraw(value=21, baseline=22, spread=23),
        "morale": AttributeDraw(value=31, baseline=32, spread=33),
    }


def test_nickname_reads_the_stored_state():
    warrior = WarriorFactory.build(nickname_state=NicknameStateChoices.STRENGTH)

    assert warrior.nickname == STRENGTH_NICKNAMES[0]


def test_nickname_holds_after_the_attribute_it_names_has_been_cut():
    """
    A man named for his nerve, whose nerve a prisoner's oath, a beating or a bad night at the ford has
    since taken a quarter of. The war band does not forget what he did, and the column is what makes
    that true: nothing here would survive a rule measured off the attribute.
    """
    warrior = WarriorFactory.build(
        nickname_state=NicknameStateChoices.MORALE_FAR, max_morale=1, morale_baseline=20, morale_spread=5
    )

    assert warrior.nickname == MORALE_FAR_NICKNAMES[0]


def test_nickname_for_an_ordinary_man():
    warrior = WarriorFactory.build()

    assert warrior.nickname is None


def test_display_name_carries_the_epithet():
    warrior = WarriorFactory.build(name="Collum", nickname_state=NicknameStateChoices.STRENGTH)

    assert warrior.display_name == f"Collum {STRENGTH_NICKNAMES[0]}"


def test_display_name_phrases_the_epithet_by_the_warriors_own_variant():
    warrior = WarriorFactory.build(name="Collum", nickname_state=NicknameStateChoices.STRENGTH, nickname_variant=1)

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


def test_the_two_wage_derived_prices_of_a_man_who_draws_no_wage():
    """
    A leader, and the reason his generator zeroes the wage alone. Being hired and being sent away are
    both employment, and neither is a thing that happens to him - so both come out at nothing rather
    than at a figure nobody could act on.
    """
    warrior = WarriorFactory.build(monthly_salary=0, recruitment_price=260)

    assert warrior.hiring_price == 0
    assert warrior.severance_pay == 0


def test_slavery_selling_price_survives_a_wage_of_zero():
    """
    The third derived price is read off "recruitment_price" instead, which is why the wage is the only
    column zeroed: a captured leader is worth what a captor gets for him whatever his own faction was
    paying him.
    """
    warrior = WarriorFactory.build(monthly_salary=0, recruitment_price=260)

    assert warrior.slavery_selling_price == 130


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
def test_expected_damage_scales_the_weapon_by_the_strength_behind_it():
    """
    The same axe is worth more in stronger hands, which is why the figure is quoted about the man
    and not about the item.
    """
    weapon_type = ItemTypeFactory(base_value="2d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON)
    warrior = WarriorFactory(weapon=ItemFactory(type=weapon_type), strength=15, strength_baseline=10)

    assert warrior.expected_damage == 10.5


@pytest.mark.django_db
def test_expected_damage_falls_back_to_bare_hands():
    warrior = WarriorFactory(weapon=None, strength=20, strength_baseline=10)

    assert warrior.expected_damage == 4.0


@pytest.mark.django_db
def test_expected_protection_leaves_strength_out_of_it():
    """
    Defence is the armour's own roll, so a strong man in the same mail turns aside no more than a
    weak one - the asymmetry the two figures exist to show.
    """
    armor_type = ItemTypeFactory(base_value="3d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR)
    warrior = WarriorFactory(armor=ItemFactory(type=armor_type), strength=20, strength_baseline=10)

    assert warrior.expected_protection == 7.5


@pytest.mark.django_db
def test_expected_protection_falls_back_to_no_armour():
    warrior = WarriorFactory(armor=None)

    assert warrior.expected_protection == 1.5


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
