from apps.core.domain import message_registry
from apps.skirmish.messages.events import item, skirmish, warrior
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.warrior import FightAction


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_log_warrior_takes_damage(context: warrior.WarriorTookDamage.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.attacker} hits for {context.attacker_damage} damage and {context.defender} defends for "
        f"{context.defender_damage} resulting in {context.damage} damage.",
    )


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_log_warrior_defends_all_damage(context: warrior.WarriorDefendedAllDamage.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.defender} defended all damage.",
    )


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_log_attacker_defender_decided(context: skirmish.AttackerDefenderDecided.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"Warrior {context.attacker} is the attacker and warrior {context.defender} the defender and chooses "
        f"to attack with a {FightAction(type=context.attack_action).get_type_display()}.",
    )


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
def handle_log_warrior_incapacitation(context: warrior.WarriorWasIncapacitated.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of the fight being unconscious.",
    )


@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_log_warrior_death(context: warrior.WarriorWasKilled.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of the fight being killed.",
    )


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_log_round_finished(context: skirmish.RoundFinished.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"Round {context.skirmish.current_round} finished.",
    )


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_log_skirmish_finished(context: skirmish.SkirmishFinished.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"Skirmish finished. {context.skirmish.victorious_faction} won.",
    )


@message_registry.register_event(event=item.ItemDroppedAsLoot)
def handle_log_item_dropped(context: item.ItemDroppedAsLoot.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} dropped the item '{context.item}'",
    )


@message_registry.register_event(event=warrior.WarriorWasCaptured)
def handle_warrior_is_captured(context: warrior.WarriorWasCaptured.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} was captured and arrested.",
    )


@message_registry.register_event(event=warrior.WarriorGainedMorale)
def handle_warrior_gains_morale(context: warrior.WarriorGainedMorale.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} gained {int(context.gained_morale)} morale.",
    )


@message_registry.register_event(event=warrior.WarriorLostMorale)
def handle_warrior_lost_morale(context: warrior.WarriorLostMorale.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} lost {int(context.lost_morale)} morale.",
    )


@message_registry.register_event(event=warrior.WarriorHasFled)
def handle_warrior_has_fled(context: warrior.WarriorHasFled.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of morale and fled the field.",
    )
