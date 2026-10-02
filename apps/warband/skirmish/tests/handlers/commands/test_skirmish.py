from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.handlers.commands.skirmish import (
    handle_assign_fighter_pairs,
    handle_attack_faction,
    handle_create_skirmish,
    handle_determine_attacker_and_defender,
    handle_faction_wins_skirmish,
    handle_finish_round,
    handle_send_locals_home,
    handle_take_raid_yield,
    handle_warrior_assaults_fortification,
    handle_warrior_attacks_warrior,
)
from apps.warband.skirmish.messages.commands.skirmish import (
    AttackFaction,
    CreateSkirmish,
    DetermineAttacker,
    FinishRound,
    SendLocalsHome,
    StartDuel,
    TakeRaidYield,
    WarriorAssaultsFortification,
    WarriorAttacksWarrior,
    WinSkirmish,
)
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
    HerdsLifted,
    LocalsWentHome,
    RoundFinished,
    SkirmishFinished,
    VillageBurned,
)
from apps.warband.skirmish.messages.events.warrior import BlowWasNotStruck
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.warband.skirmish.raids.kinds import StormTheBurh
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.buildings.fortification import NPC_STARTING_FORTIFICATION_LEVEL, Palisade
from apps.warband.warrior.choices.modified_attribute import ModifiedAttributeChoices
from apps.warband.warrior.tests.factories.injury import InjuryFactory
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


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
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
        )
    )

    assert result == FactionWasAttacked(
        attacking_faction=attacking_faction,
        defending_faction=target_faction,
        attacking_warriors=[attacking_leader],
        defending_warriors=[target_leader, *result.local_warriors],
        local_warriors=result.local_warriors,
        fortification_strength=0,
        raid_kind=RaidKindChoices.STORM_THE_BURH,
        month=3,
    )


@pytest.mark.django_db
def test_handle_attack_faction_stages_the_wall_of_the_targets_town():
    """
    The wall the attackers run into is the one the target's town has built, at the level a rival is
    handed when it is created.
    """
    attacking_faction = FactionFactory()
    target_faction = FactionFactory(
        savegame=attacking_faction.savegame, town__fortification=NPC_STARTING_FORTIFICATION_LEVEL
    )
    WarriorFactory(faction=target_faction)

    result = handle_attack_faction(
        context=AttackFaction(
            attacking_faction=attacking_faction,
            target_faction=target_faction,
            assigned_warriors=[WarriorFactory(faction=attacking_faction)],
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
        )
    )

    assert result.fortification_strength == Palisade.FORTIFICATION_STRENGTH


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
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
        )
    )

    assert result.defending_warriors == [healthy_defender, *result.local_warriors]


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
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=1,
        )
    )

    assert result.defending_warriors == [available_defender, *result.local_warriors]


@pytest.mark.django_db
def test_handle_attack_faction_meets_a_raid_in_the_shire_in_the_open():
    """The herds are not behind the wall, however much of it the town has built."""
    attacking_faction = FactionFactory()
    target_faction = FactionFactory(
        savegame=attacking_faction.savegame, town__fortification=NPC_STARTING_FORTIFICATION_LEVEL
    )
    WarriorFactory(faction=target_faction)

    result = handle_attack_faction(
        context=AttackFaction(
            attacking_faction=attacking_faction,
            target_faction=target_faction,
            assigned_warriors=[WarriorFactory(faction=attacking_faction)],
            raid_kind=RaidKindChoices.LIFT_THE_HERDS,
            month=3,
        )
    )

    assert (result.raid_kind, result.fortification_strength) == (RaidKindChoices.LIFT_THE_HERDS, 0)


@pytest.mark.django_db
def test_handle_attack_faction_brings_out_the_people_of_the_place():
    """The men of the place turn out for the defending faction and stand on its side of the fight."""
    attacking_faction = FactionFactory()
    target_faction = FactionFactory(savegame=attacking_faction.savegame)
    WarriorFactory(faction=target_faction)

    result = handle_attack_faction(
        context=AttackFaction(
            attacking_faction=attacking_faction,
            target_faction=target_faction,
            assigned_warriors=[WarriorFactory(faction=attacking_faction)],
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
        )
    )

    assert [(local.faction, local.monthly_salary) for local in result.local_warriors] == [
        (target_faction, 0)
    ] * StormTheBurh.LOCALS_TURNOUT
    assert result.defending_warriors[-StormTheBurh.LOCALS_TURNOUT :] == result.local_warriors


