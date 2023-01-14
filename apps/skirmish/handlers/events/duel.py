from apps.core.domain import message_registry
from apps.skirmish.messages.commands.duel import WarriorAttacksWarriorWithSimpleAttack
from apps.skirmish.messages.events import duel


@message_registry.register_event(event=duel.AttackerDefenderDecided)
def handle_attacker_defender_decided(context: duel.AttackerDefenderDecided.Context):
    if context.attack_action == 1:
        command = WarriorAttacksWarriorWithSimpleAttack.generator(
            context_data={
                "skirmish": context.skirmish,
                "attacker": context.attacker,
                "defender": context.defender,
                "attack_action": context.attack_action,
            }
        )
    else:
        raise RuntimeError("Invalid attack action")
    return [command]
