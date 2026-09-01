from queuebie import message_registry
from queuebie.messages import Command, Event

from apps.faction.models.faction import Faction
from apps.skirmish.messages.commands import warrior
from apps.skirmish.messages.commands.warrior import ReduceHealth, ReduceMorale
from apps.skirmish.messages.events.warrior import (
    LastUsedSkirmishActionStored,
    WarriorGainedExperience,
    WarriorGainedLevel,
    WarriorGainedMorale,
    WarriorHasFled,
    WarriorImprovedStats,
    WarriorLostMorale,
    WarriorWasCaptured,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=warrior.ReduceMoraleOfRemainingWarriors)
def handle_reduce_morale_of_remaining_warriors(*, context: warrior.ReduceMoraleOfRemainingWarriors) -> list[Command]:
    if context.warrior.faction_id == context.skirmish.attacking_faction_id:
        affected_warrior_list = context.skirmish.attacking_warriors.all()
    else:
        affected_warrior_list = context.skirmish.defending_warriors.all()

    # Every other warrior from the faction participating in this battle will lose 10% morale
    message_list = []
    for affected_warrior in affected_warrior_list:
        if affected_warrior != context.warrior:
            message_list.append(
                ReduceMorale(
                    skirmish=context.skirmish,
                    warrior=affected_warrior,
                    lost_morale=round(context.warrior.max_morale * 0.1),
                )
            )

    return message_list


@message_registry.register_command(command=warrior.StoreLastUsedSkirmishAction)
def handle_store_last_used_skirmish_action(*, context: warrior.StoreLastUsedSkirmishAction) -> list[Event] | Event:
    context.warrior.last_used_skirmish_action = context.skirmish_action
    context.warrior.save()

    return LastUsedSkirmishActionStored(
        skirmish=context.skirmish,
        warrior=context.warrior,
        skirmish_action=context.skirmish_action,
    )


@message_registry.register_command(command=warrior.CaptureWarrior)
def handle_warrior_is_captured(*, context: warrior.CaptureWarrior) -> list[Event] | Event | None:
    """
    Takes the warrior prisoner, unless somebody already has him.

    A warrior can stand on the roster of more than one unresolved skirmish, and ending the game
    decides every one of them in a single pass - so this runs once per fight he was in. Taking him
    twice left the same man sitting in two factions' cells at once, and announced a capture that
    emptied a faction which had already lost him.

    Asked of the captor relation rather than of "warrior.faction is None", because that is what
    being a prisoner actually means here: a warrior with no faction is also what a capture leaves
    behind, so reading it would refuse the very first capture as well.
    """
    if Faction.objects.filter(captured_warriors=context.warrior).exists():
        return None

    Faction.objects.add_captive(faction=context.capturing_faction, warrior=context.warrior)
    context.warrior.faction = None
    context.warrior.save()

    return WarriorWasCaptured(
        skirmish=context.skirmish,
        warrior=context.warrior,
        capturing_faction=context.capturing_faction,
    )


@message_registry.register_command(command=ReduceHealth)
def handle_reduce_warrior_health(*, context: ReduceHealth) -> list[Event]:
    message_list = []

    context.warrior = Warrior.objects.reduce_current_health(obj=context.warrior, damage=context.lost_health)

    # Update condition
    if context.warrior.current_health <= 0:
        if context.warrior.current_health < context.warrior.max_health * -0.15:
            condition = Warrior.ConditionChoices.CONDITION_DEAD
            message_list.append(
                WarriorWasKilled(
                    skirmish=context.skirmish,
                    warrior=context.warrior,
                    by_warrior=context.attacker,
                )
            )
        else:
            condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
            message_list.append(
                WarriorWasIncapacitated(
                    skirmish=context.skirmish,
                    warrior=context.warrior,
                    by_warrior=context.attacker,
                )
            )

        # Not "set_condition": the overkill depth above has served its purpose by now, so the health
        # is floored in the same write rather than left negative for every later reader to trip over
        Warrior.objects.put_out_of_the_fight(obj=context.warrior, condition=condition)

    return message_list


@message_registry.register_command(command=warrior.ReduceMorale)
def handle_warrior_losing_morale(*, context: warrior.ReduceMorale) -> list[Event] | Event:
    message_list = []

    # Only health warriors lose morale
    if context.warrior.condition != Warrior.ConditionChoices.CONDITION_HEALTHY:
        return message_list

    context.warrior = Warrior.objects.reduce_morale(obj=context.warrior, lost_morale=context.lost_morale)

    # The loss comes first, because the battle log is written in the order the events arrive and a
    # warrior who flees before losing the morale that made him flee reads backwards
    if context.lost_morale > 0:
        message_list.append(
            WarriorLostMorale(
                skirmish=context.skirmish,
                warrior=context.warrior,
                lost_morale=context.lost_morale,
            )
        )

    if context.warrior.current_morale <= 0:
        context.warrior = Warrior.objects.set_condition(
            obj=context.warrior, condition=Warrior.ConditionChoices.CONDITION_FLEEING
        )

        message_list.append(
            WarriorHasFled(
                skirmish=context.skirmish,
                warrior=context.warrior,
            )
        )

    return message_list


@message_registry.register_command(command=warrior.IncreaseMorale)
def handle_warrior_increasing_morale(*, context: warrior.IncreaseMorale) -> list[Event] | Event:
    context.warrior = Warrior.objects.increase_morale(obj=context.warrior, increased_morale=context.increased_morale)

    return WarriorGainedMorale(
        skirmish=context.skirmish,
        warrior=context.warrior,
        gained_morale=context.increased_morale,
    )


@message_registry.register_command(command=warrior.IncreaseExperience)
def handle_warrior_increasing_experience(*, context: warrior.IncreaseExperience) -> list[Event] | Event:
    """
    Books the experience, and announces every level threshold it carried the warrior across.

    The level before the gain is worked out from the value after it, because there is no reliable
    "before" left to read: increase_experience refreshes from the database and then adds, so the
    instance the caller was holding may have been stale. Subtracting what the manager was told to add
    from what it ended up with gives the old total whatever the caller had. Asking a later event
    handler instead is not an option either - strict mode blocks database access there.

    One event per level crossed rather than one for the crossing. A gain that spans two thresholds has
    to grow the warrior twice and read as two lines in the log; clamping to a single level-up would
    quietly swallow the second.
    """
    context.warrior = Warrior.objects.increase_experience(obj=context.warrior, experience=context.increased_experience)

    previous_level = Warrior.level_for(experience=context.warrior.experience - context.increased_experience)

    message_list = [
        WarriorGainedExperience(
            skirmish=context.skirmish,
            warrior=context.warrior,
            gained_experience=context.increased_experience,
        )
    ]

    for level in range(previous_level + 1, context.warrior.level + 1):
        message_list.append(
            WarriorGainedLevel(
                skirmish=context.skirmish,
                warrior=context.warrior,
                level=level,
            )
        )

    return message_list


@message_registry.register_command(command=warrior.IncreaseWarriorStatsOnLevelUp)
def handle_increase_warrior_stats_on_level_up(*, context: warrior.IncreaseWarriorStatsOnLevelUp) -> list[Event] | Event:
    gains = Warrior.objects.apply_level_up_growth(obj=context.warrior)

    return WarriorImprovedStats(
        skirmish=context.skirmish,
        warrior=context.warrior,
        gained_strength=gains["strength"],
        gained_dexterity=gains["dexterity"],
        gained_max_health=gains["max_health"],
        gained_max_morale=gains["max_morale"],
        gained_salary=gains["monthly_salary"],
        new_monthly_salary=context.warrior.monthly_salary,
    )
