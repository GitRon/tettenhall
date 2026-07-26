import pytest

from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.handlers.commands.warrior import handle_replenish_warrior_morale
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale
from apps.warrior.messages.events.warrior import WarriorMoraleReplenished


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