@pytest.mark.django_db
def test_handle_take_raid_yield_drives_off_a_share_of_the_purse():
    skirmish = SkirmishFactory(raid_kind=RaidKindChoices.LIFT_THE_HERDS)
    TransactionFactory(faction=skirmish.defending_faction, amount=500)

    result = handle_take_raid_yield(context=TakeRaidYield(skirmish=skirmish, month=4))

    assert result == [
        HerdsLifted(
            skirmish=skirmish,
            raiding_faction=skirmish.attacking_faction,
            raided_faction=skirmish.defending_faction,
            amount=100,
            month=4,
        )
    ]


@pytest.mark.django_db
def test_handle_take_raid_yield_finds_nothing_in_an_empty_purse():
    skirmish = SkirmishFactory(raid_kind=RaidKindChoices.LIFT_THE_HERDS)

    result = handle_take_raid_yield(context=TakeRaidYield(skirmish=skirmish, month=4))

    assert result == []


@pytest.mark.django_db
def test_handle_take_raid_yield_burns_names_off_the_fyrd():
    skirmish = SkirmishFactory(raid_kind=RaidKindChoices.BURN_THE_VILLAGE, defending_faction__fyrd_reserve=1)

    result = handle_take_raid_yield(context=TakeRaidYield(skirmish=skirmish, month=4))

    assert result == [
        VillageBurned(
            skirmish=skirmish,
            raiding_faction=skirmish.attacking_faction,
            raided_faction=skirmish.defending_faction,
            fyrd_names=1,
            month=4,
        )
    ]


@pytest.mark.django_db
def test_handle_take_raid_yield_finds_no_fyrd_left_to_burn():
    skirmish = SkirmishFactory(raid_kind=RaidKindChoices.BURN_THE_VILLAGE, defending_faction__fyrd_reserve=0)

    result = handle_take_raid_yield(context=TakeRaidYield(skirmish=skirmish, month=4))

    assert result == []


@pytest.mark.django_db
def test_handle_send_locals_home_releases_the_men_of_the_place_still_standing():
    skirmish = SkirmishFactory()
    local = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.local_warriors.add(local)

    result = handle_send_locals_home(
        context=SendLocalsHome(skirmish=skirmish, defeated_unconscious_warriors=[], month=4)
    )

    local.refresh_from_db()
    assert result == LocalsWentHome(skirmish=skirmish, warriors=[local], month=4)
    assert local.faction is None


@pytest.mark.django_db
def test_handle_send_locals_home_leaves_the_dead_where_they_fell():
    skirmish = SkirmishFactory()
    local = WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    skirmish.local_warriors.add(local)

    result = handle_send_locals_home(
        context=SendLocalsHome(skirmish=skirmish, defeated_unconscious_warriors=[], month=4)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_send_locals_home_leaves_a_man_about_to_be_taken_to_the_victor():
    """Capture is capture: he goes to the cells, whichever of the two commands drains first."""
    skirmish = SkirmishFactory()
    local = WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    skirmish.local_warriors.add(local)

    result = handle_send_locals_home(
        context=SendLocalsHome(skirmish=skirmish, defeated_unconscious_warriors=[local], month=4)
    )

    local.refresh_from_db()
    assert result is None
    assert local.faction == skirmish.defending_faction


@pytest.mark.django_db
def test_handle_send_locals_home_leaves_a_man_already_taken_alone():
    skirmish = SkirmishFactory()
    local = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.local_warriors.add(local)

    result = handle_send_locals_home(
        context=SendLocalsHome(skirmish=skirmish, defeated_unconscious_warriors=[], month=4)
    )

    assert result is None


@pytest.mark.django_db
def test_handle_create_skirmish_records_the_men_of_the_place():
    attacking_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=attacking_faction.savegame)
    local = WarriorFactory(faction=enemy_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Cattle raid",
            faction_1=attacking_faction,
            faction_2=enemy_faction,
            warrior_list_1=[WarriorFactory(faction=attacking_faction)],
            warrior_list_2=[local],
            local_warriors=[local],
            raid_kind=RaidKindChoices.LIFT_THE_HERDS,
            month=7,
        )
    )

    assert list(result.skirmish.local_warriors.all()) == [local]


