from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.templatetags.handout import gear_gain, improves_nobody


def test_gear_gain_of_an_item_worth_more_than_what_it_displaces():
    warrior = Warrior()
    warrior.held_gear_values = {"weapon": 3.5}
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"))

    result = gear_gain(warrior, item)

    assert result == "+3.5"


def test_gear_gain_of_an_item_worth_less_than_what_it_displaces():
    warrior = Warrior()
    warrior.held_gear_values = {"weapon": 9}
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"))

    result = gear_gain(warrior, item)

    assert result == "-2"


def test_gear_gain_of_two_items_worth_the_same():
    warrior = Warrior()
    warrior.held_gear_values = {"weapon": 7}
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"))

    result = gear_gain(warrior, item)

    assert result == "±0"


def test_gear_gain_compares_against_the_slot_the_item_fills():
    warrior = Warrior()
    warrior.held_gear_values = {"weapon": 7, "armor": 1.5}
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_ARMOR, base_value="1d6"))

    result = gear_gain(warrior, item)

    assert result == "+2"


def _warrior_holding_a_weapon_worth(value: float) -> Warrior:
    warrior = Warrior()
    warrior.held_gear_values = {"weapon": value}
    return warrior


def test_improves_nobody_when_every_man_holds_at_least_as_good():
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"))

    result = improves_nobody(item, [_warrior_holding_a_weapon_worth(7), _warrior_holding_a_weapon_worth(9)])

    assert result is True


def test_improves_nobody_is_false_when_one_man_would_gain():
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"))

    result = improves_nobody(item, [_warrior_holding_a_weapon_worth(9), _warrior_holding_a_weapon_worth(3.5)])

    assert result is False


def test_improves_nobody_is_false_with_nobody_to_compare_against():
    item = Item(type=ItemType(function=ItemType.FunctionChoices.FUNCTION_WEAPON, base_value="2d6"))

    result = improves_nobody(item, [])

    assert result is False
