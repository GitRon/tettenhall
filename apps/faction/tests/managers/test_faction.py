import pytest

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_add_captive_arrests_the_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(savegame=faction.savegame)

    Faction.objects.add_captive(faction=faction, warrior=warrior)

    assert list(faction.captured_warriors.all()) == [warrior]


@pytest.mark.django_db
def test_rivals_of_leaves_out_the_player_faction():
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    rival_faction = FactionFactory(savegame=savegame)

    result = Faction.objects.rivals_of(savegame_id=savegame.id, player_faction_id=player_faction.id)

    assert list(result) == [rival_faction]


@pytest.mark.django_db
def test_rivals_of_without_a_player_faction():
    """
    A savegame gets its row before its factions exist, so there is nobody to leave out yet.
    """
    savegame = SavegameFactory()
    faction = FactionFactory(savegame=savegame)

    result = Faction.objects.rivals_of(savegame_id=savegame.id, player_faction_id=None)

    assert list(result) == [faction]


@pytest.mark.django_db
def test_remove_captive_releases_the_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(savegame=faction.savegame)
    faction.captured_warriors.add(warrior)

    Faction.objects.remove_captive(faction=faction, warrior=warrior)

    assert list(faction.captured_warriors.all()) == []
