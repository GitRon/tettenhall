from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.handlers.events.skirmish import handle_faction_loots_warriors_silver
from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_faction_loots_warriors_silver_books_the_loot_as_income():
    gaining_faction = FactionFactory.build()

    result = handle_faction_loots_warriors_silver(
        context=WarriorDroppedSilver(
            skirmish=SkirmishFactory.build(),
            warrior=WarriorFactory.build(name="Cuthred"),
            gaining_faction=gaining_faction,
            amount=50,
            month=3,
        )
    )

    assert result == CreateTransaction(faction=gaining_faction, amount=50, reason="Looted from Cuthred", month=3)
