from unittest import mock

import pytest

from apps.warband.faction.models import Culture
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.warrior.services.generators.warrior.leader import LeaderWarriorGenerator


@pytest.mark.django_db
def test_process_names_the_leader_what_the_player_called_him():
    generator = LeaderWarriorGenerator(
        culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id, name="Cerdic"
    )

    result = generator.process()

    assert result.name == "Cerdic"


@pytest.mark.django_db
def test_process_draws_a_name_for_a_leader_nobody_named():
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.warrior.services.generators.warrior.base.draw_warrior_name", return_value="Wulfstan"):
        result = generator.process()

    assert result.name == "Wulfstan"
