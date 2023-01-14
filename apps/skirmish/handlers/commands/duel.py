import random

from apps.core.domain import message_registry
from apps.core.domain.random import DiceNotation
from apps.skirmish.messages.commands import duel
from apps.skirmish.messages.events.duel import AttackerDefenderDecided
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage, WarriorDefendedDamage, WarriorTookDamage
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=duel.DetermineAttacker)
def handle_determine_attacker_and_defender(context: duel.DetermineAttacker.Context) -> list:
    random_value = random.random()

    if context.warrior_1.dexterity / (context.warrior_1.dexterity + context.warrior_2.dexterity) > random_value:
        attacker: Warrior = context.warrior_1
        defender: Warrior = context.warrior_2
        attack_action = context.action_1
    else:
        attacker: Warrior = context.warrior_2
        defender: Warrior = context.warrior_1
        attack_action = context.action_2

    return [
        AttackerDefenderDecided.generator(
            context_data={
                "skirmish": context.skirmish,
                "attacker": attacker,
                "defender": defender,
                "attack_action": attack_action,
            }
        )
    ]


@message_registry.register_command(command=duel.WarriorAttacksWarriorWithSimpleAttack)
def handle_warrior_attacks_warrior_with_attack_action(
    context: duel.WarriorAttacksWarriorWithSimpleAttack.Context,
) -> list:
    message_list = []

    attack = DiceNotation(dice_string=context.attacker.weapon.value).result
    message_list.append(
        WarriorAttackedWithDamage.generator(
            {"skirmish": context.skirmish, "warrior": context.attacker, "damage": attack}
        )
    )

    defense = DiceNotation(dice_string=context.defender.armor.value).result
    message_list.append(
        WarriorDefendedDamage.generator({"skirmish": context.skirmish, "warrior": context.defender, "damage": defense})
    )

    damage = max(attack - defense, 0)

    message_list.append(
        WarriorTookDamage.generator(
            {
                "skirmish": context.skirmish,
                "attacker": context.attacker,
                "attacker_damage": attack,
                "defender": context.defender,
                "defender_damage": defense,
                "damage": damage,
            }
        )
    )

    return message_list
