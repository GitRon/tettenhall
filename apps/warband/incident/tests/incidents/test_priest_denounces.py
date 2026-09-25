from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.priest_denounces import PriestDenounces
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_a_man_to_name():
    faction = FactionFactory()
    WarriorFactory(faction=faction)

    assert PriestDenounces.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_without_a_war_band():
    faction = FactionFactory()

    assert PriestDenounces.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_from_the_steps():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, name="Wighelm")

    with mock.patch("apps.warband.incident.incidents.priest_denounces.random.choice", return_value=warrior):
        result = PriestDenounces.resolve(faction=faction)

    assert result.title == "A priest denounced the war band from the church steps, and named Wighelm."
    assert (result.max_morale_share, result.warrior) == (PriestDenounces.MAX_MORALE_SHARE, warrior)
