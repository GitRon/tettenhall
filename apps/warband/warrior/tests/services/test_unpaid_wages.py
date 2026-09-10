import pytest

from apps.warband.faction.tests.factories.culture import CultureFactory
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.unpaid_wages import LEADER_NOTE, get_unpaid_wages_note


@pytest.mark.django_db
def test_get_unpaid_wages_note_says_nothing_about_a_man_who_is_paid():
    warrior = WarriorFactory(faction=FactionFactory(), unpaid_months=0)

    result = get_unpaid_wages_note(warrior=warrior, leader_id=None)

    assert result is None


@pytest.mark.django_db
def test_get_unpaid_wages_note_says_nothing_about_a_man_no_faction_owes():
    """
    Capture clears the faction and leaves the count where it stood, and a mercenary waiting in the
    pub carries whatever he left a roster with. Neither is owed wages by anybody.
    """
    warrior = WarriorFactory(faction=None, savegame=SavegameFactory(), culture=CultureFactory(), unpaid_months=2)

    result = get_unpaid_wages_note(warrior=warrior, leader_id=None)

    assert result is None


@pytest.mark.django_db
def test_get_unpaid_wages_note_counts_the_first_month():
    warrior = WarriorFactory(faction=FactionFactory(), unpaid_months=1)

    result = get_unpaid_wages_note(warrior=warrior, leader_id=None)

    assert result == "1 of 3 unpaid months"


@pytest.mark.django_db
def test_get_unpaid_wages_note_counts_the_last_month_before_he_walks():
    warrior = WarriorFactory(faction=FactionFactory(), unpaid_months=Warrior.UNPAID_MONTHS_UNTIL_WALKOUT - 1)

    result = get_unpaid_wages_note(warrior=warrior, leader_id=None)

    assert result == "2 of 3 unpaid months"


@pytest.mark.django_db
def test_get_unpaid_wages_note_gives_the_leader_no_deadline():
    """
    He sulks indefinitely rather than walking, so a number beside his name would be a countdown that
    never arrives.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, unpaid_months=2)

    result = get_unpaid_wages_note(warrior=leader, leader_id=leader.id)

    assert result == LEADER_NOTE
