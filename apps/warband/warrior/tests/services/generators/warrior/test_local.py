import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.warrior.services.generators.warrior.local import LocalWarriorGenerator


@pytest.mark.django_db
def test_process_raises_a_man_of_the_place_who_draws_no_wage():
    faction = FactionFactory()

    warrior = LocalWarriorGenerator(culture=faction.culture, faction=faction, savegame_id=faction.savegame_id).process()

    assert (warrior.faction, warrior.monthly_salary) == (faction, 0)
