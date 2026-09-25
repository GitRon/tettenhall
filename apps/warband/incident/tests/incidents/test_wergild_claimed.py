from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.incidents.wergild_claimed import WergildClaimed
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_a_man_to_claim_against_and_the_silver_to_pay():
    faction = FactionFactory()
    WarriorFactory(faction=faction)
    TransactionFactory(faction=faction, amount=-WergildClaimed.SILVER_CHANGE)

    assert WergildClaimed.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_without_a_war_band():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-WergildClaimed.SILVER_CHANGE)

    assert WergildClaimed.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_is_possible_without_the_silver_to_pay():
    faction = FactionFactory()
    WarriorFactory(faction=faction)

    assert WergildClaimed.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_and_charges_the_treasury():
    """
    The man is named in the title only: "warrior" on the outcome belongs to the morale lever, and
    this entry does not pull it.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, name="Wighelm")

    with mock.patch("apps.warband.incident.incidents.wergild_claimed.random.choice", return_value=warrior):
        result = WergildClaimed.resolve(faction=faction)

    assert result.title == "Kin from across the river claimed wergild against Wighelm."
    assert (result.silver_change, result.warrior) == (WergildClaimed.SILVER_CHANGE, None)
