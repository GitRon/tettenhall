from apps.core.domain import message_registry
from apps.marketplace.messages.events.warrior import PubMercenariesRestocked
from apps.warrior.messages.events.warrior import WarriorHealthHealed, WarriorMoraleReplenished
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=PubMercenariesRestocked)
def handle_marketplace_mercenaries_restocked(*, context: PubMercenariesRestocked.Context):
    PlayerWeekLog.objects.create_record(
        title=f"New mercenaries in the pub of {context.marketplace.town_name}!",
        message="Some fancy text",
        week=context.week,
    )


@message_registry.register_event(event=WarriorMoraleReplenished)
def handle_warrior_morale_replenished(*, context: WarriorMoraleReplenished.Context):
    PlayerWeekLog.objects.create_record(
        title=f"Morale of warrior {context.warrior} was replenished to the maximum.",
        message="Some fancy text",
        week=context.week,
    )


@message_registry.register_event(event=WarriorHealthHealed)
def handle_warrior_health_healed(*, context: WarriorHealthHealed.Context):
    PlayerWeekLog.objects.create_record(
        title=f"Warrior {context.warrior} healed {context.healed_points} HP.",
        message="Some fancy text",
        week=context.week,
    )
