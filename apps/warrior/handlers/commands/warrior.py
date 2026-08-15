import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.events.warrior import WarriorRecruited, WarriorWasSoldIntoSlavery
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.town.buildings.sanctuary import Sanctuary
from apps.warrior.messages.commands.warrior import (
    CreateNewLeaderWarrior,
    CreateWarrior,
    EnslaveCapturedWarrior,
    HealInjuredWarrior,
    PunishUnpaidWarrior,
    RecruitCapturedWarrior,
    ReplenishWarriorMorale,
)
from apps.warrior.messages.events.warrior import (
    NewLeaderWarriorCreated,
    WarriorCreated,
    WarriorDesertedOverUnpaidSalary,
    WarriorHealthHealed,
    WarriorLostMoraleOverUnpaidSalary,
    WarriorMoraleReplenished,
)
from apps.warrior.services.generators.warrior.leader import LeaderWarriorGenerator


@message_registry.register_command(command=PunishUnpaidWarrior)
def handle_punish_unpaid_warrior(*, context: PunishUnpaidWarrior) -> Event:
    """
    What a month without wages does to the man who went without it.

    Morale first and desertion after, so the war band sours visibly before it starts shrinking and
    the player has a couple of months to sell something. Low morale is what routs a warrior
    mid-fight, so an unpaid band breaks early without any of this having to say so.

    The gear stays behind. An item belongs to the faction and is only wielded by a warrior, so
    letting him keep it would put it out of everyone's reach rather than in his hands - and the
    silver it fetches is exactly what a broke faction needs.
    """
    # The leader is the one man who never walks. Faction.leader is a CASCADE FK and losing him is
    # what defeats a faction, so a leader deserting would end the game over a wage bill instead of
    # shrinking the war band to what it can afford. He sulks indefinitely instead.
    is_leader = context.faction.leader_id == context.warrior.id

    if context.warrior.unpaid_months >= Warrior.UNPAID_MONTHS_UNTIL_DESERTION and not is_leader:
        Warrior.objects.strip_equipment(obj=context.warrior)
        Warrior.objects.set_faction(obj=context.warrior, faction=None)

        return WarriorDesertedOverUnpaidSalary(
            warrior=context.warrior,
            faction=context.faction,
            month=context.month,
        )

    # Floored at one point, the way apply_level_up_growth floors its gains: a quarter of a levy's
    # morale rounds to nothing for every maximum below three, and a penalty of zero is not one
    lost_morale = max(1, round(context.warrior.max_morale * Warrior.UNPAID_MORALE_LOSS))
    Warrior.objects.reduce_morale(obj=context.warrior, lost_morale=lost_morale)

    return WarriorLostMoraleOverUnpaidSalary(
        warrior=context.warrior,
        faction=context.faction,
        lost_morale=lost_morale,
        month=context.month,
    )


@message_registry.register_command(command=ReplenishWarriorMorale)
def handle_replenish_warrior_morale(*, context: ReplenishWarriorMorale) -> list[Event] | Event | None:
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
def handle_heal_injured_warrior(*, context: HealInjuredWarrior) -> Event | None:
    # How far the town's sanctuary can mend a warrior in one month. The faction is taken off the
    # command rather than off the warrior, because a captive has none: capture clears
    # "warrior.faction", and he is mended in his captor's town, at his captor's sanctuary.
    sanctuary = Sanctuary.get_building_by_type(building_type=context.faction.town.sanctuary)
    max_recoverable_health_points = sanctuary.MAX_HEALING_POINTS

    # Cap healed points at the maximum. randrange() excludes its upper bound, so it needs the "+ 1"
    # for "max_recoverable_health_points" to be reachable at all.
    healed_hp = min(
        random.randrange(1, max_recoverable_health_points + 1),
        context.warrior.max_health - context.warrior.current_health,
    )

    if healed_hp == 0:
        return None

    # Update warrior
    Warrior.objects.replenish_current_health(obj=context.warrior, healed_points=healed_hp)

    return WarriorHealthHealed(
        warrior=context.warrior,
        faction=context.faction,
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
