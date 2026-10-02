from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.handlers.events.skirmish import (
    handle_faction_loots_warriors_silver,
    handle_herds_lifted_change_hands,
    handle_pay_march_cost_for_attack,
)
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.messages.events.skirmish import FactionWasAttacked, HerdsLifted
from apps.warband.skirmish.messages.events.transaction import WarriorDroppedSilver
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


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


def test_handle_pay_march_cost_for_attack_in_winter():
    """Month 7 is Winterfylleth: every man who marches is paid for, the leader among them."""
    attacking_faction = FactionFactory.build()
    defending_faction = FactionFactory.build(name="Tamworth")

    result = handle_pay_march_cost_for_attack(
        context=FactionWasAttacked(
            attacking_faction=attacking_faction,
            defending_faction=defending_faction,
            attacking_warriors=[WarriorFactory.build(), WarriorFactory.build()],
            defending_warriors=[WarriorFactory.build()],
            fortification_strength=0,
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=7,
        )
    )

    assert result == CreateTransaction(
        faction=attacking_faction, amount=-20, reason="Winter march on Tamworth", month=7
    )


def test_handle_pay_march_cost_for_attack_in_summer():
    result = handle_pay_march_cost_for_attack(
        context=FactionWasAttacked(
            attacking_faction=FactionFactory.build(),
            defending_faction=FactionFactory.build(),
            attacking_warriors=[WarriorFactory.build()],
            defending_warriors=[WarriorFactory.build()],
            fortification_strength=0,
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
        )
    )

    assert result is None


def test_handle_herds_lifted_change_hands_moves_the_silver_from_one_ledger_to_the_other():
    raiding_faction = FactionFactory.build(name="Mercia")
    raided_faction = FactionFactory.build(name="Wessex")

    result = handle_herds_lifted_change_hands(
        context=HerdsLifted(
            skirmish=SkirmishFactory.build(),
            raiding_faction=raiding_faction,
            raided_faction=raided_faction,
            amount=90,
            month=4,
        )
    )

    assert result == [
        CreateTransaction(faction=raiding_faction, amount=90, reason="Herds lifted from Wessex", month=4),
        CreateTransaction(faction=raided_faction, amount=-90, reason="Herds lifted by Mercia", month=4),
    ]
