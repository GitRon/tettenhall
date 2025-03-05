from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events import warrior
from apps.faction.messages.events.faction import MonthlyWarriorSalariesPaid, NewFactionCreated
from apps.finance.messages.commands.transaction import CreateTransaction


@message_registry.register_event(event=warrior.WarriorRecruited)
def handle_warrior_recruited(*, context: warrior.WarriorRecruited) -> Command:
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


@message_registry.register_event(event=NewFactionCreated)
def handle_hand_out_starting_silver_for_new_factions(*, context: NewFactionCreated) -> Command:
    return CreateTransaction(faction=context.faction, month=1, amount=1000, reason="Starting silver")
