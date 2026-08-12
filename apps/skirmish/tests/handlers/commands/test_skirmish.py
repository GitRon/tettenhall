from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.handlers.commands.skirmish import (
    handle_assign_fighter_pairs,
    handle_create_skirmish,
    handle_determine_attacker_and_defender,
    handle_faction_wins_skirmish,
    handle_finish_round,
)
from apps.skirmish.messages.commands.skirmish import (
    CreateSkirmish,
    DetermineAttacker,
    FinishRound,
    StartDuel,
    WinSkirmish,
)
from apps.skirmish.messages.events.skirmish import (
    AttackerDefenderDecided,
    FighterPairsMatched,
    RoundFinished,
    SkirmishFinished,
)
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_create_skirmish_uses_the_given_opponents():
    quest_contract = QuestContractFactory()
    player_warrior = WarriorFactory(faction=quest_contract.faction)
    enemy_warrior = WarriorFactory(faction=quest_contract.quest.target_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=quest_contract.faction,
            faction_2=quest_contract.quest.target_faction,
            warrior_list_1=[player_warrior],
            warrior_list_2=[enemy_warrior],
            quest_contract=quest_contract,
        )
    )

    assert list(result.skirmish.player_warriors.all()) == [player_warrior]
    assert list(result.skirmish.non_player_warriors.all()) == [enemy_warrior]


@pytest.mark.django_db
def test_handle_create_skirmish_generates_opponents_when_none_are_given():
    quest_contract = QuestContractFactory()
    player_warrior = WarriorFactory(faction=quest_contract.faction)
    ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON)
    ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR)

    # Boundary randomness: the number of generated opponents is a random draw
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.randrange", return_value=2):
        result = handle_create_skirmish(
            context=CreateSkirmish(
                name="Ambush",
                faction_1=quest_contract.faction,
                faction_2=quest_contract.quest.target_faction,
                warrior_list_1=[player_warrior],
                warrior_list_2=None,
                quest_contract=quest_contract,
            )
        )

    assert result.skirmish.non_player_warriors.count() == 2


@pytest.mark.django_db
def test_handle_create_skirmish_passes_the_quest_contract_on():
    quest_contract = QuestContractFactory()
    player_warrior = WarriorFactory(faction=quest_contract.faction)
    enemy_warrior = WarriorFactory(faction=quest_contract.quest.target_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=quest_contract.faction,
            faction_2=quest_contract.quest.target_faction,
            warrior_list_1=[player_warrior],
            warrior_list_2=[enemy_warrior],
            quest_contract=quest_contract,
        )
    )

    assert result.quest_contract == quest_contract


