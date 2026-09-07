"""
What every entry of the catalogue inherits, exercised through the entries that inherit it.

No test-only subclass of [Incident]: the shared behaviour is a default weight, a default
precondition and a default resolve, and each of those is worth more asserted through a real entry
than through one written to make the assert pass.
"""

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.incident.incidents.base import IncidentOutcome, losable_items, roster
from apps.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.incident.incidents.hall_roof_falls_in import HallRoofFallsIn
from apps.incident.incidents.plough_hoard import PloughHoard
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_roster_holds_the_living_men_of_the_faction():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)

    assert roster(faction=faction) == [warrior]


@pytest.mark.django_db
def test_roster_excludes_the_dead():
    """
    Dying does not clear "Warrior.faction", so without this a relic is handed to a corpse.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert roster(faction=faction) == []


@pytest.mark.django_db
def test_losable_items_excludes_the_finest_of_each_function():
    faction = FactionFactory()
    finest_weapon = ItemFactory(owner=faction, savegame=faction.savegame, price=200)
    cheap_weapon = ItemFactory(owner=faction, savegame=faction.savegame, price=30)
    WarriorFactory(faction=faction, weapon=finest_weapon)
    WarriorFactory(faction=faction, weapon=cheap_weapon)

    assert losable_items(faction=faction) == [cheap_weapon]


@pytest.mark.django_db
def test_losable_items_counts_weapons_and_armour_separately():
    """
    One of each in the field means both are the finest of their function, so neither is losable.
    """
    faction = FactionFactory()
    weapon = ItemFactory(owner=faction, savegame=faction.savegame)
    armor = ItemFactory(
        owner=faction,
        savegame=faction.savegame,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )
    WarriorFactory(faction=faction, weapon=weapon, armor=armor)

    assert losable_items(faction=faction) == []


@pytest.mark.django_db
def test_losable_items_ignores_gear_nobody_carries():
    """
    An item no warrior wears is in a chest at home, not out on a moor.
    """
    faction = FactionFactory()
    worn_weapon = ItemFactory(owner=faction, savegame=faction.savegame, price=200)
    ItemFactory(owner=faction, savegame=faction.savegame, price=30)
    WarriorFactory(faction=faction, weapon=worn_weapon)

    assert losable_items(faction=faction) == []


@pytest.mark.django_db
def test_is_possible_for_an_entry_with_nothing_to_take():
    faction = FactionFactory()

    assert PloughHoard.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_for_a_cost_the_treasury_covers():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-HallRoofFallsIn.SILVER_CHANGE)

    assert HallRoofFallsIn.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_for_a_cost_the_treasury_does_not_cover():
    """
    An incident must not open a hole the player did not dig, so a cost he cannot pay does not happen
    to him at all.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-HallRoofFallsIn.SILVER_CHANGE - 1)

    assert HallRoofFallsIn.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_turns_the_constants_into_an_outcome():
    """
    An entry whose outcome depends on nothing needs no code of its own, which is what keeps adding
    one to a single class.
    """
    faction = FactionFactory()

    result = BurntVillageRefugees.resolve(faction=faction)

    assert result == IncidentOutcome(
        title=BurntVillageRefugees.TITLE,
        body=BurntVillageRefugees.BODY,
        silver_change=BurntVillageRefugees.SILVER_CHANGE,
        fyrd_change=BurntVillageRefugees.FYRD_CHANGE,
    )
