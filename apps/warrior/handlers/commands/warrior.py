import random

from apps.core.domain import message_registry
from apps.skirmish.models.warrior import Warrior
from apps.warrior.messages.commands.warrior import HealInjuredWarrior, ReplenishWarriorMorale
from apps.warrior.messages.events.warrior import WarriorHealthHealed, WarriorMoraleReplenished


@message_registry.register_command(command=ReplenishWarriorMorale)
def handle_replenish_warrior_morale(context: ReplenishWarriorMorale.Context):
    # Morale is always filled up to the max
    recovered_morale = context.warrior.max_morale - context.warrior.current_morale

    # Update warrior
    Warrior.objects.replenish_current_morale(obj=context.warrior, recovered_morale_points=recovered_morale)

    return WarriorMoraleReplenished.generator(
        context_data={
            "warrior": context.warrior,
            "recovered_morale": recovered_morale,
            "week": context.week,
        }
    )


@message_registry.register_command(command=HealInjuredWarrior)
def handle_heal_injured_warrior(context: HealInjuredWarrior.Context):
    max_recoverable_health_points = 10

    # Cap healed points at the maximum
    healed_hp = min(
        random.randrange(1, max_recoverable_health_points), context.warrior.max_health - context.warrior.current_health
    )

    # Update warrior
    Warrior.objects.replenish_current_health(obj=context.warrior, healed_points=healed_hp)

    return WarriorHealthHealed.generator(
        context_data={
            "warrior": context.warrior,
            "healed_points": healed_hp,
            "week": context.week,
        }
    )