@pytest.mark.django_db
def test_handle_create_skirmish_without_a_quest_contract():
    player_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=player_faction.savegame)
    player_warrior = WarriorFactory(faction=player_faction)
    enemy_warrior = WarriorFactory(faction=enemy_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Brawl",
            faction_1=player_faction,
            faction_2=enemy_faction,
            warrior_list_1=[player_warrior],
            warrior_list_2=[enemy_warrior],
            quest_contract=None,
        )
    )

    assert result.quest_contract is None


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_matches_equally_sized_groups():
    skirmish = SkirmishFactory()
    player_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.player_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.non_player_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[player_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        FighterPairsMatched(
            skirmish=skirmish,
            warrior_1=player_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_grants_a_free_attack_to_the_more_numerous_group():
    skirmish = SkirmishFactory()
    first_player_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.player_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    second_player_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.player_faction),
        skirmish_action=SkirmishActionChoices.FAST_ATTACK,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.non_player_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[first_player_participant, second_player_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        FighterPairsMatched(
            skirmish=skirmish,
            warrior_1=first_player_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
        AttackerDefenderDecided(
            skirmish=skirmish,
            attacker=second_player_participant.warrior,
            attacker_action=SkirmishActionChoices.FAST_ATTACK,
            defender=enemy_participant.warrior,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
    ]


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_lets_the_first_warrior_attack():
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.player_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction, dexterity=10)

    # Boundary randomness: equal matching points are decided by a random draw
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.random", return_value=0.2):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                warrior_1=player_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        attacker=player_warrior,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=enemy_warrior,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_lets_the_second_warrior_attack():
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.player_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction, dexterity=10)

    # Boundary randomness: equal matching points are decided by a random draw
    with mock.patch("apps.skirmish.handlers.commands.skirmish.random.random", return_value=0.8):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                warrior_1=player_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        attacker=enemy_warrior,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=player_warrior,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_with_two_defensive_stances():
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.player_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction, dexterity=10)

    result = handle_determine_attacker_and_defender(
        context=DetermineAttacker(
            skirmish=skirmish,
            warrior_1=player_warrior,
            action_1=SkirmishActionChoices.DEFENSIVE_STANCE,
            warrior_2=enemy_warrior,
            action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        attacker=player_warrior,
        attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        defender=enemy_warrior,
        defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_loots_and_captures_for_the_player():
    """
    Both sides carry someone who is neither dead nor healthy, because that is where the two rules
    differ: the loser's unconscious are stripped where they lie, the winner's own are not, and the
    one who fled is gone with his kit whichever side he was on.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.player_faction, skirmish=skirmish, quest__loot=250)
    dead_player_warrior = WarriorFactory(
        faction=skirmish.player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    unconscious_player_warrior = WarriorFactory(
        faction=skirmish.player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    healthy_player_warrior = WarriorFactory(faction=skirmish.player_faction)
    unconscious_enemy_warrior = WarriorFactory(
        faction=skirmish.non_player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    fleeing_enemy_warrior = WarriorFactory(
        faction=skirmish.non_player_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING
    )
    skirmish.player_warriors.add(dead_player_warrior, unconscious_player_warrior, healthy_player_warrior)
    skirmish.non_player_warriors.add(unconscious_enemy_warrior, fleeing_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.player_faction, month=3)
    )

    assert result == SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[dead_player_warrior, unconscious_enemy_warrior],
        defeated_unconscious_warriors=[unconscious_enemy_warrior],
        victorious_conscious_warriors=[healthy_player_warrior],
        quest_name=quest_contract.quest.name,
        quest_loot=250,
        month=3,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_does_not_loot_a_warband_that_fled():
    """
    A defeat is declared as soon as nobody on a side is healthy, so a warband can lose without
    leaving anyone on the field. Stripping "everyone not healthy" would have cost the loser every
    weapon and piece of armour he owns for running away.
    """
    skirmish = SkirmishFactory()
    fleeing_player_warrior = WarriorFactory(
        faction=skirmish.player_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING
    )
    healthy_enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.player_warriors.add(fleeing_player_warrior)
    skirmish.non_player_warriors.add(healthy_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.non_player_faction, month=3)
    )

    assert result.incapacitated_warriors == []
    assert result.defeated_unconscious_warriors == []


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_loots_and_captures_for_the_non_player_faction():
    """
    The mirror image of the test above: the loot follows the victor, not the player. Naming the two
    sides "player" and "non_player" used to make this case take the winner's items from the loser's
    side and vice versa, so a losing player kept the gear of everyone who was merely knocked out.
    """
    skirmish = SkirmishFactory()
    quest_contract = QuestContractFactory(faction=skirmish.player_faction, skirmish=skirmish, quest__loot=250)
    unconscious_player_warrior = WarriorFactory(
        faction=skirmish.player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.non_player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    healthy_enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.player_warriors.add(unconscious_player_warrior)
    skirmish.non_player_warriors.add(dead_enemy_warrior, healthy_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.non_player_faction, month=3)
    )

    assert result == SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[dead_enemy_warrior, unconscious_player_warrior],
        defeated_unconscious_warriors=[unconscious_player_warrior],
        victorious_conscious_warriors=[healthy_enemy_warrior],
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
    healthy_player_warrior = WarriorFactory(faction=skirmish.player_faction)
    skirmish.player_warriors.add(healthy_player_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.player_faction, month=3)
    )

    assert result == SkirmishFinished(
        skirmish=skirmish,
        incapacitated_warriors=[],
        defeated_unconscious_warriors=[],
        victorious_conscious_warriors=[healthy_player_warrior],
        quest_name=None,
        quest_loot=0,
        month=3,
    )


@pytest.mark.django_db
def test_handle_finish_round_leaves_an_undecided_skirmish_without_a_victor():
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.player_faction)
    enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.player_warriors.add(player_warrior)
    skirmish.non_player_warriors.add(enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, victor=None, month=3)
    skirmish.refresh_from_db()
    assert skirmish.current_round == 2


@pytest.mark.django_db
def test_handle_finish_round_declares_the_player_faction_the_victor():
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.player_faction)
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.non_player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    skirmish.player_warriors.add(player_warrior)
    skirmish.non_player_warriors.add(dead_enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, victor=skirmish.player_faction, month=3)


@pytest.mark.django_db
def test_handle_finish_round_declares_the_non_player_faction_the_victor():
    skirmish = SkirmishFactory()
    unconscious_player_warrior = WarriorFactory(
        faction=skirmish.player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.player_warriors.add(unconscious_player_warrior)
    skirmish.non_player_warriors.add(enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, victor=skirmish.non_player_faction, month=3)


@pytest.mark.django_db
def test_handle_finish_round_declares_the_player_faction_the_victor_on_a_mutual_wipeout():
    """
    Both sides going down in the same round is decided in the player's favour.
    """
    skirmish = SkirmishFactory()
    dead_player_warrior = WarriorFactory(
        faction=skirmish.player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    dead_enemy_warrior = WarriorFactory(
        faction=skirmish.non_player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    skirmish.player_warriors.add(dead_player_warrior)
    skirmish.non_player_warriors.add(dead_enemy_warrior)

    result = handle_finish_round(context=FinishRound(skirmish=skirmish, month=3))

    assert result == RoundFinished(skirmish=skirmish, victor=skirmish.player_faction, month=3)
