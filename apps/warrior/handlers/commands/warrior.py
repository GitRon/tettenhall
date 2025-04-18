import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.events.warrior import WarriorRecruited, WarriorWasSoldIntoSlavery
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.messages.commands.warrior import (
    CreateNewLeaderWarrior,
    CreateWarrior,
    DropWarriorItems,
    EnslaveCapturedWarrior,
    HealInjuredWarrior,
    RecruitCapturedWarrior,
    ReplenishWarriorMorale,
)
from apps.warrior.messages.events.warrior import (
    NewLeaderWarriorCreated,
    WarriorCreated,
    WarriorHealthHealed,
    WarriorItemsDropped,
    WarriorMoraleReplenished,
)
from apps.warrior.services.generators.warrior.leader import LeaderWarriorGenerator


@message_registry.register_command(command=ReplenishWarriorMorale)
def handle_replenish_warrior_morale(*, context: ReplenishWarriorMorale) -> list[Event] | Event | None:
    # TODO: when money goes below X, let warriors morale drop once they don't get payed

    # Morale is always filled up to the max
    recovered_morale = context.warrior.max_morale - context.warrior.current_morale

    if recovered_morale == 0:
        return None

    # Update warrior
    Warrior.objects.replenish_current_morale(obj=context.warrior, recovered_morale_points=recovered_morale)

    return WarriorMoraleReplenished(
        warrior=context.warrior,
        faction=context.warrior.faction,
        recovered_morale=recovered_morale,
        month=context.month,
    )


@message_registry.register_command(command=HealInjuredWarrior)
def handle_heal_injured_warrior(*, context: HealInjuredWarrior) -> list[Event] | Event:
    max_recoverable_health_points = 10

    # Cap healed points at the maximum
    healed_hp = min(
        random.randrange(1, max_recoverable_health_points), context.warrior.max_health - context.warrior.current_health
    )

    if healed_hp == 0:
        return None

    # Update warrior
    Warrior.objects.replenish_current_health(obj=context.warrior, healed_points=healed_hp)

    return WarriorHealthHealed(
        warrior=context.warrior,
        faction=context.warrior.faction,
        healed_points=healed_hp,
        month=context.month,
    )


@message_registry.register_command(command=RecruitCapturedWarrior)
def handle_recruit_captured_warrior(*, context: RecruitCapturedWarrior) -> list[Event] | Event:
    # Set new faction
    Warrior.objects.set_faction(obj=context.warrior, faction=context.faction)
    # Remove from captured warriors
    Faction.objects.remove_captive(faction=context.faction, warrior=context.warrior)
    # Reduce morale
    Warrior.objects.reduce_max_morale(obj=context.warrior, lost_max_morale_in_percent=0.25)

    return WarriorRecruited(
        warrior=context.warrior,
        faction=context.faction,
        # Recruiting a captured warrior is always for free
        recruitment_price=0,
        month=context.month,
    )


@message_registry.register_command(command=EnslaveCapturedWarrior)
def handle_enslave_captured_warrior(*, context: EnslaveCapturedWarrior) -> list[Event] | Event:
    # Set new faction
    Warrior.objects.set_faction(obj=context.warrior, faction=None)
    # Remove from captured warriors
    Faction.objects.remove_captive(faction=context.faction, warrior=context.warrior)

    return WarriorWasSoldIntoSlavery(
        warrior=context.warrior,
        selling_faction=context.faction,
        price=context.warrior.recruitment_price,
        month=context.month,
    )


@message_registry.register_command(command=CreateWarrior)
def handle_create_new_warrior(*, context: CreateWarrior) -> list[Event] | Event:
    # Create warrior
    warrior_generator = context.generator_class(
        culture=context.culture, faction=context.faction, savegame_id=context.savegame.id
    )
    warrior = warrior_generator.process()

    return WarriorCreated(
        savegame=context.savegame,
        faction=context.faction,
        warrior=warrior,
        month=context.month,
    )


@message_registry.register_command(command=CreateNewLeaderWarrior)
def handle_create_new_leader_warrior(*, context: CreateNewLeaderWarrior) -> list[Event] | Event:
    # Create warrior
    warrior_generator = LeaderWarriorGenerator(
        culture=context.faction.culture, faction=context.faction, savegame_id=context.faction.savegame_id
    )
    warrior = warrior_generator.process()

    return NewLeaderWarriorCreated(
        faction=context.faction,
        warrior=warrior,
    )


@message_registry.register_command(command=DropWarriorItems)
def handle_drop_warrior_items(*, context: DropWarriorItems) -> Event | None:
    items = [context.warrior.weapon, context.warrior.armor]

    if len(items) > 0:
        context.warrior.weapon = None
        context.warrior.armor = None
        context.warrior.save()

        # TODO: we should add the items to the skirmish and the winner gets them
        return WarriorItemsDropped(
            skirmish=context.skirmish,
            warrior=context.warrior,
            items=items,
        )

    return None
