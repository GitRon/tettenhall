from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.handlers.events.warrior import handle_pay_warrior_severance
from apps.finance.messages.commands.transaction import CreateTransaction
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.events.warrior import WarriorWasDismissed


def test_handle_pay_warrior_severance_debits_what_he_is_owed():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Cuthbert", faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_pay_warrior_severance(
        context=WarriorWasDismissed(
            warrior=warrior, faction=faction, savegame=SavegameFactory.build(), severance_pay=120, month=3
        )
    )

    assert result == CreateTransaction(faction=faction, amount=-120, reason="Severance for Cuthbert", month=3)


def test_handle_pay_warrior_severance_writes_nothing_for_a_man_on_no_wage():
    """
    A row reading "-0 silver" is not a payment, and a man drawing nothing is owed nothing.
    """
    faction = FactionFactory.build()

    result = handle_pay_warrior_severance(
        context=WarriorWasDismissed(
            warrior=WarriorFactory.build(),
            faction=faction,
            savegame=SavegameFactory.build(),
            severance_pay=0,
            month=3,
        )
    )

    assert result is None
