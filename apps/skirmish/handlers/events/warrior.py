from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import DetermineAttacker
from apps.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    ReduceHealth,
    ReduceMorale,
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
) -> list[Command]:
    message_list = []

    if context.warrior.faction_id == context.skirmish.player_faction_id:
        affected_warrior_list = context.skirmish.player_warriors.all()
    else:
        affected_warrior_list = context.skirmish.non_player_warriors.all()

    # Every other warrior from the faction participating in this battle will lose 10% morale
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


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_morale_increase_on_warriors_defends_all_damage(
    *, context: warrior.WarriorDefendedAllDamage
) -> Command | None:
    increased_morale = round(context.defender.max_morale * 0.1)

    if increased_morale > 0:
        return IncreaseMorale(
            skirmish=context.skirmish,
            warrior=context.defender,
            increased_morale=increased_morale,
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

    for victorious_warrior in context.victorious_conscious_warriors:
        message_list.append(
            IncreaseExperience(
                skirmish=context.skirmish,
                warrior=victorious_warrior,
                increased_experience=gained_experience,
            )
        )

    return message_list
