import random

from django.db.models import F
from queuebie import message_registry
from queuebie.messages import Event

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
def handle_replenish_fyrd_reserve(*, context: ReplenishFyrdReserve) -> list[Event] | Event:
    new_recruitees = random.randrange(0, 3)

    if new_recruitees == 0:
        return None

    # Update faction
    Faction.objects.replenish_fyrd_reserve(faction=context.faction, new_recruitees=new_recruitees)

    return FactionFyrdReserveReplenished(
        faction=context.faction,
        new_recruitees=new_recruitees,
        week=context.week,
    )


@message_registry.register_command(command=DetermineWarriorsWithLowMorale)
def handle_determine_warriors_with_low_morale(*, context: DetermineWarriorsWithLowMorale) -> list[Event] | Event:
    warrior_qs = context.faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    return FactionWarriorsWithLowMoraleDetermined(
        faction=context.faction,
        warrior_list=list(warrior_qs),
        week=context.week,
    )


@message_registry.register_command(command=DetermineInjuredWarriors)
def handle_determine_injured_warriors(*, context: DetermineInjuredWarriors) -> list[Event] | Event:
    # Get all injured but not dead warriors of "faction"
    warrior_qs = context.faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD).filter(
        current_health__lt=F("max_health")
    )

    event_list = []
    for warrior in warrior_qs:
        event_list.append(
            HealInjuredWarrior(
                warrior=warrior,
                week=context.week,
            )
        )

    return event_list
