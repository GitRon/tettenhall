import random

from django.db.models import F

from apps.core.domain import message_registry
from apps.faction.messages.commands.faction import (
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    ReplenishFyrdReserve,
)
from apps.faction.messages.events.faction import FactionFyrdReserveReplenished, FactionWarriorsWithLowMoraleDetermined
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.messages.commands.warrior import HealInjuredWarrior


@message_registry.register_command(command=ReplenishFyrdReserve)
def handle_replenish_fyrd_reserve(context: ReplenishFyrdReserve.Context):
    new_recruitees = random.randrange(0, 3)

    if new_recruitees == 0:
        return

    # Update faction
    Faction.objects.replenish_fyrd_reserve(faction=context.faction, new_recruitees=new_recruitees)

    return FactionFyrdReserveReplenished.generator(
        context_data={
            "faction": context.faction,
            "new_recruitees": new_recruitees,
            "week": context.week,
        }
    )


@message_registry.register_command(command=DetermineWarriorsWithLowMorale)
def handle_determine_warriors_with_low_morale(context: DetermineWarriorsWithLowMorale.Context):
    warrior_qs = context.faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    return FactionWarriorsWithLowMoraleDetermined.generator(
        context_data={
            "faction": context.faction,
            "warrior_list": list(warrior_qs),
            "week": context.week,
        }
    )


@message_registry.register_command(command=DetermineInjuredWarriors)
def handle_determine_injured_warriors(context: DetermineInjuredWarriors.Context):
    # Get all injured but not dead warriors of "faction"
    warrior_qs = context.faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD).filter(
        current_health__lt=F("max_health")
    )

    event_list = []
    for warrior in warrior_qs:
        event_list.append(
            HealInjuredWarrior.generator(
                context_data={
                    "warrior": warrior,
                    "week": context.week,
                }
            )
        )

    return event_list
