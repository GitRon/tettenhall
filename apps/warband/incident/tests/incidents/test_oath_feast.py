from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.oath_feast import OathFeast
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models.town import Town


@pytest.mark.django_db
def test_is_possible_with_a_hall_and_a_war_band():
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_SMALL)
    WarriorFactory(faction=faction)

    assert OathFeast.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_without_a_hall():
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_NONE)
    WarriorFactory(faction=faction)

    assert OathFeast.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_is_possible_without_a_war_band():
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_SMALL)

    assert OathFeast.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_who_spoke_first():
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_SMALL)
    warrior = WarriorFactory(faction=faction, name="Wighelm")

    with mock.patch("apps.warband.incident.incidents.oath_feast.random.choice", return_value=warrior):
        result = OathFeast.resolve(faction=faction)

    assert result.title == "The war band renewed its oaths at the mead-bench, and Wighelm spoke first."
    assert (result.max_morale_share, result.warrior) == (OathFeast.MAX_MORALE_SHARE, warrior)
