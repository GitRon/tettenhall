import random

from apps.core.domain import message_registry
from apps.skirmish.messages.commands import duel
from apps.skirmish.messages.events.duel import AttackerDefenderDecided, FighterPairsMatched
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.fight_actions.risky_attack import RiskyAttackService
from apps.skirmish.services.fight_actions.simple_attack import SimpleAttackService


@message_registry.register_command(command=duel.StartDuel)
def handle_assign_fighter_pairs(context: duel.StartDuel.Context) -> list:
    message_list = []

    # The larger list is always the first
    if len(context.warrior_list_1) >= len(context.warrior_list_2):
        warrior_list_1 = context.warrior_list_1
        warrior_list_2 = context.warrior_list_2
    else:
        warrior_list_1 = context.warrior_list_2
        warrior_list_2 = context.warrior_list_1

    used_warriors_list_2 = []

    for warrior_1, attack_action_1 in warrior_list_1.items():
        # If list 2 is shorter, the warriors get matched again
        # # todo change to: get just hit, and cannot try to attack (create different event)
        if len(used_warriors_list_2) == len(warrior_list_2):
            used_warriors_list_2 = []

        warrior_2 = random.choice(list(warrior_list_2.keys()))
        attack_action_2 = warrior_list_2[warrior_2]
        used_warriors_list_2.append(warrior_2)

        message_list.append(
            FighterPairsMatched.generator(
                context_data={
                    "skirmish": context.skirmish,
                    "warrior_1": Warrior.objects.get(id=warrior_1),
                    "warrior_2": Warrior.objects.get(id=warrior_2),
                    "attack_action_1": attack_action_1,
                    "attack_action_2": attack_action_2,
                }
            )
        )

    return message_list


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
def handle_warrior_attacks_warrior_with_simple_attack(
    context: duel.WarriorAttacksWarriorWithSimpleAttack.Context,
) -> list:
    service = SimpleAttackService(context=context)
    return service.process()


@message_registry.register_command(command=duel.WarriorAttacksWarriorWithRiskyAttack)
def handle_warrior_attacks_warrior_with_risky_attack(
    context: duel.WarriorAttacksWarriorWithRiskyAttack.Context,
) -> list:
    service = RiskyAttackService(context=context)
    return service.process()
