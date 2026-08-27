from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events import warrior
from apps.faction.messages.events.faction import (
    MonthlyBuildingMoneyEarned,
    MonthlyFactionIncomeEarned,
    MonthlyWarriorSalariesPaid,
    NewFactionCreated,
)
from apps.finance.messages.commands.transaction import CreateTransaction


@message_registry.register_event(event=warrior.WarriorRecruited)
def handle_warrior_recruited(*, context: warrior.WarriorRecruited) -> Command | None:
    # A recruitment at no price moves no silver, and a row reading "-0 silver" is not a payment.
    # Silent rather than free-with-a-receipt because the fyrd levy is free and every faction drafts
    # every month it can afford to, so the ledger would fill with those and a rival's balance is meant
    # to be readable off it - the purse itself is shown nowhere in the UI.
    if context.recruitment_price == 0:
        return None

    # Pay the money
    return CreateTransaction(
        reason=f"{context.warrior} recruited",
        amount=-context.recruitment_price,
        faction=context.faction,
        month=context.month,
    )


@message_registry.register_event(event=warrior.WarriorWasSoldIntoSlavery)
def handle_warrior_sold_into_slavery(*, context: warrior.WarriorWasSoldIntoSlavery) -> Command:
    # Pay the money
    return CreateTransaction(
        reason=f"{context.warrior} was sold into slavery",
        amount=context.warrior.slavery_selling_price,
        faction=context.selling_faction,
        month=context.month,
    )


@message_registry.register_event(event=MonthlyWarriorSalariesPaid)
def handle_pay_warrior_salaries(*, context: MonthlyWarriorSalariesPaid) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=-context.amount,
        reason=f"Salaries paid in month {context.month}.",
        month=context.month,
    )


@message_registry.register_event(event=MonthlyBuildingMoneyEarned)
def handle_building_money_earnings(*, context: MonthlyBuildingMoneyEarned) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=context.amount,
        reason=f"Building earnings in month {context.month}.",
        month=context.month,
    )


@message_registry.register_event(event=MonthlyFactionIncomeEarned)
def handle_monthly_faction_income(*, context: MonthlyFactionIncomeEarned) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=context.amount,
        reason=f"Faction income in month {context.month}.",
        month=context.month,
    )


@message_registry.register_event(event=NewFactionCreated)
def handle_hand_out_starting_silver_for_new_factions(*, context: NewFactionCreated) -> Command:
    return CreateTransaction(faction=context.faction, month=1, amount=1000, reason="Starting silver")
