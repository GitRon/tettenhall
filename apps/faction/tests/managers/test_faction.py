import pytest

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_add_captive_arrests_the_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(savegame=faction.savegame)

    Faction.objects.add_captive(faction=faction, warrior=warrior)

    assert list(faction.captured_warriors.all()) == [warrior]


@pytest.mark.django_db
def test_remove_captive_releases_the_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(savegame=faction.savegame)
    faction.captured_warriors.add(warrior)

    Faction.objects.remove_captive(faction=faction, warrior=warrior)

    assert list(faction.captured_warriors.all()) == []
