from unittest import mock

import pytest

from apps.warband.skirmish.raids.kinds import BurnTheVillage, LiftTheHerds, StormTheBurh
from apps.warband.skirmish.services.raid_defenders import get_raid_defenders
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_get_raid_defenders_meets_every_man_at_the_burh():
    muster = WarriorFactory.create_batch(3)

    assert get_raid_defenders(raid_kind=StormTheBurh, muster=muster) == muster


def test_get_raid_defenders_finds_nobody_in_an_empty_muster():
    assert get_raid_defenders(raid_kind=LiftTheHerds, muster=[]) == []


@pytest.mark.django_db
def test_get_raid_defenders_meets_only_the_men_drawn_to_the_herds():
    """The places are drawn over the muster in id order, whatever order it arrived in."""
    first, second, third = WarriorFactory.create_batch(3)

    with mock.patch(
        "apps.warband.skirmish.services.raid_defenders.random.choice",
        side_effect=[LiftTheHerds, StormTheBurh, LiftTheHerds],
    ):
        defenders = get_raid_defenders(raid_kind=LiftTheHerds, muster=[third, first, second])

    assert defenders == [first, third]


@pytest.mark.django_db
def test_get_raid_defenders_leaves_a_place_to_its_own_people_when_no_man_of_the_band_stands_there():
    """The herdsmen turn out whoever of the war band is elsewhere, so nobody is moved to the herds."""
    lone_man = WarriorFactory()

    with mock.patch("apps.warband.skirmish.services.raid_defenders.random.choice", side_effect=[BurnTheVillage]):
        defenders = get_raid_defenders(raid_kind=LiftTheHerds, muster=[lone_man])

    assert defenders == []


class UnpeopledPlace(LiftTheHerds):
    """A place nobody of its own turns out for, which no kind the game ships is."""

    LOCALS_TURNOUT = 0


@pytest.mark.django_db
def test_get_raid_defenders_posts_one_man_where_nobody_of_the_place_turns_out():
    """The one man is drawn elsewhere, and is put there all the same, so the side is never empty."""
    lone_man = WarriorFactory()

    with mock.patch(
        "apps.warband.skirmish.services.raid_defenders.random.choice", side_effect=[BurnTheVillage, lone_man]
    ):
        defenders = get_raid_defenders(raid_kind=UnpeopledPlace, muster=[lone_man])

    assert defenders == [lone_man]
