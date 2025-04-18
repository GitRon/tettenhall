from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.skirmish.messages.events import item, skirmish, transaction, warrior


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_log_warrior_takes_damage(*, context: warrior.WarriorTookDamage) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.attacker} hits for {context.attacker_damage} damage and {context.defender} defends for "
        f"{context.defender_damage} resulting in {context.damage} damage.",
    )


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_log_warrior_defends_all_damage(*, context: warrior.WarriorDefendedAllDamage) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.defender} defended {context.attacker_damage} damage from {context.attacker} "
        f"with {context.defender_damage} defense.",
    )


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_log_attacker_defender_decided(*, context: skirmish.AttackerDefenderDecided) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.attacker} is the attacker and {context.defender} the defender and chooses "
        f"to attack with a {SkirmishActionChoices(context.attacker_action).label}.",
    )


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
def handle_log_warrior_incapacitation(*, context: warrior.WarriorWasIncapacitated) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of the fight being unconscious.",
    )


@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_log_warrior_death(*, context: warrior.WarriorWasKilled) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of the fight being killed.",
    )


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_log_round_finished(*, context: skirmish.RoundFinished) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"Round {context.skirmish.current_round} finished.",
    )


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_log_skirmish_finished(*, context: skirmish.SkirmishFinished) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"Skirmish finished. {context.skirmish.victorious_faction} won.",
    )


@message_registry.register_event(event=item.ItemDroppedAsLoot)
def handle_log_item_dropped(*, context: item.ItemDroppedAsLoot) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} dropped the item '{context.item_name}'",
    )


@message_registry.register_event(event=warrior.WarriorWasCaptured)
def handle_warrior_is_captured(*, context: warrior.WarriorWasCaptured) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} was captured and arrested.",
    )


@message_registry.register_event(event=warrior.WarriorGainedMorale)
def handle_warrior_gains_morale(*, context: warrior.WarriorGainedMorale) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} gained {int(context.gained_morale)} morale.",
    )


@message_registry.register_event(event=warrior.WarriorLostMorale)
def handle_warrior_lost_morale(*, context: warrior.WarriorLostMorale) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} lost {int(context.lost_morale)} morale.",
    )


@message_registry.register_event(event=warrior.WarriorHasFled)
def handle_warrior_has_fled(*, context: warrior.WarriorHasFled) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of morale and fled the field.",
    )


@message_registry.register_event(event=warrior.WarriorGainedExperience)
def handle_warrior_gained_experience(*, context: warrior.WarriorGainedExperience) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} gained {context.gained_experience} experience.",
    )


@message_registry.register_event(event=transaction.WarriorDroppedSilver)
def handle_warrior_dropped_silver(*, context: transaction.WarriorDroppedSilver) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} dropped {context.amount} silver.",
    )
