from unittest import mock

import pytest

from apps.faction.models import Culture
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator
from apps.warrior.services.generators.warrior.leader import LeaderWarriorGenerator


@pytest.mark.django_db
def test_process_leaves_a_warrior_whose_experience_is_an_integer():
    """
    Every roll is rounded, so the instance handed back holds the same integer the row does even
    though Django does not re-read after a create. "isqrt" refuses a float, and this is every warrior
    in the pub and every leader on the turn a savegame is created.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert isinstance(result.experience, int)
    assert result.level == Warrior.objects.get(pk=result.pk).level


@pytest.mark.django_db
def test_process_rounds_a_sub_one_health_roll_up_to_a_point():
    """
    The band between zero and one is the one a truncating column turns into a warrior with no health
    at all, so it is patched rather than waited for.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.max_health == 1
    assert Warrior.objects.get(pk=result.pk).max_health == 1


@pytest.mark.django_db
def test_process_rounds_a_sub_one_morale_roll_up_to_a_point():
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.max_morale == 1
    assert Warrior.objects.get(pk=result.pk).max_morale == 1


@pytest.mark.django_db
def test_process_rerolls_a_roll_that_rounds_to_zero():
    """
    Every roll comes up at minus five first, which the floor and the rounding turn into the zero the
    guards refuse, and then at twelve. A "return_value" the guards reject would spin for ever, so the
    second value is what proves the retry fires and the loops terminate.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warrior.services.generators.warrior.base.random.gauss", side_effect=[-5, 12] * 10):
        result = generator.process()

    assert result.max_health == 12
    assert result.max_morale == 12


@pytest.mark.django_db
def test_process_keeps_a_progress_roll_at_its_ceiling():
    """
    A roll just above a hundred rounds down onto the ceiling rather than over it, so the guard takes
    it instead of asking for another one.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warrior.services.generators.warrior.base.random.gauss", return_value=100.4):
        result = generator.process()

    assert result.health_progress == 100
    assert result.morale_progress == 100


@pytest.mark.django_db
def test_process_floors_the_stats_at_the_generator_minimum():
    """
    A leader sits at STATS_MIN = 4, so a roll that rounds to one is lifted to the minimum instead of
    being re-rolled - which is why the two stats need no guard.
    """
    generator = LeaderWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warrior.services.generators.warrior.base.random.gauss", return_value=0.6):
        result = generator.process()

    assert result.strength == 4
    assert result.dexterity == 4


@pytest.mark.django_db
def test_process_equips_the_warrior_when_both_rolls_come_up():
    """
    Whether a warrior gets a weapon and an armour is a dice roll, so the roll is patched at the
    boundary instead of leaving these two branches to chance.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    # Below both chances, so both items are generated
    with mock.patch("apps.warrior.services.generators.warrior.base.random.uniform", return_value=0):
        result = generator.process()

    assert result.weapon is not None
    assert result.armor is not None


@pytest.mark.django_db
def test_process_leaves_the_warrior_bare_when_both_rolls_fail():
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    # Above both chances, so neither item is generated
    with mock.patch("apps.warrior.services.generators.warrior.base.random.uniform", return_value=1):
        result = generator.process()

    assert result.weapon is None
    assert result.armor is None
