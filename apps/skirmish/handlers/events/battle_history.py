from apps.core.domain import message_registry
from apps.skirmish.messages.events import duel, warrior
from apps.skirmish.models.battle_history import BattleHistory


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_log_warrior_takes_damage(context: warrior.WarriorTookDamage.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"{context.attacker} hits for {context.attacker_damage} damage and {context.defender} defends for "
        f"{context.defender_damage} resulting in {context.damage} damage.",
    )


@message_registry.register_event(event=duel.AttackerDefenderDecided)
def handle_log_attacker_defender_decided(context: duel.AttackerDefenderDecided.Context):
    BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=f"Warrior {context.attacker} is the attacker and warrior {context.defender} the defender.",
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
