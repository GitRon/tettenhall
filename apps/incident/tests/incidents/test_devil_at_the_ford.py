from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.incident.incidents.devil_at_the_ford import DevilAtTheFord
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_a_man_to_frighten():
    faction = FactionFactory()
    WarriorFactory(faction=faction)

    assert DevilAtTheFord.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_without_a_war_band():
    faction = FactionFactory()

    assert DevilAtTheFord.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_who_saw_it():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, name="Wighelm")

    with mock.patch("apps.incident.incidents.devil_at_the_ford.random.choice", return_value=warrior):
        result = DevilAtTheFord.resolve(faction=faction)

    assert result.title == "Wighelm swears he saw the Devil at the ford."
    assert result.max_morale_share == DevilAtTheFord.MAX_MORALE_SHARE
