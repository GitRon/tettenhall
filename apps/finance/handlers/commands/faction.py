from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.faction import PayWeeklyWarriorSalaries
from apps.faction.messages.events.faction import WeeklyWarriorSalariesPaid
from apps.finance.models.transaction import Transaction
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=PayWeeklyWarriorSalaries)
def handle_warrior_weekly_salaries(*, context: PayWeeklyWarriorSalaries) -> list[Event] | Event:
    amount = Warrior.objects.get_weekly_salary_for_faction(faction=context.faction)

    Transaction.objects.create_transaction(
        faction=context.faction, amount=-amount, reason=f"Salaries of {amount} silver paid in week {context.week}."
    )

    return WeeklyWarriorSalariesPaid(
        faction=context.faction,
        amount=amount,
        week=context.week,
    )
