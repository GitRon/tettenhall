import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.quest.models import QuestContract
from apps.skirmish.messages.commands import skirmish
from apps.skirmish.messages.events.skirmish import (
    AttackerDefenderDecided,
    FactionWasAttacked,
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


@message_registry.register_command(command=skirmish.AttackFaction)
def handle_attack_faction(*, context: skirmish.AttackFaction) -> list[Event] | Event:
    # Whom the rival fields is a query, so it is answered here rather than in the event handler that
    # turns this into a skirmish - strict mode blocks the database there. Only the ones still on
    # their feet turn out: a warrior who is down does not defend his town, and an unhealthy side
    # would count as beaten before the first round.
    defending_warriors = list(Warrior.objects.filter_healthy().filter_faction(faction_id=context.target_faction.id))

    return FactionWasAttacked(
        attacking_faction=context.attacking_faction,
        defending_faction=context.target_faction,
        attacking_warriors=list(context.assigned_warriors),
        defending_warriors=defending_warriors,
        month=context.month,
    )


@message_registry.register_command(command=skirmish.CreateSkirmish)
def handle_create_skirmish(*, context: skirmish.CreateSkirmish) -> list[Event] | Event:
    # Both rosters arrive resolved. Whom a faction fields is its own business and is answered by the
    # command handler that raised the event leading here - handle_attack_faction for a march,
    # handle_accept_quest for an errand - so there is exactly one answer to it and this only stages
    # the fight.
    skirmish_generator = BaseSkirmishGenerator(
        name=context.name,
        warriors_faction_1=context.warrior_list_1,
        warriors_faction_2=context.warrior_list_2,
        month=context.month,
    )
    new_skirmish = skirmish_generator.process()

    # Linking the contract to the skirmish is the quest app's reaction to SkirmishCreated, see
    # handle_link_quest_contract_to_its_skirmish - writing it here as well meant doing it twice
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


def _scaled_quest_loot(*, quest_contract: QuestContract, skirmish: Skirmish) -> int:
    """
    What the contract actually pays, given how thin a war band the target turned out to be.

    The money follows the opposition rather than the opposition being padded to fit the money: the
    difficulty says how many of the rival's warriors turn out, and a hard quest against a faction
    that can field two men is an easy fight and pays like one. "Quest.loot" is therefore a ceiling
    rather than a promise, measured against the top of the difficulty band.

    Never an undersell: the turnout is drawn from that same band, so the ratio is one at a full
    muster and less below it. And never a number the player is disappointed against either - the
    quest board runs the loot through "obscurify", so what was advertised was "High", not a figure.
    """
    _, band_maximum = quest_contract.quest.get_min_max_number_of_opponents()

    return round(quest_contract.quest.loot * skirmish.defending_warriors.count() / band_maximum)


@message_registry.register_command(command=skirmish.WinSkirmish)
def handle_faction_wins_skirmish(*, context: skirmish.WinSkirmish) -> list[Event] | Event:
    Skirmish.objects.set_victor(skirmish=context.skirmish, victorious_faction=context.victorious_faction)

    try:
        quest_contract = context.skirmish.quest_contract
        quest_name = quest_contract.quest.name
        # A quest only pays the faction that signed the contract, and only if it actually won: the
        # reward is handed to the victor further down the chain, so carrying it regardless of the
        # outcome funded the rival who beat you out of your own quest. Decided here rather than in
        # the finance handler because reading the contract's faction is a query, which strict mode
        # forbids in an event handler.
        if quest_contract.faction_id == context.victorious_faction.pk:
            quest_loot = _scaled_quest_loot(quest_contract=quest_contract, skirmish=context.skirmish)
        else:
            quest_loot = 0
    except QuestContract.DoesNotExist:
        # There might be skirmishes with no assigned quest contract
        # TODO: this shouldn't be handled here that explicitly -> model method?
        quest_name = None
        quest_loot = 0

    # Everything below is about the winner and the loser, so the two sides get sorted into those
    # roles exactly once - "attacking_warriors" and "defending_warriors" only coincide with them when
    # the side that marched is the side that won
    if context.skirmish.victorious_faction == context.skirmish.attacking_faction:
        victorious_warriors = context.skirmish.attacking_warriors
        defeated_warriors = context.skirmish.defending_warriors
    else:
        victorious_warriors = context.skirmish.defending_warriors
        defeated_warriors = context.skirmish.attacking_warriors

    # Only a warrior left lying on the field can be stripped: the dead and the unconscious. One who
    # fled took his kit with him, so a warband that merely routs loses nothing but the fight. That
    # distinction matters more than it looks: a defeat is declared exactly when nobody on that side
    # is healthy any more, so "everyone not healthy" would have meant the whole roster, not its
    # casualties.
    defeated_warriors_on_the_field = list(
        defeated_warriors.filter(
            condition__in=(
                Warrior.ConditionChoices.CONDITION_DEAD,
                Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
            )
        )
    )

    # The winner's own dead take the same route, reassigned to the victor - who is their own faction,
    # so it amounts to their gear returning to the stash. His unconscious survive and keep theirs.
    incapacitated_warriors = [
        *victorious_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_DEAD),
        *defeated_warriors_on_the_field,
    ]

    # The unconscious among them are the ones taken prisoner, and are already loaded above
    defeated_unconscious_warriors = [warrior for warrior in defeated_warriors_on_the_field if warrior.is_unconscious]

    # Only the ones still standing when it was over share in the victory: a warrior who was knocked
    # out or lost his nerve did not see the fight through, and in a mutual wipeout nobody did
    victorious_healthy_warriors = victorious_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY)

    # We need to evaluate the QS to avoid hitting the DB in the events
    return SkirmishFinished(
        skirmish=context.skirmish,
        incapacitated_warriors=incapacitated_warriors,
        defeated_unconscious_warriors=defeated_unconscious_warriors,
        victorious_healthy_warriors=list(victorious_healthy_warriors),
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
    if not context.skirmish.defending_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        # Checked first on purpose: if both sides are wiped out in the same round, the tie goes to
        # the side that marched
        victor = context.skirmish.attacking_faction
    elif not context.skirmish.attacking_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        victor = context.skirmish.defending_faction

    return RoundFinished(skirmish=context.skirmish, victor=victor, month=context.month)
