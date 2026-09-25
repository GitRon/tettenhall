from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.child_with_his_face import ChildWithHisFace
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_a_man_to_talk_about():
    faction = FactionFactory()
    WarriorFactory(faction=faction)

    assert ChildWithHisFace.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_without_a_war_band():
    faction = FactionFactory()

    assert ChildWithHisFace.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_names_the_man_whose_face_it_is():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, name="Wighelm")

    with mock.patch("apps.warband.incident.incidents.child_with_his_face.random.choice", return_value=warrior):
        result = ChildWithHisFace.resolve(faction=faction)

    assert result.title == "A child in the village has Wighelm's face, and another man's name."
    assert (result.max_morale_share, result.warrior) == (ChildWithHisFace.MAX_MORALE_SHARE, warrior)
