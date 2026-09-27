import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.thegn_buys_out_his_sons import ThegnBuysOutHisSons


@pytest.mark.django_db
def test_is_possible_with_a_name_on_the_fyrd_roll():
    faction = FactionFactory(fyrd_reserve=1)

    assert ThegnBuysOutHisSons.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_with_an_empty_reserve():
    """
    Silver for men the fyrd has not got would be silver for nothing.
    """
    faction = FactionFactory(fyrd_reserve=0)

    assert ThegnBuysOutHisSons.is_possible(faction=faction) is False
