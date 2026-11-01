from unittest import mock

import pytest

from apps.warband.faction.models import Culture
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
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


def test_generator_seats_every_leader_at_level_two():
    """
    A leader takes his seat a seasoned man, the way #10 set the professionals. His experience is rolled
    as a normal draw, so "every" means everything within four spreads of the mean - all but about one
    draw in sixteen thousand - and both ends of that band have to buy level 2. A mean on the threshold
    itself put half of all leaders a point short of it (#493).
    """
    lowest = round(LeaderWarriorGenerator.XP_MU - 4 * LeaderWarriorGenerator.XP_SIGMA)
    highest = round(LeaderWarriorGenerator.XP_MU + 4 * LeaderWarriorGenerator.XP_SIGMA)

    assert Warrior.level_for(experience=lowest) == 2
    assert Warrior.level_for(experience=highest) == 2
