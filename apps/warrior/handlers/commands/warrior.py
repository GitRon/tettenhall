import random

from apps.core.domain import message_registry
from apps.faction.messages.events.warrior import WarriorRecruited, WarriorWasSoldIntoSlavery
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.messages.commands.warrior import (
    EnslaveCapturedWarrior,
    HealInjuredWarrior,
    RecruitCapturedWarrior,
    ReplenishWarriorMorale,
)
from apps.warrior.messages.events.warrior import WarriorHealthHealed, WarriorMoraleReplenished


@message_registry.register_command(command=ReplenishWarriorMorale)
def handle_replenish_warrior_morale(context: ReplenishWarriorMorale.Context):
    # Morale is always filled up to the max
    recovered_morale = context.warrior.max_morale - context.warrior.current_morale

    if recovered_morale == 0:
        return None

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

    if healed_hp == 0:
        return None

    # Update warrior
    Warrior.objects.replenish_current_health(obj=context.warrior, healed_points=healed_hp)

    return WarriorHealthHealed.generator(
        context_data={
            "warrior": context.warrior,
            "healed_points": healed_hp,
            "week": context.week,
        }
    )


@message_registry.register_command(command=RecruitCapturedWarrior)
def handle_recruit_captured_warrior(context: RecruitCapturedWarrior.Context):
    # Set new faction
    Warrior.objects.set_faction(obj=context.warrior, faction=context.faction)
    # Remove from captured warriors
    Faction.objects.remove_captive(faction=context.faction, warrior=context.warrior)
    # Reduce morale
    Warrior.objects.reduce_max_morale(obj=context.warrior, lost_max_morale_in_percent=0.25)

    return WarriorRecruited.generator(
        context_data={
            "warrior": context.warrior,
            "faction": context.faction,
            "recruitment_price": context.warrior.recruitment_price,
        }
    )


@message_registry.register_command(command=EnslaveCapturedWarrior)
def handle_enslave_captured_warrior(context: EnslaveCapturedWarrior.Context):
    # Set new faction
    Warrior.objects.set_faction(obj=context.warrior, faction=None)
    # Remove from captured warriors
    Faction.objects.remove_captive(faction=context.faction, warrior=context.warrior)

    return WarriorWasSoldIntoSlavery.generator(
        context_data={
            "warrior": context.warrior,
            "selling_faction": context.faction,
            "price": context.warrior.recruitment_price,
        }
    )
