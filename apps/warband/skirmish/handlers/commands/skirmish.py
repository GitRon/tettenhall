import random

from queuebie import message_registry
from queuebie.messages import Command, Event

from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.messages.commands import skirmish
from apps.warband.skirmish.messages.commands.skirmish import WarriorAssaultsFortification
from apps.warband.skirmish.messages.commands.warrior import (
    RallyRemainingWarriors,
    StoreLastUsedSkirmishAction,
    WithdrawFromSkirmish,
)
from apps.warband.skirmish.messages.events.skirmish import (
    AttackerDefenderDecided,
    FactionWasAttacked,
    FighterPairsMatched,
    FortificationAssaulted,
    FortificationFell,
    RoundFinished,
    SkirmishCreated,
    SkirmishFinished,
)
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.warband.skirmish.services.actions.assault_fortification import AssaultFortificationService
from apps.warband.skirmish.services.actions.utils import get_service_by_attack_action
from apps.warband.skirmish.services.generators.skirmish.base import BaseSkirmishGenerator
from apps.warband.skirmish.services.skirmish.assign_fighter_pairs import AssignFighterPairsService
from apps.warband.skirmish.services.skirmish.damage import SkirmishDamageService


@message_registry.register_command(command=skirmish.AttackFaction)
def handle_attack_faction(*, context: skirmish.AttackFaction) -> list[Event] | Event:
    # Whom the rival fields is a query, so it is answered here rather than in the event handler that
    # turns this into a skirmish - strict mode blocks the database there. Only the ones still on
    # their feet turn out: a warrior who is down does not defend his town, and an unhealthy side
    # would count as beaten before the first round.
    #
    # And only the ones not already in a fight, the same rule the quest muster applies. A defender
    # standing in two open skirmishes strands whichever is resolved second: the side that lost him
    # has nobody healthy left to post, so it cannot be played out, and the month refuses to turn
    # while a skirmish is open. "attackable_targets" asks this same question, so a target that
    # reaches here has somebody to field.
    defending_warriors = list(
        Warrior.objects.filter_healthy()
        .filter_faction(faction_id=context.target_faction.id)
        .exclude_currently_busy(month=context.month)
    )

    return FactionWasAttacked(
        attacking_faction=context.attacking_faction,
        defending_faction=context.target_faction,
        attacking_warriors=list(context.assigned_warriors),
        defending_warriors=defending_warriors,
        fortification_strength=context.target_faction.town.get_fortification_strength(),
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
        fortification_strength=context.fortification_strength,
    )
    new_skirmish = skirmish_generator.process()

    # Linking the contract to the skirmish is the quest app's reaction to SkirmishCreated, see
    # handle_link_quest_contract_to_its_skirmish - writing it here as well meant doing it twice
    return SkirmishCreated(
        skirmish=new_skirmish,
        quest_contract=context.quest_contract,
    )


def _withdrawing_and_remaining(
    *, skirmish: Skirmish, participants: list[SkirmishParticipant]
) -> tuple[list[Command], list[SkirmishParticipant]]:
    """
    Splits one side into the orders to walk away and the men who are still in the fight.

    Flight is answered here rather than by a service of its own under "services/actions/", because it
    is the one action that is not something a warrior does to somebody: it removes him from the round
    before there is anyone to do it to, so it never reaches "get_service_by_attack_action".
    """
    withdrawals = []
    remaining = []

    for participant in participants:
        if participant.skirmish_action == SkirmishActionChoices.FLEE:
            withdrawals.append(WithdrawFromSkirmish(skirmish=skirmish, warrior=participant.warrior))
        else:
            remaining.append(participant)

    return withdrawals, remaining


def _assaults(*, skirmish: Skirmish, round_number: int, participants: list[SkirmishParticipant]) -> list[Command]:
    """
    One order per man who spends this round on the wall.

    He stays in the pairing all the same: storming a gate does not take him out of reach of the man
    in front of it, so he is still paired and still takes his opponent's blow. What he does not do is
    swing at that opponent - his action yields no matching points, so he is never his pair's attacker.
    """
    return [
        WarriorAssaultsFortification(skirmish=skirmish, round_number=round_number, warrior=participant.warrior)
        for participant in participants
        if participant.skirmish_action == SkirmishActionChoices.ASSAULT_FORTIFICATION
    ]


