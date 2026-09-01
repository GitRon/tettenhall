from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest import Quest
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.handlers.commands.skirmish import (
    handle_assign_fighter_pairs,
    handle_attack_faction,
    handle_create_skirmish,
    handle_determine_attacker_and_defender,
    handle_faction_wins_skirmish,
    handle_finish_round,
)
from apps.skirmish.messages.commands.skirmish import (
    AttackFaction,
    CreateSkirmish,
    DetermineAttacker,
    FinishRound,
    StartDuel,
    WinSkirmish,
)
from apps.skirmish.messages.events.skirmish import (
    AttackerDefenderDecided,
    FactionWasAttacked,
    FighterPairsMatched,
    RoundFinished,
    SkirmishFinished,
)
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_attack_faction_fields_the_targets_own_warriors():
    """
    The point of the whole story: the defending side is the rival's actual war band, its leader
    among them, rather than mercenaries invented for the occasion.
    """
    attacking_faction = FactionFactory()
    target_faction = FactionFactory(savegame=attacking_faction.savegame)
    attacking_leader = WarriorFactory(faction=attacking_faction)
    target_leader = WarriorFactory(faction=target_faction)
    target_faction.leader = target_leader
    target_faction.save()

    result = handle_attack_faction(
        context=AttackFaction(
            attacking_faction=attacking_faction,
            target_faction=target_faction,
            assigned_warriors=[attacking_leader],
            month=3,
        )
    )

    assert result == FactionWasAttacked(
        attacking_faction=attacking_faction,
        defending_faction=target_faction,
        attacking_warriors=[attacking_leader],
        defending_warriors=[target_leader],
        month=3,
    )


@pytest.mark.django_db
def test_handle_attack_faction_leaves_the_targets_casualties_out_of_the_line_up():
    """
    A warrior who is down does not turn out to defend his town - and a side made up of him alone
    would count as beaten before the first round.
    """
    attacking_faction = FactionFactory()
    target_faction = FactionFactory(savegame=attacking_faction.savegame)
    healthy_defender = WarriorFactory(faction=target_faction)
    WarriorFactory(faction=target_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_attack_faction(
        context=AttackFaction(
            attacking_faction=attacking_faction,
            target_faction=target_faction,
            assigned_warriors=[WarriorFactory(faction=attacking_faction)],
            month=3,
        )
    )

    assert result.defending_warriors == [healthy_defender]


@pytest.mark.django_db
def test_handle_attack_faction_leaves_out_a_defender_already_in_a_fight():
    """
    Every warrior fights once a month, defenders included. Two open skirmishes sharing a defender is a
    savegame that cannot be finished: resolving one leaves the other with nobody healthy to post, and
    the month will not turn while a skirmish is open.
    """
    attacking_faction = FactionFactory()
    target_faction = FactionFactory(savegame=attacking_faction.savegame)
    available_defender = WarriorFactory(faction=target_faction)
    committed_defender = WarriorFactory(faction=target_faction)
    SkirmishFactory(defending_faction=target_faction).defending_warriors.add(committed_defender)

    result = handle_attack_faction(
        context=AttackFaction(
            attacking_faction=attacking_faction,
            target_faction=target_faction,
            assigned_warriors=[WarriorFactory(faction=attacking_faction)],
            month=1,
        )
    )

    assert result.defending_warriors == [available_defender]


@pytest.mark.django_db
def test_handle_create_skirmish_uses_the_given_opponents():
    quest_contract = QuestContractFactory()
    attacking_warrior = WarriorFactory(faction=quest_contract.faction)
    enemy_warrior = WarriorFactory(faction=quest_contract.quest.target_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=quest_contract.faction,
            faction_2=quest_contract.quest.target_faction,
            warrior_list_1=[attacking_warrior],
            warrior_list_2=[enemy_warrior],
            month=3,
            quest_contract=quest_contract,
        )
    )

    assert list(result.skirmish.attacking_warriors.all()) == [attacking_warrior]
    assert list(result.skirmish.defending_warriors.all()) == [enemy_warrior]


@pytest.mark.django_db
def test_handle_create_skirmish_records_the_month():
    """
    A skirmish had nowhere to say which month it belongs to, and the cap on attacking the same rival
    twice has nothing else to go on.
    """
    quest_contract = QuestContractFactory()
    attacking_warrior = WarriorFactory(faction=quest_contract.faction)
    enemy_warrior = WarriorFactory(faction=quest_contract.quest.target_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=quest_contract.faction,
            faction_2=quest_contract.quest.target_faction,
            warrior_list_1=[attacking_warrior],
            warrior_list_2=[enemy_warrior],
            month=7,
            quest_contract=quest_contract,
        )
    )

    assert result.skirmish.month == 7


