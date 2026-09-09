import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.fever_in_the_villages import FeverInTheVillages


@pytest.mark.django_db
def test_is_possible_with_men_in_the_reserve():
    faction = FactionFactory(fyrd_reserve=1)

    assert FeverInTheVillages.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_with_an_empty_reserve():
    faction = FactionFactory(fyrd_reserve=0)

    assert FeverInTheVillages.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_takes_what_the_entry_names():
    faction = FactionFactory(fyrd_reserve=5)

    result = FeverInTheVillages.resolve(faction=faction)

    assert result.fyrd_change == -2


@pytest.mark.django_db
def test_resolve_takes_no_more_men_than_the_reserve_holds():
    """
    The manager floors the reserve at zero either way, but a log line reporting two men gone from a
    reserve of one would be a lie the player can check.
    """
    faction = FactionFactory(fyrd_reserve=1)

    result = FeverInTheVillages.resolve(faction=faction)

    assert result.fyrd_change == -1