def _rallies(*, skirmish: Skirmish, participants: list[SkirmishParticipant]) -> list[Command]:
    """
    The order to steady the side, for a leader who spends this round on it.

    Like the wall-stormer he stays in the pairing and still takes his opponent's blow - what he gives
    up is his swing, which "RallyService" answers. The steadying is raised here because an action
    service returns a roll and cannot emit.
    """
    return [
        RallyRemainingWarriors(skirmish=skirmish, leader=participant.warrior)
        for participant in participants
        if participant.skirmish_action == SkirmishActionChoices.RALLY
    ]


@message_registry.register_command(command=skirmish.StartDuel)
def handle_assign_fighter_pairs(*, context: skirmish.StartDuel) -> list[Command | Event]:
    # Everyone ordered off the field leaves before anybody is matched, and the orders are returned
    # ahead of the pairings so the battle log reads in the order the round happened: a man walks away,
    # and then the blows he is not there for are struck. The runner routes each message on its own
    # type, so commands and events travelling together is no different from returning either alone.
    withdrawals_1, participants_1 = _withdrawing_and_remaining(
        skirmish=context.skirmish, participants=context.skirmish_participants_1
    )
    withdrawals_2, participants_2 = _withdrawing_and_remaining(
        skirmish=context.skirmish, participants=context.skirmish_participants_2
    )
    message_list = [*withdrawals_1, *withdrawals_2]

    # A side the retreat emptied has nobody left to pair, and the matching below picks a random
    # opponent out of the other list - which raises on an empty one. Leaving with the orders alone is
    # the whole of this round: "handle_finish_round" counts healthy warriors, and a side that walked
    # off has none, so the fight is lost by the men who left it rather than by a special case here.
    if len(participants_1) == 0 or len(participants_2) == 0:
        return message_list

    # Read once, here, and carried on every message the round produces. This is the handler that
    # starts the round, so "current_round" is the round being fought by definition rather than by
    # ordering luck - and it is the last point at which that is true, because "FinishRound"
    # increments and saves before any of the events below are handled
    round_number = context.skirmish.current_round

    # The assaults go out ahead of the pairings, and they land ahead of every blow of the round too:
    # each is resolved by its own command, one hop, where a blow at a man is three hops down from its
    # pairing. So a wall that falls this round no longer shields anybody from this round's blows, and
    # the log says the wall came down before it says who struck whom.
    message_list.extend(_assaults(skirmish=context.skirmish, round_number=round_number, participants=participants_1))
    message_list.extend(_assaults(skirmish=context.skirmish, round_number=round_number, participants=participants_2))

    # The rallies go out ahead of the pairings for the same reason, and behind the withdrawals, so the
    # men who walked off this round are already gone when the leader looks round for whom to steady
    message_list.extend(_rallies(skirmish=context.skirmish, participants=participants_1))
    message_list.extend(_rallies(skirmish=context.skirmish, participants=participants_2))

    # Determine larger group
    assign_fighter_pairs_service = AssignFighterPairsService()
    skirmish_participants_1, skirmish_participants_2 = assign_fighter_pairs_service.determine_larger_group(
        skirmish_participants_1=participants_1, skirmish_participants_2=participants_2
    )

    # Shuffle both lists to have more interaction going on. It is what decides whom each man faces:
    # the two lists are then walked in step, so the order they are in is the pairing.
    random.shuffle(skirmish_participants_1)
    random.shuffle(skirmish_participants_2)

    # For every warrior in the larger group...
    index: int
    participant_1: SkirmishParticipant
    participant_2: SkirmishParticipant
    for index, participant_1 in enumerate(skirmish_participants_1):
        if index < len(skirmish_participants_2):
            # One opponent each, in the order the shuffle left them in. Matching them off rather than
            # drawing means three men a side are three fights, and not the same man struck three times
            # while two of his are never touched.
            participant_2 = skirmish_participants_2[index]

            message_list.append(
                FighterPairsMatched(
                    skirmish=context.skirmish,
                    round_number=round_number,
                    warrior_1=participant_1.warrior,
                    warrior_2=participant_2.warrior,
                    attack_action_1=participant_1.skirmish_action,
                    attack_action_2=participant_2.skirmish_action,
                )
            )
        elif participant_1.skirmish_action in (
            SkirmishActionChoices.ASSAULT_FORTIFICATION,
            SkirmishActionChoices.RALLY,
        ):
            # Nobody is left to face a man at the wall or a leader rallying, and neither is looking for
            # anybody: his round is the order above, and there is no man for him to strike free at.
            # No exchange means nothing else records what he did, so his card would open the next
            # round on the default instead of on the order he keeps giving
            message_list.append(
                StoreLastUsedSkirmishAction(
                    skirmish=context.skirmish,
                    warrior=participant_1.warrior,
                    skirmish_action=participant_1.skirmish_action,
                )
            )
        else:
            # The smaller group has run out, so this man is one the other side cannot field anybody
            # against and he strikes unopposed. Whom he falls on is the one draw in the round that may
            # repeat, because he is by definition a man more than there are opponents to go round.
            participant_2 = random.choice(skirmish_participants_2)

            message_list.append(
                AttackerDefenderDecided(
                    skirmish=context.skirmish,
                    round_number=round_number,
                    attacker=participant_1.warrior,
                    attacker_action=participant_1.skirmish_action,
                    defender=participant_2.warrior,
                    defender_action=participant_2.skirmish_action,
                    initiative=InitiativeChoices.INITIATIVE_UNOPPOSED,
                )
            )

    return message_list