@pytest.mark.django_db
def test_handle_create_skirmish_refuses_an_empty_defending_side():
    """
    Nobody is conjured to fill the gap any more, so a side that fields nobody is a fight that cannot
    be staged. What keeps it unreachable is who may be targeted at all - "Quest.objects.resolvable()"
    for an errand, "attackable_targets" for a march.
    """
    attacking_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=attacking_faction.savegame)
    attacking_warrior = WarriorFactory(faction=attacking_faction)

    with pytest.raises(RuntimeError, match="no warriors on the defending side"):
        handle_create_skirmish(
            context=CreateSkirmish(
                name="Brawl",
                faction_1=attacking_faction,
                faction_2=enemy_faction,
                warrior_list_1=[attacking_warrior],
                warrior_list_2=[],
                month=3,
                quest_contract=None,
            )
        )


@pytest.mark.django_db
def test_handle_create_skirmish_passes_the_quest_contract_on():
    quest_contract = QuestContractFactory()
    attacking_warrior = WarriorFactory(faction=quest_contract.faction)
    enemy_warrior = WarriorFactory(faction=quest_contract.quest.target_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=quest_contract.faction,
            faction_2=quest_contract.quest.target_faction,
            warrior_list_1=[attacking_warrior],
            warrior_list_2=[enemy_warrior],
            month=3,
            quest_contract=quest_contract,
        )
    )

    assert result.quest_contract == quest_contract


