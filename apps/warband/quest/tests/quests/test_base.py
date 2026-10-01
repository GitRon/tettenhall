"""
The base behaviour, through real entries of the catalogue rather than a test subclass.
"""

from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_possible_with_the_men_it_takes():
    faction = FactionFactory()
    WarriorFactory.create_batch(DriveOffWolves.MIN_MEN, faction=faction)

    assert DriveOffWolves.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_counts_the_leader_before_his_row_is_written():
    faction = FactionFactory()

    assert HarvestHands.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_short_of_men():
    """The dead are still on the roster and are not counted."""
    faction = FactionFactory()
    WarriorFactory(faction=faction)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert DriveOffWolves.is_possible(faction=faction) is False


def test_get_success_factor_at_the_yardstick():
    warriors = WarriorFactory.build_batch(2, strength=HarvestHands.STAT_YARDSTICK // 2)

    assert HarvestHands.get_success_factor(warriors=warriors) == 1.0


def test_get_success_factor_is_capped():
    warriors = WarriorFactory.build_batch(4, strength=HarvestHands.STAT_YARDSTICK)

    assert HarvestHands.get_success_factor(warriors=warriors) == HarvestHands.MAX_SUCCESS_FACTOR


def test_get_outcome_weights_moves_only_the_successes():
    warriors = WarriorFactory.build_batch(4, strength=HarvestHands.STAT_YARDSTICK // 2)

    # Twice the yardstick: the reaping is twice as likely, the rain exactly as likely as written
    assert HarvestHands.get_outcome_weights(warriors=warriors) == [6.0, 1]


def test_draw_outcome_draws_off_the_weights():
    warriors = WarriorFactory.build_batch(2, strength=HarvestHands.STAT_YARDSTICK // 2)

    with mock.patch("apps.warband.quest.quests.base.random.choices", return_value=[HarvestHands.OUTCOMES[1]]) as draw:
        result = HarvestHands.draw_outcome(warriors=warriors)

    assert result == HarvestHands.OUTCOMES[1]
    assert draw.call_args.kwargs["weights"] == [3.0, 1]
