from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.commands.skirmish import DetermineAttacker
from apps.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    IncreaseWarriorStatsOnLevelUp,
    ReduceHealth,
    ReduceMorale,
    ReduceMoraleOfRemainingWarriors,
    StoreLastUsedSkirmishAction,
)
from apps.skirmish.messages.events import skirmish, warrior


@message_registry.register_event(event=skirmish.FighterPairsMatched)
def handle_determine_attacker(*, context: skirmish.FighterPairsMatched) -> Command:
    return DetermineAttacker(
        skirmish=context.skirmish,
        warrior_1=context.warrior_1,
        warrior_2=context.warrior_2,
        action_1=context.attack_action_1,
        action_2=context.attack_action_2,
    )


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_store_last_used_skirmish_action(*, context: skirmish.AttackerDefenderDecided) -> list[Command]:
    return [
        StoreLastUsedSkirmishAction(
            skirmish=context.skirmish,
            warrior=context.attacker,
            skirmish_action=context.attacker_action,
        ),
        StoreLastUsedSkirmishAction(
            skirmish=context.skirmish,
            warrior=context.defender,
            skirmish_action=context.defender_action,
        ),
    ]


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_reduce_health_and_update_condition(*, context: warrior.WarriorTookDamage) -> list[Command]:
    return [
        # Reduce health
        ReduceHealth(
            skirmish=context.skirmish,
            warrior=context.defender,
            attacker=context.attacker,
            lost_health=context.damage,
        ),
        # Taking damages causes loss of 10% morale
        ReduceMorale(
            skirmish=context.skirmish,
            warrior=context.defender,
            lost_morale=round(context.defender.max_morale * 0.1),
        ),
    ]


@message_registry.register_event(event=warrior.WarriorHasFled)
@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
    *,
    context: [
        warrior.WarriorHasFled,
        warrior.WarriorWasIncapacitated,
        warrior.WarriorWasKilled,
    ],
) -> Command:
    # Determining who is affected needs the participants of the skirmish, and strict mode blocks
    # database access in event handlers, so the command handler does the reading
    return ReduceMoraleOfRemainingWarriors(skirmish=context.skirmish, warrior=context.warrior)


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_experience_gain_on_warrior_incapacitation(
    *,
    context: [warrior.WarriorWasIncapacitated, warrior.WarriorWasKilled],
) -> Command:
    gained_experience = 25

    return IncreaseExperience(
        skirmish=context.skirmish,
        warrior=context.by_warrior,
        increased_experience=gained_experience,
    )


@message_registry.register_event(event=warrior.WarriorGainedLevel)
def handle_stat_growth_on_warrior_level_up(*, context: warrior.WarriorGainedLevel) -> Command:
    # The writing happens in the command handler rather than here, for the same reason
    # ReduceMoraleOfRemainingWarriors exists rather than the morale drop happening inline: an event
    # handler reacts, it does not touch the database
    return IncreaseWarriorStatsOnLevelUp(skirmish=context.skirmish, warrior=context.warrior)


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_morale_change_on_warrior_defends_all_damage(*, context: warrior.WarriorDefendedAllDamage) -> Command | None:
    """
    Turning a blow aside steadies a warrior. Cowering behind a shield wears him down.

    Without the second half a fight could not end. Below a quarter of his health a warrior always
    picks a defensive stance, that stance doubles his defense and zeroes his attack, and once the
    doubled defense outruns what the other side can hit for, nobody takes damage again - and the only
    other two things that move morale in this game are taking damage and watching a comrade fall.
    Neither happens, so nobody routs, no side ever loses its last healthy warrior, and the round
    counter climbs for ever. One observed fight reached 54 rounds. That matters more than it sounds:
    the month cannot be advanced while a skirmish is unresolved, so such a fight ends the savegame's
    life rather than its own.

    Draining instead of merely withholding the reward is the whole point - a warrior sitting at the
    same morale for ever is exactly the fight that never ends. Dropping him to zero raises
    WarriorHasFled, and a fleeing warrior is not a healthy one, which is what the defeat check in
    handle_finish_round already counts.
    """
    # Ten percent of what he can hold, the lever the reward and the damage penalty already use
    morale_at_stake = round(context.defender.max_morale * 0.1)

    if context.defender_action == SkirmishActionChoices.DEFENSIVE_STANCE:
        # Floored at one point, and only here: a tenth of a small morale pool rounds away to nothing,
        # and a stance that costs nothing is the unwinnable fight all over again. The reward keeps its
        # old shape below, because no such argument applies to it - inventing a point of morale for a
        # warrior too brittle to have earned one would be a balance change with nothing behind it.
        return ReduceMorale(
            skirmish=context.skirmish,
            warrior=context.defender,
            lost_morale=max(1, morale_at_stake),
        )

    if morale_at_stake > 0:
        return IncreaseMorale(
            skirmish=context.skirmish,
            warrior=context.defender,
            increased_morale=morale_at_stake,
        )

    return None


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_capture_unconscious_warriors(*, context: skirmish.SkirmishFinished) -> list[Command]:
    message_list = []

    for captured_warrior in context.defeated_unconscious_warriors:
        message_list.append(
            CaptureWarrior(
                skirmish=context.skirmish,
                warrior=captured_warrior,
                capturing_faction=context.skirmish.victorious_faction,
            )
        )

    return message_list


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_experience_gain_after_battle_for_victor(*, context: skirmish.SkirmishFinished) -> list[Command]:
    message_list = []

    gained_experience = 10

    for victorious_warrior in context.victorious_healthy_warriors:
        message_list.append(
            IncreaseExperience(
                skirmish=context.skirmish,
                warrior=victorious_warrior,
                increased_experience=gained_experience,
            )
        )

    return message_list
