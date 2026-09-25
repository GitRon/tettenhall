from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.incidents.tribute_to_a_rival import TributeToARival


@pytest.mark.django_db
def test_is_possible_with_a_rival_on_the_board_and_the_silver_to_pay():
    faction = FactionFactory()
    FactionFactory(savegame=faction.savegame)
    TransactionFactory(faction=faction, amount=-TributeToARival.SILVER_CHANGE)

    assert TributeToARival.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_once_every_rival_is_knocked_out():
    """
    A defeated rival has no army left to ask with.
    """
    faction = FactionFactory()
    FactionFactory(savegame=faction.savegame, is_defeated=True)
    TransactionFactory(faction=faction, amount=-TributeToARival.SILVER_CHANGE)

    assert TributeToARival.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_is_possible_without_the_silver_to_pay():
    faction = FactionFactory()
    FactionFactory(savegame=faction.savegame)

    assert TributeToARival.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_rival_who_asked():
    faction = FactionFactory()
    rival = FactionFactory(savegame=faction.savegame, name="Hwicce")

    with mock.patch("apps.warband.incident.incidents.tribute_to_a_rival.random.choice", return_value=rival):
        result = TributeToARival.resolve(faction=faction)

    assert result.title == "Tribute went to Hwicce, who asked for it with an army behind the asking."
    assert result.silver_change == TributeToARival.SILVER_CHANGE
