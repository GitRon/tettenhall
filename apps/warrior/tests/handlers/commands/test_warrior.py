from unittest import mock

import pytest

from apps.faction.messages.events.warrior import WarriorRecruited
from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.handlers.commands.warrior import (
    handle_heal_injured_warrior,
    handle_recruit_captured_warrior,
    handle_replenish_warrior_morale,
)
from apps.warrior.messages.commands.warrior import HealInjuredWarrior, RecruitCapturedWarrior, ReplenishWarriorMorale
from apps.warrior.messages.events.warrior import WarriorHealthHealed, WarriorMoraleReplenished


@pytest.mark.django_db
def test_handle_replenish_warrior_morale_fills_up_to_the_maximum():
    warrior = WarriorFactory(current_morale=5, max_morale=20)

    result = handle_replenish_warrior_morale(context=ReplenishWarriorMorale(warrior=warrior, month=3))

    assert result == WarriorMoraleReplenished(warrior=warrior, faction=warrior.faction, recovered_morale=15, month=3)
    warrior.refresh_from_db()
    assert warrior.current_morale == 20


@pytest.mark.django_db
def test_handle_replenish_warrior_morale_does_nothing_on_full_morale():
    warrior = WarriorFactory(current_morale=20, max_morale=20)

    result = handle_replenish_warrior_morale(context=ReplenishWarriorMorale(warrior=warrior, month=3))

    assert result is None


@pytest.mark.django_db
def test_handle_heal_injured_warrior_heals_rolled_amount():
    warrior = WarriorFactory(current_health=5, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=5, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 10


@pytest.mark.django_db
def test_handle_heal_injured_warrior_caps_healing_at_the_maximum():
    warrior = WarriorFactory(current_health=18, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=2, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 20


@pytest.mark.django_db
def test_handle_heal_injured_warrior_at_full_health():
    warrior = WarriorFactory(current_health=20, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    assert result is None


@pytest.mark.django_db
def test_handle_heal_injured_warrior_can_roll_the_maximum():
    """
    randrange() excludes its upper bound, so the maximum recoverable amount needs the "+ 1" to be
    reachable at all.
    """
    # A Shrine mends up to 8 points a month
    warrior = WarriorFactory(current_health=1, max_health=20, faction__town__sanctuary=1)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=8) as mocked_randrange:
        result = handle_heal_injured_warrior(
            context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3)
        )

    mocked_randrange.assert_called_once_with(1, 9)
    assert result.healed_points == 8


@pytest.mark.django_db
def test_handle_heal_injured_warrior_heals_further_with_a_larger_sanctuary():
    """
    The sanctuary sets the ceiling of the monthly healing roll, so the building is what decides how
    fast a warrior comes back.
    """
    warrior = WarriorFactory(current_health=1, max_health=30, faction__town__sanctuary=3)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=1) as mocked_randrange:
        handle_heal_injured_warrior(context=HealInjuredWarrior(faction=warrior.faction, warrior=warrior, month=3))

    # A Great Sanctuary reaches 20 points, against the 4 a town without one manages
    mocked_randrange.assert_called_once_with(1, 21)


@pytest.mark.django_db
def test_handle_heal_injured_warrior_mends_a_captive_at_his_captors_sanctuary():
    """
    A captive belongs to nobody, so the ceiling can only come from the faction holding him.
    """
    captor = FactionFactory(town__sanctuary=1)
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=8) as mocked_randrange:
        result = handle_heal_injured_warrior(context=HealInjuredWarrior(faction=captor, warrior=captive, month=3))

    # A Shrine mends up to 8 points a month, against the 4 of the town the captive no longer has
    mocked_randrange.assert_called_once_with(1, 9)
    assert result == WarriorHealthHealed(warrior=captive, faction=captor, healed_points=8, month=3)


@pytest.mark.django_db
def test_handle_heal_injured_warrior_wakes_a_captive_without_freeing_him():
    """
    Mending a captive above zero health lifts him out of CONDITION_UNCONSCIOUS, which is what makes
    him worth recruiting. He stays a prisoner all the same - every roster query goes through the
    faction he does not have, so being healthy buys him nothing while he is held.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=captor.savegame,
        culture=captor.culture,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    captor.captured_warriors.add(captive)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=4):
        handle_heal_injured_warrior(context=HealInjuredWarrior(faction=captor, warrior=captive, month=3))

    captive.refresh_from_db()
    assert captive.condition == Warrior.ConditionChoices.CONDITION_HEALTHY
    assert list(captor.captured_warriors.all()) == [captive]


@pytest.mark.django_db
def test_handle_recruit_captured_warrior_keeps_the_health_he_was_mended_to():
    """
    Recruiting is the moment a captive rejoins a roster, not a second course of treatment: the
    months in the cell already brought him back, and taking him on adds nothing to that.
    """
    captor = FactionFactory()
    captive = WarriorFactory(
        faction=None, savegame=captor.savegame, culture=captor.culture, current_health=20, max_health=20
    )
    captor.captured_warriors.add(captive)

    result = handle_recruit_captured_warrior(context=RecruitCapturedWarrior(warrior=captive, faction=captor, month=3))

    assert result == WarriorRecruited(warrior=captive, faction=captor, recruitment_price=0, month=3)
    captive.refresh_from_db()
    assert captive.current_health == 20