@pytest.mark.django_db
def test_handle_create_skirmish_uses_the_given_opponents():
    attacking_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=attacking_faction.savegame)
    attacking_warrior = WarriorFactory(faction=attacking_faction)
    enemy_warrior = WarriorFactory(faction=enemy_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=attacking_faction,
            faction_2=enemy_faction,
            warrior_list_1=[attacking_warrior],
            warrior_list_2=[enemy_warrior],
            local_warriors=[],
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
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
    attacking_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=attacking_faction.savegame)
    attacking_warrior = WarriorFactory(faction=attacking_faction)
    enemy_warrior = WarriorFactory(faction=enemy_faction)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Ambush",
            faction_1=attacking_faction,
            faction_2=enemy_faction,
            warrior_list_1=[attacking_warrior],
            warrior_list_2=[enemy_warrior],
            local_warriors=[],
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=7,
        )
    )

    assert result.skirmish.month == 7


@pytest.mark.django_db
def test_handle_create_skirmish_records_the_raid_kind():
    attacking_faction = FactionFactory()
    enemy_faction = FactionFactory(savegame=attacking_faction.savegame)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Cattle raid",
            faction_1=attacking_faction,
            faction_2=enemy_faction,
            warrior_list_1=[WarriorFactory(faction=attacking_faction)],
            warrior_list_2=[WarriorFactory(faction=enemy_faction)],
            local_warriors=[],
            raid_kind=RaidKindChoices.BURN_THE_VILLAGE,
            month=7,
        )
    )

    assert result.skirmish.raid_kind == RaidKindChoices.BURN_THE_VILLAGE


