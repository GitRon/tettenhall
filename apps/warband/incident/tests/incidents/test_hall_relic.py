from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.hall_relic import HallRelic
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_a_man_to_carry_it():
    faction = FactionFactory()
    WarriorFactory(faction=faction)

    assert HallRelic.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_without_a_war_band():
    faction = FactionFactory()

    assert HallRelic.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_it_was_given_to():
    """
    Outside a skirmish nobody watches morale, so a change nobody is named for is invisible.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, name="Wighelm")

    with mock.patch("apps.warband.incident.incidents.hall_relic.random.choice", return_value=warrior):
        result = HallRelic.resolve(faction=faction)

    assert result.title == "A relic came to the hall, and Wighelm was given it to carry."
    assert result.warrior == warrior
