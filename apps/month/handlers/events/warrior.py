from queuebie import message_registry

from apps.month.models.player_month_log import PlayerMonthLog
from apps.warrior.messages.events.warrior import WarriorHealthHealed, WarriorMoraleReplenished


@message_registry.register_event(event=WarriorMoraleReplenished)
def handle_warrior_morale_replenished(*, context: WarriorMoraleReplenished):
    PlayerMonthLog.objects.create_record(
        title=f"Morale of warrior {context.warrior} was replenished to the maximum.",
        month=context.month,
        faction_id=context.warrior.faction_id,
    )


@message_registry.register_event(event=WarriorHealthHealed)
def handle_warrior_health_healed(*, context: WarriorHealthHealed):
    PlayerMonthLog.objects.create_record(
        title=f"Warrior {context.warrior} healed {context.healed_points} HP.",
        month=context.month,
        faction_id=context.warrior.faction_id,
    )
