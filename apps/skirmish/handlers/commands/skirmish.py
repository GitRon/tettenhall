import random

from apps.core.domain import message_registry
from apps.core.event_loop.messages import Event
from apps.skirmish.messages.commands import skirmish
from apps.skirmish.messages.events.skirmish import (
    AttackerDefenderDecided,
    FighterPairsMatched,
    SkirmishCreated,
    SkirmishFinished,
)
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.skirmish.services.actions.simple_attack import SimpleAttackService
from apps.skirmish.services.generators.skirmish.base import BaseSkirmishGenerator


@message_registry.register_command(command=skirmish.CreateSkirmish)
def handle_create_skirmish(*, context: skirmish.CreateSkirmish.Context) -> list[Event] | Event:
    skirmish_generator = BaseSkirmishGenerator(
        name=context.name,
        warriors_faction_1=context.warrior_list_1,
        warriors_faction_2=context.warrior_list_2,
    )
    new_skirmish = skirmish_generator.process()

    if context.quest_contract:
        context.quest_contract.skirmish = new_skirmish
        context.quest_contract.save()

    return SkirmishCreated(
        context=SkirmishCreated.Context(
            skirmish=new_skirmish,
            quest_contract=context.quest_contract,
        )
    )


@message_registry.register_command(command=skirmish.StartDuel)
def handle_assign_fighter_pairs(*, context: skirmish.StartDuel.Context) -> list[Event] | Event:
    message_list = []

    # TODO: we need to start here looking at the skirmish actions to be able to affect pairing, defense etc,
    #  not just attack value.

    # The larger list is always the first
    if len(context.warrior_list_1) >= len(context.warrior_list_2):
        warrior_list_1 = context.warrior_list_1
        warrior_list_2 = context.warrior_list_2
    else:
        warrior_list_1 = context.warrior_list_2
        warrior_list_2 = context.warrior_list_1

    used_warriors_list_2 = []

    # Ensure that all lists contain warriors (todo: might be redundant at some point)
    if len(warrior_list_1) == 0 or len(warrior_list_2) == 0:
        return []

    # This flag indicates when warriors from list 1 are more numerous, and so they can attack the other side without
    # to decide who attacks first. Having more guys will result in a free attack.
    double_warriors = False
    # TODO: shuffle the list somehow so there is more interaction going on
    for warrior_1, attack_action_1 in warrior_list_1.items():
        # If list 2 is shorter, the warriors get matched again
        if len(used_warriors_list_2) == len(warrior_list_2):
            double_warriors = True
            used_warriors_list_2 = []

        warrior_2 = random.choice(list(warrior_list_2.keys()))
        attack_action_2 = warrior_list_2[warrior_2]
        used_warriors_list_2.append(warrior_2)

        # TODO: hier stimmt was nicht, der player-warrior hat auch angegriffen
        if not double_warriors:
            message_list.append(
                FighterPairsMatched(
                    FighterPairsMatched.Context(
                        skirmish=context.skirmish,
                        warrior_1=Warrior.objects.get(id=warrior_1),
                        warrior_2=Warrior.objects.get(id=warrior_2),
                        attack_action_1=attack_action_1,
                        attack_action_2=attack_action_2,
                    )
                )
            )
        else:
            message_list.append(
                AttackerDefenderDecided(
                    AttackerDefenderDecided.Context(
                        skirmish=context.skirmish,
                        attacker=Warrior.objects.get(id=warrior_1),
                        defender=Warrior.objects.get(id=warrior_2),
                        attack_action=attack_action_1,
                    )
                )
            )

    return message_list


@message_registry.register_command(command=skirmish.DetermineAttacker)
def handle_determine_attacker_and_defender(*, context: skirmish.DetermineAttacker.Context) -> list[Event] | Event:
    # TODO: bug: 2 warriors, the weak one is faster
    #  -> it never ends because strong warrior never is able to hit but other one never makes damage
    #  -> thous dexterity seems to be imba
    #  -> maybe make the defender hit back immediately? So dex lets you hit first but you'll get a hit back?

    random_value = random.random()

    if context.warrior_1.dexterity / (context.warrior_1.dexterity + context.warrior_2.dexterity) > random_value:
        attacker: Warrior = context.warrior_1
        defender: Warrior = context.warrior_2
        attack_action = context.action_1
    else:
        attacker: Warrior = context.warrior_2
        defender: Warrior = context.warrior_1
        attack_action = context.action_2

    return AttackerDefenderDecided(
        AttackerDefenderDecided.Context(
            skirmish=context.skirmish,
            attacker=attacker,
            defender=defender,
            attack_action=attack_action,
        )
    )


@message_registry.register_command(command=skirmish.WarriorAttacksWarriorWithSimpleAttack)
def handle_warrior_attacks_warrior_with_simple_attack(
    *,
    context: skirmish.WarriorAttacksWarriorWithSimpleAttack.Context,
) -> list[Event] | Event:
    service = SimpleAttackService(context=context)
    return service.process()


@message_registry.register_command(command=skirmish.WarriorAttacksWarriorWithRiskyAttack)
def handle_warrior_attacks_warrior_with_risky_attack(
    *,
    context: skirmish.WarriorAttacksWarriorWithRiskyAttack.Context,
) -> list[Event] | Event:
    service = RiskyAttackService(context=context)
    return service.process()


@message_registry.register_command(command=skirmish.WarriorAttacksWarriorWithFastAttack)
def handle_warrior_attacks_warrior_with_fast_attack(
    *,
    context: skirmish.WarriorAttacksWarriorWithRiskyAttack.Context,
) -> list[Event] | Event:
    # TODO: implement me -> how can I alter the warrior matching here? too late, right?
    # service = RiskyAttackService(context=context)
    # return service.process()
    return []


@message_registry.register_command(command=skirmish.WinSkirmish)
def handle_faction_wins_skirmish(*, context: skirmish.WinSkirmish.Context) -> list[Event] | Event:
    Skirmish.objects.set_victor(skirmish=context.skirmish, victorious_faction=context.victorious_faction)

    return SkirmishFinished(SkirmishFinished.Context(skirmish=context.skirmish))
