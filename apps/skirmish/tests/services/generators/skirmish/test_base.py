import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.services.generators.skirmish.base import BaseSkirmishGenerator
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_process_sets_up_both_sides():
    player_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=player_faction.savegame)
    player_warrior = WarriorFactory(faction=player_faction)
    enemy_warrior = WarriorFactory(faction=enemy_faction)

    result = BaseSkirmishGenerator(
        name="Attack on Wessex",
        warriors_faction_1=[player_warrior],
        warriors_faction_2=[enemy_warrior],
        month=7,
    ).process()

    assert result.month == 7
    assert list(result.player_warriors.all()) == [player_warrior]


@pytest.mark.django_db
def test_process_without_an_attacking_side():
    enemy_faction = FactionFactory()

    generator = BaseSkirmishGenerator(
        name="Attack on Wessex",
        warriors_faction_1=[],
        warriors_faction_2=[WarriorFactory(faction=enemy_faction)],
        month=7,
    )

    with pytest.raises(RuntimeError, match="no warriors on the attacking side"):
        generator.process()


@pytest.mark.django_db
def test_process_without_a_defending_side():
    """
    Says which side is missing instead of dying on the IndexError three lines further down.
    """
    player_faction = FactionFactory()

    generator = BaseSkirmishGenerator(
        name="Attack on Wessex",
        warriors_faction_1=[WarriorFactory(faction=player_faction)],
        warriors_faction_2=[],
        month=7,
    )

    with pytest.raises(RuntimeError, match="no warriors on the defending side"):
        generator.process()
