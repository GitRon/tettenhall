from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.faction import PayMonthlyWarriorSalaries
from apps.faction.messages.events.faction import MonthlyWarriorSalariesPaid
from apps.finance.models.transaction import Transaction
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=PayMonthlyWarriorSalaries)
def handle_warrior_monthly_salaries(*, context: PayMonthlyWarriorSalaries) -> list[Event] | Event:
    amount = Warrior.objects.get_monthly_salary_for_faction(faction=context.faction)

    Transaction.objects.create_transaction(
        faction=context.faction, amount=-amount, reason=f"Salaries of {amount} silver paid in month {context.month}."
    )

    return MonthlyWarriorSalariesPaid(
        faction=context.faction,
        amount=amount,
        month=context.month,
    )
