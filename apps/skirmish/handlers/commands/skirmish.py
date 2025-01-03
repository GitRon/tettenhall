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
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.skirmish.services.actions.simple_attack import SimpleAttackService
from apps.skirmish.services.generators.skirmish.base import BaseSkirmishGenerator
from apps.skirmish.services.skirmish.assign_fighter_pairs import AssignFighterPairsService


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

    # Determine larger group
    assign_fighter_pairs_service = AssignFighterPairsService()
    skirmish_participants_1, skirmish_participants_2 = assign_fighter_pairs_service.determine_attacker_and_defenders(
        skirmish_participants_1=context.skirmish_participants_1, skirmish_participants_2=context.skirmish_participants_2
    )

    # Shuffle both lists to have more interaction going on
    random.shuffle(skirmish_participants_1)
    random.shuffle(skirmish_participants_2)

    # This flag indicates when warriors from list 1 are more numerous, and so they can attack the other side without
    # to decide who attacks first. Having more guys will result in a free attack.
    used_warriors_from_list_2 = 0
    free_attack_due_to_being_more_numerous = False

    # For every warrior in list 1...
    participant_1: SkirmishParticipant
    for participant_1 in skirmish_participants_1:
        # If list 2 is shorter, list 1 warriors get matched again
        if used_warriors_from_list_2 == len(skirmish_participants_2):
            free_attack_due_to_being_more_numerous = True

        # Fetch a random defender
        # TODO: one warrior might get hit multiple times without the free attacks -> do we want this?
        participant_2: SkirmishParticipant = random.choice(skirmish_participants_2)
        used_warriors_from_list_2 += 1  # noqa: SIM113

        if not free_attack_due_to_being_more_numerous:
            message_list.append(
                FighterPairsMatched(
                    FighterPairsMatched.Context(
                        skirmish=context.skirmish,
                        warrior_1=participant_1.warrior,
                        warrior_2=participant_2.warrior,
                        attack_action_1=participant_1.skirmish_action,
                        attack_action_2=participant_2.skirmish_action,
                    )
                )
            )
        else:
            message_list.append(
                AttackerDefenderDecided(
                    AttackerDefenderDecided.Context(
                        skirmish=context.skirmish,
                        attacker=participant_1.warrior,
                        defender=participant_2.warrior,
                        attack_action=participant_1.skirmish_action,
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
