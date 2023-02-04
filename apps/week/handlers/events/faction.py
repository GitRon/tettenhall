from apps.core.domain import message_registry
from apps.faction.messages.events.faction import FactionFyrdReserveReplenished, WeeklyWarriorSalariesPaid
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(context: FactionFyrdReserveReplenished.Context):
    PlayerWeekLog.objects.create_record(
        title=f"The fyrd has increased and has {context.new_recruitees} new recruitees!",
        message="Some fancy text",
        week=context.week,
    )


@message_registry.register_event(event=WeeklyWarriorSalariesPaid)
def handle_pay_weekly_salary(context: WeeklyWarriorSalariesPaid.Context):
    PlayerWeekLog.objects.create_record(
        title=f"Weekly salaries paid of {context.amount} silver.",
        message="Some fancy text",
        week=context.week,
    )
