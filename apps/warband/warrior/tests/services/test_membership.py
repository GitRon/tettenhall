import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.membership import is_on_roster, was_sold_from_cells


@pytest.mark.django_db
def test_is_on_roster_for_one_of_his_men():
    faction = FactionFactory()

    assert is_on_roster(warrior=WarriorFactory(faction=faction), faction=faction) is True


@pytest.mark.django_db
def test_is_on_roster_for_another_factions_man():
    faction = FactionFactory()

    assert is_on_roster(warrior=WarriorFactory(faction=FactionFactory()), faction=faction) is False


@pytest.mark.django_db
def test_was_sold_from_cells_for_a_man_gone_from_them_to_nobody():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)

    assert was_sold_from_cells(warrior=warrior, faction=faction) is True


@pytest.mark.django_db
def test_was_sold_from_cells_for_a_man_still_in_them():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.captured_warriors.add(warrior)

    assert was_sold_from_cells(warrior=warrior, faction=faction) is False


@pytest.mark.django_db
def test_was_sold_from_cells_for_a_man_recruited_instead():
    faction = FactionFactory()

    assert was_sold_from_cells(warrior=WarriorFactory(faction=faction), faction=faction) is False