@pytest.mark.django_db
def test_handle_create_skirmish_without_a_quest_contract():
    attacking_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=attacking_faction.savegame)
    attacking_warrior = WarriorFactory(faction=attacking_faction)
    enemy_warrior = WarriorFactory(faction=enemy_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Brawl",
            faction_1=attacking_faction,
            faction_2=enemy_faction,
            warrior_list_1=[attacking_warrior],
            warrior_list_2=[enemy_warrior],
            month=3,
            quest_contract=None,
        )
    )

    assert result.quest_contract is None


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_matches_equally_sized_groups():
    skirmish = SkirmishFactory()
    attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[attacking_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        FighterPairsMatched(
            skirmish=skirmish,
            warrior_1=attacking_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_grants_a_free_attack_to_the_more_numerous_group():
    skirmish = SkirmishFactory()
    first_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    second_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.FAST_ATTACK,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[first_attacking_participant, second_attacking_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        FighterPairsMatched(
            skirmish=skirmish,
            warrior_1=first_attacking_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
        AttackerDefenderDecided(
            skirmish=skirmish,
            attacker=second_attacking_participant.warrior,
            attacker_action=SkirmishActionChoices.FAST_ATTACK,
            defender=enemy_participant.warrior,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
    ]


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_lets_the_first_warrior_attack():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    # Boundary randomness: equal matching points are decided by a random draw
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.random", return_value=0.2):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                warrior_1=attacking_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        attacker=attacking_warrior,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=enemy_warrior,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_lets_the_second_warrior_attack():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    # Boundary randomness: equal matching points are decided by a random draw
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.random", return_value=0.8):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                warrior_1=attacking_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        attacker=enemy_warrior,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=attacking_warrior,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_with_two_defensive_stances():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    result = handle_determine_attacker_and_defender(
        context=DetermineAttacker(
            skirmish=skirmish,
            warrior_1=attacking_warrior,
            action_1=SkirmishActionChoices.DEFENSIVE_STANCE,
            warrior_2=enemy_warrior,
            action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        attacker=attacking_warrior,
        attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        defender=enemy_warrior,
        defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_loots_and_captures_for_the_attacking_faction():
    """
    Both sides carry someone who is neither dead nor healthy, because that is where the two rules
    differ: the loser's unconscious are stripped where they lie, the winner's own are not, and the
    one who fled is gone with his kit whichever side he was on.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction, skirmish=skirmish, quest__loot=250)
    dead_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    unconscious_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    healthy_attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    unconscious_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    fleeing_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING
    )
    skirmish.attacking_warriors.add(dead_attacking_warrior, unconscious_attacking_warrior, healthy_attacking_warrior)
    skirmish.defending_warriors.add(unconscious_enemy_warrior, fleeing_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)
    )

    assert result == SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[dead_attacking_warrior, unconscious_enemy_warrior],
        defeated_unconscious_warriors=[unconscious_enemy_warrior],
        victorious_healthy_warriors=[healthy_attacking_warrior],
        quest_name=quest_contract.quest.name,
        # Two defenders turned out against an easy quest's band of up to five, so the contract pays
        # two fifths of its face value
        quest_loot=100,
        month=3,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_pays_the_full_loot_for_a_full_muster():
    """
    The advertised figure is never an undersell: the turnout is drawn from the difficulty band, so a
    faction that fields the top of it earns the contract's whole face value.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(
        faction=skirmish.attacking_faction,
        skirmish=skirmish,
        quest__loot=300,
        quest__difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY,
    )
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))
    # An easy quest musters up to five
    for _ in range(5):
        skirmish.defending_warriors.add(
            WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
        )

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)
    )

    assert result.quest_loot == quest_contract.quest.loot


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_pays_less_for_a_thin_warband():
    """
    The money follows the opposition rather than the opposition being padded to fit the money: a hard
    quest against a faction that can field two men is an easy fight and pays like one.
    """
    skirmish = SkirmishFactory()
    QuestContractFactory(
        faction=skirmish.attacking_faction,
        skirmish=skirmish,
        quest__loot=800,
        quest__difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD,
    )
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))
    skirmish.defending_warriors.add(
        WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    )
    skirmish.defending_warriors.add(
        WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    )

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)
    )

    # Two of the eight a hard quest musters, so a quarter of the 800 on the contract
    assert result.quest_loot == 200


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_does_not_loot_a_warband_that_fled():
    """
    A defeat is declared as soon as nobody on a side is healthy, so a warband can lose without
    leaving anyone on the field. Stripping "everyone not healthy" would have cost the loser every
    weapon and piece of armour he owns for running away.
    """
    skirmish = SkirmishFactory()
    fleeing_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING
    )
    healthy_enemy_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(fleeing_attacking_warrior)
    skirmish.defending_warriors.add(healthy_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.defending_faction, month=3)
    )

    assert result.incapacitated_warriors == []
    assert result.defeated_unconscious_warriors == []


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_pays_no_quest_loot_to_a_rival_victor():
    """
    The reward is handed to whoever won further down the chain, so carrying it regardless of the
    outcome credited the rival with the contract holder's own quest money.
    """
    skirmish = SkirmishFactory()
    QuestContractFactory(faction=skirmish.attacking_faction, skirmish=skirmish, quest__loot=250)
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))
    skirmish.defending_warriors.add(WarriorFactory(faction=skirmish.defending_faction))

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.defending_faction, month=3)
    )

    assert result.quest_loot == 0


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_loots_and_captures_for_the_defending_faction():
    """
    The mirror image of the test above: the loot follows the victor, not the side that marched.

    Back when the two sides were named after the player rather than their role, this case took the
    winner's items from the loser's side and vice versa, so a losing player kept the gear of everyone
    who was merely knocked out.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.attacking_faction, skirmish=skirmish, quest__loot=250)
    unconscious_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    healthy_enemy_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(unconscious_attacking_warrior)
    skirmish.defending_warriors.add(dead_enemy_warrior, healthy_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.defending_faction, month=3)
    )

    assert result == SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[dead_enemy_warrior, unconscious_attacking_warrior],
        defeated_unconscious_warriors=[unconscious_attacking_warrior],
        victorious_healthy_warriors=[healthy_enemy_warrior],
        quest_name=quest_contract.quest.name,
        quest_loot=0,
        month=3,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_without_a_quest_contract():
    """
    Not every skirmish belongs to a quest, so winning one without a contract has to work.
    """
    skirmish = SkirmishFactory()
    healthy_attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(healthy_attacking_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)
    )

    assert result == SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[],
        defeated_unconscious_warriors=[],
        victorious_healthy_warriors=[healthy_attacking_warrior],
        quest_name=None,
        quest_loot=0,
        month=3,
    )


@pytest.mark.django_db
def test_handle_finish_round_leaves_an_undecided_skirmish_without_a_victor():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(attacking_warrior)
    skirmish.defending_warriors.add(enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, round_number=1, victor=None, month=3)
    skirmish.refresh_from_db()
    assert skirmish.current_round == 2


@pytest.mark.django_db
def test_handle_finish_round_declares_the_attacking_faction_the_victor():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    skirmish.attacking_warriors.add(attacking_warrior)
    skirmish.defending_warriors.add(dead_enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, round_number=1, victor=skirmish.attacking_faction, month=3)


@pytest.mark.django_db
def test_handle_finish_round_declares_the_defending_faction_the_victor():
    skirmish = SkirmishFactory()
    unconscious_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(unconscious_attacking_warrior)
    skirmish.defending_warriors.add(enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, round_number=1, victor=skirmish.defending_faction, month=3)


@pytest.mark.django_db
def test_handle_finish_round_declares_the_attacking_faction_the_victor_on_a_mutual_wipeout():
    """
    Both sides going down in the same round is decided in favour of the side that marched.
    """
    skirmish = SkirmishFactory()
    dead_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    skirmish.attacking_warriors.add(dead_attacking_warrior)
    skirmish.defending_warriors.add(dead_enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, round_number=1, victor=skirmish.attacking_faction, month=3)
