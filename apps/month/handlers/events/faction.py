from queuebie import message_registry

from apps.faction.messages.events.faction import FactionFyrdReserveReplenished, MonthlyWarriorSalariesPaid
from apps.month.models.player_month_log import PlayerMonthLog


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(*, context: FactionFyrdReserveReplenished):
    PlayerMonthLog.objects.create_record(
        title=f"The fyrd has increased and has {context.new_recruitees} new recruitees!",
        month=context.month,
        faction_id=context.faction.id,
    )


@message_registry.register_event(event=MonthlyWarriorSalariesPaid)
def handle_pay_monthly_salary(*, context: MonthlyWarriorSalariesPaid):
    PlayerMonthLog.objects.create_record(
        title=f"Monthly salaries paid of {context.amount} silver.",
        month=context.month,
        faction_id=context.faction.id,
    )