@pytest.mark.django_db
def test_handle_create_skirmish_refuses_an_empty_defending_side():
    """
    Nobody is conjured to fill the gap, so a side that fields nobody is a fight that cannot be staged.
    What keeps it unreachable is who may be targeted at all - "attackable_targets" for a march.
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
                local_warriors=[],
                raid_kind=RaidKindChoices.STORM_THE_BURH,
                month=3,
            )
        )


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
    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
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
            round_number=skirmish.current_round,
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
    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
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
            round_number=skirmish.current_round,
            warrior_1=first_attacking_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
        AttackerDefenderDecided(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            attacker=second_attacking_participant.warrior,
            attacker_action=SkirmishActionChoices.FAST_ATTACK,
            defender=enemy_participant.warrior,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            initiative=InitiativeChoices.INITIATIVE_UNOPPOSED,
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_gives_each_man_an_opponent_of_his_own():
    """
    Two a side are two fights, not two men falling on whoever the draw picked - which could be the
    same man twice while the other is never touched.
    """
    skirmish = SkirmishFactory()
    first_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    second_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.FAST_ATTACK,
    )
    first_enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )
    second_enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.RISKY_ATTACK,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order. The draw is pinned
    # too, although an even fight never reaches it - a pairing that went back to drawing its defender
    # would otherwise land on the expectation below by chance about one run in four.
    with (
        mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"),
        mock.patch(
            "apps.warband.skirmish.handlers.commands.skirmish.random.choice",
            return_value=first_enemy_participant,
        ),
    ):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[first_attacking_participant, second_attacking_participant],
                skirmish_participants_2=[first_enemy_participant, second_enemy_participant],
            )
        )

    assert result == [
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=first_attacking_participant.warrior,
            warrior_2=first_enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=second_attacking_participant.warrior,
            warrior_2=second_enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.FAST_ATTACK,
            attack_action_2=SkirmishActionChoices.RISKY_ATTACK,
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_sends_only_the_surplus_man_in_free():
    """
    Everyone the other side can field somebody against is matched off first, and only the man left
    over strikes unopposed - so a side one larger buys one free attack and not three.
    """
    skirmish = SkirmishFactory()
    first_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    second_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.FAST_ATTACK,
    )
    third_attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.RISKY_ATTACK,
    )
    first_enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )
    second_enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )

    # Boundary randomness: both groups get shuffled, and whom the surplus man falls on is a draw
    with (
        mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"),
        mock.patch(
            "apps.warband.skirmish.handlers.commands.skirmish.random.choice",
            return_value=first_enemy_participant,
        ),
    ):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[
                    first_attacking_participant,
                    second_attacking_participant,
                    third_attacking_participant,
                ],
                skirmish_participants_2=[first_enemy_participant, second_enemy_participant],
            )
        )

    assert result == [
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=first_attacking_participant.warrior,
            warrior_2=first_enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=second_attacking_participant.warrior,
            warrior_2=second_enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.FAST_ATTACK,
            attack_action_2=SkirmishActionChoices.SIMPLE_ATTACK,
        ),
        AttackerDefenderDecided(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            attacker=third_attacking_participant.warrior,
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            defender=first_enemy_participant.warrior,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            initiative=InitiativeChoices.INITIATIVE_UNOPPOSED,
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_walks_a_fleeing_warrior_off_before_matching_the_rest():
    """
    The order to leave comes back ahead of the pairings, so the battle log reads the way the round
    happened - and the man who left is not matched with anyone.
    """
    skirmish = SkirmishFactory()
    fleeing_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.FLEE,
    )
    staying_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order
    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[fleeing_participant, staying_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        WithdrawFromSkirmish(skirmish=skirmish, warrior=fleeing_participant.warrior),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=staying_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_matches_nobody_when_a_side_walks_away_entirely():
    """
    A side the retreat emptied has nobody to pair, and the matching picks a random opponent out of the
    other list - which raises on an empty one. The fight is then lost by the men who left it:
    "handle_finish_round" counts healthy warriors, and a warrior who walked off is not one.
    """
    skirmish = SkirmishFactory()
    fleeing_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.FLEE,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    result = handle_assign_fighter_pairs(
        context=StartDuel(
            skirmish=skirmish,
            skirmish_participants_1=[fleeing_participant],
            skirmish_participants_2=[enemy_participant],
        )
    )

    assert result == [WithdrawFromSkirmish(skirmish=skirmish, warrior=fleeing_participant.warrior)]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_matches_nobody_when_the_enemy_walks_away_entirely():
    skirmish = SkirmishFactory()
    attacking_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    fleeing_enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.FLEE,
    )

    result = handle_assign_fighter_pairs(
        context=StartDuel(
            skirmish=skirmish,
            skirmish_participants_1=[attacking_participant],
            skirmish_participants_2=[fleeing_enemy_participant],
        )
    )

    assert result == [WithdrawFromSkirmish(skirmish=skirmish, warrior=fleeing_enemy_participant.warrior)]


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_lets_the_first_warrior_attack():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    # Boundary randomness: equal matching points are decided by a random draw
    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.random", return_value=0.2):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                round_number=2,
                warrior_1=attacking_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        round_number=2,
        attacker=attacking_warrior,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=enemy_warrior,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
    )


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_lets_the_second_warrior_attack():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    # Boundary randomness: equal matching points are decided by a random draw
    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.random", return_value=0.8):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                round_number=2,
                warrior_1=attacking_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        round_number=2,
        attacker=enemy_warrior,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=attacking_warrior,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
    )


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_with_two_defensive_stances():
    skirmish = SkirmishFactory()
    attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    result = handle_determine_attacker_and_defender(
        context=DetermineAttacker(
            skirmish=skirmish,
            round_number=2,
            warrior_1=attacking_warrior,
            action_1=SkirmishActionChoices.DEFENSIVE_STANCE,
            warrior_2=enemy_warrior,
            action_2=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    )

    assert result == AttackerDefenderDecided(
        skirmish=skirmish,
        round_number=2,
        attacker=attacking_warrior,
        attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        defender=enemy_warrior,
        defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
    )


def _warrior_attacks_warrior(
    *, skirmish, attacker, defender, initiative: int = InitiativeChoices.INITIATIVE_UNOPPOSED
) -> WarriorAttacksWarrior:
    return WarriorAttacksWarrior(
        skirmish=skirmish,
        round_number=1,
        attacker=attacker,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=defender,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        initiative=initiative,
    )


@pytest.mark.django_db
def test_handle_warrior_attacks_warrior_strikes_between_two_men_standing():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)

    result = handle_warrior_attacks_warrior(
        context=_warrior_attacks_warrior(skirmish=skirmish, attacker=attacker, defender=defender)
    )

    assert len(result) == 1


@pytest.mark.django_db
def test_handle_warrior_attacks_warrior_throws_nothing_at_a_man_already_down():
    """
    The defender on the message is the instance the round was drawn with, and still reads healthy: he
    went down to an earlier blow of the same round. Struck again, he would die twice in the log.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)
    Warrior.objects.filter(id=defender.id).update(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = handle_warrior_attacks_warrior(
        context=_warrior_attacks_warrior(skirmish=skirmish, attacker=attacker, defender=defender)
    )

    assert result == BlowWasNotStruck(skirmish=skirmish, attacker=attacker, defender=defender, attacker_is_down=False)


@pytest.mark.django_db
def test_handle_warrior_attacks_warrior_throws_nothing_at_a_man_already_unconscious():
    """
    Struck again, a man lying senseless would be carried past the death threshold by a blow meant for
    somebody standing, or go down unconscious a second time in the log.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)
    Warrior.objects.filter(id=defender.id).update(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_warrior_attacks_warrior(
        context=_warrior_attacks_warrior(skirmish=skirmish, attacker=attacker, defender=defender)
    )

    assert result == BlowWasNotStruck(skirmish=skirmish, attacker=attacker, defender=defender, attacker_is_down=False)


@pytest.mark.django_db
def test_handle_warrior_attacks_warrior_throws_nothing_from_a_man_already_down():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)
    Warrior.objects.filter(id=attacker.id).update(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_warrior_attacks_warrior(
        context=_warrior_attacks_warrior(skirmish=skirmish, attacker=attacker, defender=defender)
    )

    assert result == BlowWasNotStruck(skirmish=skirmish, attacker=attacker, defender=defender, attacker_is_down=True)


@pytest.mark.django_db
def test_handle_warrior_attacks_warrior_drops_a_counter_its_striker_is_too_far_gone_for():
    """
    The first blow put him down, and his fall has its own line. Nothing announced the counter, so there
    is no line for a refusal to close either.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)
    Warrior.objects.filter(id=attacker.id).update(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_warrior_attacks_warrior(
        context=_warrior_attacks_warrior(
            skirmish=skirmish, attacker=attacker, defender=defender, initiative=InitiativeChoices.INITIATIVE_COUNTER
        )
    )

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_attacks_warrior_tells_a_counter_at_a_man_somebody_else_put_down():
    """
    The man he means to strike back at went down to a blow from outside the pair, in between. That the
    counter found him already down is worth saying, as it is for any other blow.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)
    Warrior.objects.filter(id=defender.id).update(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_warrior_attacks_warrior(
        context=_warrior_attacks_warrior(
            skirmish=skirmish, attacker=attacker, defender=defender, initiative=InitiativeChoices.INITIATIVE_COUNTER
        )
    )

    assert result == BlowWasNotStruck(skirmish=skirmish, attacker=attacker, defender=defender, attacker_is_down=False)


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_loots_and_captures_for_the_attacking_faction():
    """
    Both sides carry someone who is neither dead nor healthy, because that is where the two rules
    differ: the loser's unconscious are stripped where they lie, the winner's own are not, and the
    one who fled is gone with his kit whichever side he was on.
    """
    skirmish = SkirmishFactory()
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
        month=3,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_leaves_out_a_victor_who_walked_off_the_field():
    """
    A warrior ordered to flee shares in none of what the fight pays out, and this is where that is
    decided for all of it: "victorious_healthy_warriors" is what the experience reward is handed, so a
    man who was not there when it ended earns nothing for it.
    """
    skirmish = SkirmishFactory()
    healthy_attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    fled_attacking_warrior = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING
    )
    unconscious_enemy_warrior = WarriorFactory(
        faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    skirmish.attacking_warriors.add(healthy_attacking_warrior, fled_attacking_warrior)
    skirmish.defending_warriors.add(unconscious_enemy_warrior)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)
    )

    assert result.victorious_healthy_warriors == [healthy_attacking_warrior]


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
def test_handle_faction_wins_skirmish_loots_and_captures_for_the_defending_faction():
    """
    The mirror image of the attacking side winning: the loot follows the victor, not the side that
    marched.

    Back when the two sides were named after the player rather than their role, this case took the
    winner's items from the loser's side and vice versa, so a losing player kept the gear of everyone
    who was merely knocked out.
    """
    skirmish = SkirmishFactory()
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
        month=3,
    )


@pytest.mark.django_db
def test_handle_faction_wins_skirmish_refuses_a_skirmish_that_already_has_a_victor():
    """
    Killing the player's leader ends the savegame, which force-resolves the very fight it ended in -
    so the round still resolving that fight arrives behind a victory already paid out. Stopping here
    is what keeps the loser from being stripped twice and the victor from being paid twice.
    """
    skirmish = SkirmishFactory()
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))
    Skirmish.objects.filter(pk=skirmish.pk).update(victorious_faction=skirmish.attacking_faction)

    result = handle_faction_wins_skirmish(
        context=WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)
    )

    assert result is None


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


@pytest.mark.django_db
def test_handle_determine_attacker_and_defender_costs_a_lame_man_the_initiative():
    """
    Dexterity decides who strikes, so an injury is felt twice: a weaker swing, and fewer of them.

    The lame man carries six points off ten against an unharmed ten, and the draw sits at the share
    his four points buy - so he loses here and would have won it at his stored dexterity.
    """
    skirmish = SkirmishFactory()
    lame_warrior = WarriorFactory(faction=skirmish.attacking_faction, dexterity=10)
    InjuryFactory(
        warrior=lame_warrior,
        type=InjuryTypeFactory(attribute=ModifiedAttributeChoices.ATTRIBUTE_DEXTERITY, magnitude=6),
    )
    enemy_warrior = WarriorFactory(faction=skirmish.defending_faction, dexterity=10)

    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.random", return_value=0.4):
        result = handle_determine_attacker_and_defender(
            context=DetermineAttacker(
                skirmish=skirmish,
                round_number=2,
                warrior_1=lame_warrior,
                action_1=SkirmishActionChoices.SIMPLE_ATTACK,
                warrior_2=enemy_warrior,
                action_2=SkirmishActionChoices.SIMPLE_ATTACK,
            )
        )

    assert result.attacker == enemy_warrior
    assert result.defender == lame_warrior


@pytest.mark.django_db
def test_handle_create_skirmish_raises_the_wall_it_is_given():
    attacking_faction = FactionFactory()
    defending_faction = FactionFactory(savegame=attacking_faction.savegame)

    result = handle_create_skirmish(
        context=CreateSkirmish(
            name="Attack on Wessex",
            faction_1=attacking_faction,
            faction_2=defending_faction,
            warrior_list_1=[WarriorFactory(faction=attacking_faction)],
            warrior_list_2=[WarriorFactory(faction=defending_faction)],
            local_warriors=[],
            raid_kind=RaidKindChoices.STORM_THE_BURH,
            month=3,
            fortification_strength=20,
        )
    )

    assert result.skirmish.fortification_strength == 20


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_sends_a_man_at_the_wall_and_keeps_him_in_the_pairing():
    skirmish = SkirmishFactory(fortification_strength=20)
    storming_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.ASSAULT_FORTIFICATION,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )

    # Boundary randomness: both groups get shuffled, so pin the resulting order
    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[storming_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        WarriorAssaultsFortification(
            skirmish=skirmish, round_number=skirmish.current_round, warrior=storming_participant.warrior
        ),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=storming_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.ASSAULT_FORTIFICATION,
            attack_action_2=SkirmishActionChoices.SIMPLE_ATTACK,
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_sends_a_rallying_leader_and_keeps_him_in_the_pairing():
    skirmish = SkirmishFactory()
    rallying_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.RALLY,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )

    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[rallying_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        RallyRemainingWarriors(skirmish=skirmish, leader=rallying_participant.warrior),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=rallying_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.RALLY,
            attack_action_2=SkirmishActionChoices.SIMPLE_ATTACK,
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_lets_an_unopposed_rallying_leader_strike_nobody():
    skirmish = SkirmishFactory()
    fighting_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    rallying_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.RALLY,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )

    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[fighting_participant, rallying_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        RallyRemainingWarriors(skirmish=skirmish, leader=rallying_participant.warrior),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=fighting_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.SIMPLE_ATTACK,
        ),
        StoreLastUsedSkirmishAction(
            skirmish=skirmish, warrior=rallying_participant.warrior, skirmish_action=SkirmishActionChoices.RALLY
        ),
    ]


@pytest.mark.django_db
def test_handle_assign_fighter_pairs_lets_an_unopposed_man_at_the_wall_strike_nobody():
    """
    A man nobody is left to face would strike free at a random defender - unless his round is the wall,
    in which case the wall is all of it. With no exchange to record it, his order is stored here, so
    his card opens the next round on it.
    """
    skirmish = SkirmishFactory(fortification_strength=20)
    fighting_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )
    storming_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.attacking_faction),
        skirmish_action=SkirmishActionChoices.ASSAULT_FORTIFICATION,
    )
    enemy_participant = SkirmishParticipant(
        warrior=WarriorFactory(faction=skirmish.defending_faction),
        skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )

    with mock.patch("apps.warband.skirmish.handlers.commands.skirmish.random.shuffle"):
        result = handle_assign_fighter_pairs(
            context=StartDuel(
                skirmish=skirmish,
                skirmish_participants_1=[fighting_participant, storming_participant],
                skirmish_participants_2=[enemy_participant],
            )
        )

    assert result == [
        WarriorAssaultsFortification(
            skirmish=skirmish, round_number=skirmish.current_round, warrior=storming_participant.warrior
        ),
        FighterPairsMatched(
            skirmish=skirmish,
            round_number=skirmish.current_round,
            warrior_1=fighting_participant.warrior,
            warrior_2=enemy_participant.warrior,
            attack_action_1=SkirmishActionChoices.SIMPLE_ATTACK,
            attack_action_2=SkirmishActionChoices.SIMPLE_ATTACK,
        ),
        StoreLastUsedSkirmishAction(
            skirmish=skirmish,
            warrior=storming_participant.warrior,
            skirmish_action=SkirmishActionChoices.ASSAULT_FORTIFICATION,
        ),
    ]


@pytest.mark.django_db
def test_handle_warrior_assaults_fortification_wears_the_wall_down():
    skirmish = SkirmishFactory(fortification_strength=20)
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10, strength_baseline=10)

    # Patched at the boundary: the die behind the swing
    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = handle_warrior_assaults_fortification(
            context=WarriorAssaultsFortification(skirmish=skirmish, round_number=1, warrior=warrior)
        )

    assert [(type(message), message.damage, message.remaining_strength) for message in result] == [
        (FortificationAssaulted, 3, 17)
    ]
    skirmish.refresh_from_db()
    assert skirmish.fortification_strength == 17


@pytest.mark.django_db
def test_handle_warrior_assaults_fortification_brings_the_wall_down():
    skirmish = SkirmishFactory(fortification_strength=2)
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10, strength_baseline=10)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = handle_warrior_assaults_fortification(
            context=WarriorAssaultsFortification(skirmish=skirmish, round_number=1, warrior=warrior)
        )

    assert result[1:] == [FortificationFell(skirmish=skirmish, round_number=1, warrior=warrior)]
    assert result[0].remaining_strength == 0


@pytest.mark.django_db
def test_handle_warrior_assaults_fortification_on_a_wall_already_down():
    """
    Two men storming in the same round: the second finds rubble, and the wall does not fall twice.
    """
    skirmish = SkirmishFactory(fortification_strength=0)
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10, strength_baseline=10)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = handle_warrior_assaults_fortification(
            context=WarriorAssaultsFortification(skirmish=skirmish, round_number=1, warrior=warrior)
        )

    assert [(type(message), message.damage, message.remaining_strength) for message in result] == [
        (FortificationAssaulted, 0, 0)
    ]
