from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.templatetags.handout import gear_gain


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
