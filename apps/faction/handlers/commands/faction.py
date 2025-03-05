import random

from django.db.models import F
from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.faction import (
    CreateNewFaction,
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    ReplenishFyrdReserve,
    SetNewLeaderWarrior,
)
from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    FactionWarriorsWithLowMoraleDetermined,
    NewFactionCreated,
    NewLeaderWarriorSet,
)
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.messages.commands.warrior import HealInjuredWarrior


@message_registry.register_command(command=CreateNewFaction)
def handle_create_new_faction(*, context: CreateNewFaction) -> list[Event] | Event:
    faction = Faction.objects.create(
        name=context.name,
        culture_id=context.culture_id,
        savegame=context.savegame,
        fyrd_reserve=random.randint(2, 5),
    )

    # Set player faction in savegame
    if context.is_player_faction:
        context.savegame.player_faction = faction
        context.savegame.save()

    return NewFactionCreated(
        faction=faction,
    )


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
        month=context.month,
    )


@message_registry.register_command(command=DetermineWarriorsWithLowMorale)
def handle_determine_warriors_with_low_morale(*, context: DetermineWarriorsWithLowMorale) -> list[Event] | Event:
    warrior_qs = context.faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    return FactionWarriorsWithLowMoraleDetermined(
        faction=context.faction,
        warrior_list=list(warrior_qs),
        month=context.month,
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
            # TODO: this should be an event, not a command
            HealInjuredWarrior(
                warrior=warrior,
                month=context.month,
            )
        )

    return event_list


@message_registry.register_command(command=SetNewLeaderWarrior)
def handle_set_new_leader_warrior(*, context: SetNewLeaderWarrior) -> list[Event] | Event:
    context.faction.leader = context.warrior
    context.faction.save()

    return NewLeaderWarriorSet(faction=context.faction, warrior=context.warrior)
