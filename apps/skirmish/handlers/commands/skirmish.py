import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.quest.models import QuestContract
from apps.skirmish.messages.commands import skirmish
from apps.skirmish.messages.events.skirmish import (
    AttackerDefenderDecided,
    FighterPairsMatched,
    RoundFinished,
    SkirmishCreated,
    SkirmishFinished,
)
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.skirmish.services.actions.utils import get_service_by_attack_action
from apps.skirmish.services.generators.skirmish.base import BaseSkirmishGenerator
from apps.skirmish.services.skirmish.assign_fighter_pairs import AssignFighterPairsService
from apps.skirmish.services.skirmish.damage import SkirmishDamageService
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_command(command=skirmish.CreateSkirmish)
def handle_create_skirmish(*, context: skirmish.CreateSkirmish) -> list[Event] | Event:
    if context.warrior_list_2:
        warrior_list_2 = context.warrior_list_2
    else:
        warrior_generator = MercenaryWarriorGenerator(
            faction=context.faction_2, culture=context.faction_2.culture, savegame_id=context.faction_1.savegame_id
        )
        warrior_list_2 = [
            warrior_generator.process()
            for _ in range(random.randrange(*context.quest_contract.quest.get_min_max_number_of_opponents()))
        ]

    skirmish_generator = BaseSkirmishGenerator(
        name=context.name,
        warriors_faction_1=context.warrior_list_1,
        warriors_faction_2=warrior_list_2,
    )
    new_skirmish = skirmish_generator.process()

    if context.quest_contract:
        context.quest_contract.skirmish = new_skirmish
        context.quest_contract.save()

    return SkirmishCreated(
        skirmish=new_skirmish,
        quest_contract=context.quest_contract,
    )


@message_registry.register_command(command=skirmish.StartDuel)
def handle_assign_fighter_pairs(*, context: skirmish.StartDuel) -> list[Event] | Event:
    message_list = []

    # Determine larger group
    assign_fighter_pairs_service = AssignFighterPairsService()
    skirmish_participants_1, skirmish_participants_2 = assign_fighter_pairs_service.determine_larger_group(
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
        participant_2: SkirmishParticipant = random.choice(skirmish_participants_2)
        used_warriors_from_list_2 += 1  # noqa: SIM113

        if not free_attack_due_to_being_more_numerous:
            message_list.append(
                FighterPairsMatched(
                    skirmish=context.skirmish,
                    warrior_1=participant_1.warrior,
                    warrior_2=participant_2.warrior,
                    attack_action_1=participant_1.skirmish_action,
                    attack_action_2=participant_2.skirmish_action,
                )
            )
        else:
            message_list.append(
                AttackerDefenderDecided(
                    skirmish=context.skirmish,
                    attacker=participant_1.warrior,
                    attacker_action=participant_1.skirmish_action,
                    defender=participant_2.warrior,
                    defender_action=participant_2.skirmish_action,
                )
            )

    return message_list


@message_registry.register_command(command=skirmish.DetermineAttacker)
def handle_determine_attacker_and_defender(*, context: skirmish.DetermineAttacker) -> list[Event] | Event:
    warrior_1_attack_action_service_class = get_service_by_attack_action(attack_action=context.action_1)
    warrior_2_attack_action_service_class = get_service_by_attack_action(attack_action=context.action_2)

    warrior_1_matching_points = warrior_1_attack_action_service_class.get_pair_matching_points(
        warrior_dexterity=context.warrior_1.dexterity
    )
    warrior_2_matching_points = warrior_2_attack_action_service_class.get_pair_matching_points(
        warrior_dexterity=context.warrior_2.dexterity
    )

    random_value = random.random()

    # Catch edge case that both have zero values
    if (
        warrior_1_matching_points + warrior_2_matching_points == 0
        or warrior_1_matching_points / (warrior_1_matching_points + warrior_2_matching_points) > random_value
    ):
        attacker: Warrior = context.warrior_1
        defender: Warrior = context.warrior_2
        attack_action = context.action_1
        defend_action = context.action_2
    else:
        attacker: Warrior = context.warrior_2
        defender: Warrior = context.warrior_1
        attack_action = context.action_2
        defend_action = context.action_1

    return AttackerDefenderDecided(
        skirmish=context.skirmish,
        attacker=attacker,
        attacker_action=attack_action,
        defender=defender,
        defender_action=defend_action,
    )


@message_registry.register_command(command=skirmish.WarriorAttacksWarrior)
def handle_warrior_attacks_warrior(
    *,
    context: skirmish.WarriorAttacksWarrior,
) -> list[Event] | Event:
    service = SkirmishDamageService(
        skirmish=context.skirmish,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        defender=context.defender,
        defender_action=context.defender_action,
    )
    return service.process()


@message_registry.register_command(command=skirmish.WinSkirmish)
def handle_faction_wins_skirmish(*, context: skirmish.WinSkirmish) -> list[Event] | Event:
    Skirmish.objects.set_victor(skirmish=context.skirmish, victorious_faction=context.victorious_faction)

    try:
        quest_contract = context.skirmish.quest_contract
        quest_name = quest_contract.quest.name
        quest_loot = quest_contract.quest.loot
    except QuestContract.ObjectDoesNotExist:
        # There might be skirmishes with no assigned quest contract
        # TODO: this shouldn't be handled here that explicitly -> model method?
        quest_name = None
        quest_loot = 0

    # The winner keeps the items from his dead warriors, but since it's easier they get "reassigned" to the victor,
    # thus himself.
    # Therefore, we reassign all dead victorious warriors items and all non-healthy defeated ones
    incapacitated_warriors = [
        *context.skirmish.player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_DEAD),
        *context.skirmish.non_player_warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_HEALTHY),
    ]

    # Fetch a list of unconscious, defeated warriors
    if context.skirmish.victorious_faction == context.skirmish.player_faction:
        defeated_unconscious_warriors = context.skirmish.non_player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
        )
    else:
        defeated_unconscious_warriors = context.skirmish.player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
        )

    # Fetch list of victorious, conscious warriors
    if context.skirmish.victorious_faction == context.skirmish.player_faction:
        victorious_conscious_warriors = context.skirmish.player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )
    else:
        victorious_conscious_warriors = context.skirmish.non_player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )

    # We need to evaluate the QS to avoid hitting the DB in the events
    return SkirmishFinished(
        skirmish=context.skirmish,
        incapacitated_warriors=incapacitated_warriors,
        defeated_unconscious_warriors=list(defeated_unconscious_warriors),
        victorious_conscious_warriors=list(victorious_conscious_warriors),
        month=context.month,
        quest_name=quest_name,
        quest_loot=quest_loot,
    )


@message_registry.register_command(command=skirmish.FinishRound)
def handle_finish_round(*, context: skirmish.FinishRound) -> list[Event] | Event:
    # Increment round
    Skirmish.objects.increment_round(skirmish=context.skirmish)

    # Check if one faction has been defeated
    victor = None
    if not context.skirmish.non_player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        victor = context.skirmish.player_faction
    if not context.skirmish.player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        victor = context.skirmish.non_player_faction

    return RoundFinished(skirmish=context.skirmish, victor=victor, month=context.month)
