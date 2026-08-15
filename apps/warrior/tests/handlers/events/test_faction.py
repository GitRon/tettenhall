import pytest

from apps.faction.messages.events.faction import MonthlyWarriorSalariesUnpaid
from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.handlers.events.faction import handle_unpaid_warriors
from apps.warrior.messages.commands.warrior import PunishUnpaidWarrior


@pytest.mark.django_db
def test_handle_unpaid_warriors_asks_for_one_punishment_per_man():
    """
    One command per warrior rather than one for the list, because what happens to him depends on how
    long he has gone without - and reading that off the roster is not something an event handler may
    do under strict mode.
    """
    faction = FactionFactory()
    thegn = WarriorFactory(faction=faction)
    ealdorman = WarriorFactory(faction=faction)

    result = handle_unpaid_warriors(
        context=MonthlyWarriorSalariesUnpaid(
            faction=faction, warrior_list=[thegn, ealdorman], missing_amount=500, month=3
        )
    )

    assert result == [
        PunishUnpaidWarrior(warrior=thegn, faction=faction, month=3),
        PunishUnpaidWarrior(warrior=ealdorman, faction=faction, month=3),
    ]
