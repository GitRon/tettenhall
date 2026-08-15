from unittest import mock

import pytest

from apps.faction.models import Culture
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator


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


@pytest.mark.django_db
def test_process_leaves_a_warrior_whose_level_can_be_read():
    """
    The generated experience is a float and Django does not re-read after a create, so the instance
    handed back here keeps it while the database holds an integer. "isqrt" refuses a float, and this
    is every warrior in the pub and every leader on the turn a savegame is created - so the level is
    asked of a generated warrior here rather than only of a factory-built one.
    """
    generator = FyrdWarriorGenerator(culture=Culture.objects.first(), faction=None, savegame_id=SavegameFactory().id)

    result = generator.process()

    assert isinstance(result.experience, float)
    assert result.level == Warrior.objects.get(pk=result.pk).level
