import pytest

from apps.warband.skirmish.choices.posting import PostingChoices
from apps.warband.skirmish.raids.kinds import LiftTheHerds, StormTheBurh
from apps.warband.skirmish.services.raid_defenders import get_raid_defenders
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_get_raid_defenders_meets_every_man_at_the_burh_wherever_he_is_posted():
    muster = [
        WarriorFactory(posting=PostingChoices.HERDS),
        WarriorFactory(posting=PostingChoices.VILLAGE),
        WarriorFactory(posting=PostingChoices.BURH),
    ]

    assert get_raid_defenders(raid_kind=StormTheBurh, muster=muster) == muster


def test_get_raid_defenders_finds_nobody_in_an_empty_muster():
    assert get_raid_defenders(raid_kind=LiftTheHerds, muster=[]) == []


@pytest.mark.django_db
def test_get_raid_defenders_meets_only_the_men_posted_at_the_herds_in_id_order():
    first = WarriorFactory(posting=PostingChoices.HERDS)
    second = WarriorFactory(posting=PostingChoices.BURH)
    third = WarriorFactory(posting=PostingChoices.HERDS)

    assert get_raid_defenders(raid_kind=LiftTheHerds, muster=[third, first, second]) == [first, third]


@pytest.mark.django_db
def test_get_raid_defenders_leaves_a_place_to_its_own_people_when_no_man_of_the_band_stands_there():
    """The herdsmen turn out whoever of the war band is elsewhere, so nobody is moved to the herds."""
    lone_man = WarriorFactory(posting=PostingChoices.VILLAGE)

    assert get_raid_defenders(raid_kind=LiftTheHerds, muster=[lone_man]) == []


class UnpeopledPlace(LiftTheHerds):
    """A place nobody of its own turns out for, which no kind the game ships is."""

    LOCALS_TURNOUT = 0


@pytest.mark.django_db
def test_get_raid_defenders_puts_the_first_man_where_nobody_of_the_place_turns_out():
    """Nobody is posted there, and the first man of the muster stands there all the same, so the side is never empty."""
    second = WarriorFactory(posting=PostingChoices.BURH)
    first = WarriorFactory(posting=PostingChoices.VILLAGE)
    first_by_id, second_by_id = sorted([first, second], key=lambda warrior: warrior.id)

    assert get_raid_defenders(raid_kind=UnpeopledPlace, muster=[second_by_id, first_by_id]) == [first_by_id]
