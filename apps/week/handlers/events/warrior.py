from apps.core.domain import message_registry
from apps.marketplace.messages.events.warrior import PubMercenariesRestocked
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=PubMercenariesRestocked)
def handle_marketplace_mercenaries_restocked(context: PubMercenariesRestocked.Context):
    PlayerWeekLog.objects.create_record(
        title=f"New mercenaries in the pub of {context.marketplace.town_name}!",
        message="Some fancy text",
        week=context.week,
    )