@message_registry.register_command(command=skirmish.DetermineAttacker)
def handle_determine_attacker_and_defender(*, context: skirmish.DetermineAttacker) -> list[Event] | Event:
    warrior_1_attack_action_service_class = get_service_by_attack_action(attack_action=context.action_1)
    warrior_2_attack_action_service_class = get_service_by_attack_action(attack_action=context.action_2)

    # The effective dexterity, so a lame man loses the initiative he no longer has - the other half
    # of what an injury costs him, beside the weaker swing
    warrior_1_matching_points = warrior_1_attack_action_service_class.get_pair_matching_points(
        warrior_dexterity=context.warrior_1.effective_dexterity
    )
    warrior_2_matching_points = warrior_2_attack_action_service_class.get_pair_matching_points(
        warrior_dexterity=context.warrior_2.effective_dexterity
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
        round_number=context.round_number,
        attacker=attacker,
        attacker_action=attack_action,
        defender=defender,
        defender_action=defend_action,
        initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
    )


@message_registry.register_command(command=skirmish.WarriorAttacksWarrior)
def handle_warrior_attacks_warrior(
    *,
    context: skirmish.WarriorAttacksWarrior,
) -> list[Event] | Event:
    service = SkirmishDamageService(
        skirmish=context.skirmish,
        round_number=context.round_number,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        defender=context.defender,
        defender_action=context.defender_action,
    )
    return service.process()


@message_registry.register_command(command=skirmish.WarriorAssaultsFortification)
def handle_warrior_assaults_fortification(*, context: skirmish.WarriorAssaultsFortification) -> list[Event]:
    assault = AssaultFortificationService(skirmish=context.skirmish, warrior=context.warrior).get_assault_value()
    had_a_wall = context.skirmish.is_fortified

    damage = Skirmish.objects.batter_fortification(skirmish=context.skirmish, damage=assault.value)

    message_list: list[Event] = [
        FortificationAssaulted(
            skirmish=context.skirmish,
            round_number=context.round_number,
            warrior=context.warrior,
            assault=assault,
            damage=damage,
            remaining_strength=context.skirmish.fortification_strength,
        )
    ]
    # The fall is its own fact, and it happens once: to the swing that took the last of it, not to a
    # second man storming the same round what the first one already brought down
    if had_a_wall and not context.skirmish.is_fortified:
        message_list.append(
            FortificationFell(skirmish=context.skirmish, round_number=context.round_number, warrior=context.warrior)
        )

    return message_list


@message_registry.register_command(command=skirmish.WinSkirmish)
def handle_faction_wins_skirmish(*, context: skirmish.WinSkirmish) -> list[Event] | Event | None:
    # A fight is won once. The manager refuses a skirmish that already has a victor, and stopping here
    # is what keeps the silver, the experience, the quest reward and the log line to a single helping:
    # the savegame ending force-resolves the very fight it ended in, so the round that ended it arrives
    # behind a victory that has already been paid out.
    if not Skirmish.objects.set_victor(skirmish=context.skirmish, victorious_faction=context.victorious_faction):
        return None

    quest_name, quest_loot = context.skirmish.quest_reward_for(victorious_faction=context.victorious_faction)

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
    # Read before the increment: this is the round that just resolved, and it is what the battle log
    # names. Afterwards "current_round" points at the round nobody has fought yet
    finished_round = context.skirmish.current_round

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

    return RoundFinished(skirmish=context.skirmish, round_number=finished_round, victor=victor, month=context.month)
