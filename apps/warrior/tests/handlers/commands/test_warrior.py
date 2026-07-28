from unittest import mock

import pytest

from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.handlers.commands.warrior import handle_heal_injured_warrior, handle_replenish_warrior_morale
from apps.warrior.messages.commands.warrior import HealInjuredWarrior, ReplenishWarriorMorale
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
        result = handle_heal_injured_warrior(context=HealInjuredWarrior(warrior=warrior, month=3))

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=5, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 10


@pytest.mark.django_db
def test_handle_heal_injured_warrior_caps_healing_at_the_maximum():
    warrior = WarriorFactory(current_health=18, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(context=HealInjuredWarrior(warrior=warrior, month=3))

    assert result == WarriorHealthHealed(warrior=warrior, faction=warrior.faction, healed_points=2, month=3)
    warrior.refresh_from_db()
    assert warrior.current_health == 20


@pytest.mark.django_db
def test_handle_heal_injured_warrior_at_full_health():
    warrior = WarriorFactory(current_health=20, max_health=20)

    with mock.patch("apps.warrior.handlers.commands.warrior.random.randrange", return_value=5):
        result = handle_heal_injured_warrior(context=HealInjuredWarrior(warrior=warrior, month=3))

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
        result = handle_heal_injured_warrior(context=HealInjuredWarrior(warrior=warrior, month=3))

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
        handle_heal_injured_warrior(context=HealInjuredWarrior(warrior=warrior, month=3))

    # A Great Sanctuary reaches 20 points, against the 4 a town without one manages
    mocked_randrange.assert_called_once_with(1, 21)
