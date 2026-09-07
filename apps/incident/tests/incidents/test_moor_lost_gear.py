from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.incident.incidents.moor_lost_gear import MoorLostGear
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_a_second_blade_in_the_field():
    faction = FactionFactory()
    WarriorFactory(faction=faction, weapon=ItemFactory(owner=faction, savegame=faction.savegame, price=200))
    WarriorFactory(faction=faction, weapon=ItemFactory(owner=faction, savegame=faction.savegame, price=30))

    assert MoorLostGear.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_with_only_the_finest_in_the_field():
    """
    A war band carrying one weapon carries its best one, and the best one never goes missing.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, weapon=ItemFactory(owner=faction, savegame=faction.savegame))

    assert MoorLostGear.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_and_what_he_lost():
    faction = FactionFactory()
    spear = ItemFactory(owner=faction, savegame=faction.savegame, price=30, type=ItemTypeFactory(name="Spear"))
    WarriorFactory(faction=faction, weapon=ItemFactory(owner=faction, savegame=faction.savegame, price=200))
    WarriorFactory(faction=faction, weapon=spear, name="Wighelm")

    with mock.patch("apps.incident.incidents.moor_lost_gear.random.choice", return_value=spear):
        result = MoorLostGear.resolve(faction=faction)

    assert result.title == "Wighelm has lost his spear in the moor."
    assert result.lost_item == spear
