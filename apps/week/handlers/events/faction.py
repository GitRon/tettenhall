from apps.core.domain import message_registry
from apps.faction.messages.events.faction import FactionFyrdReserveReplenished
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(context: FactionFyrdReserveReplenished.Context):
    PlayerWeekLog.objects.create_record(
        title=f"The fyrd has increased and has {context.new_recruitees} new recruitees!",
        message="Some fancy text",
        week=context.week,
    )
