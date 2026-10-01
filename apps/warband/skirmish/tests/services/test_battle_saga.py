from unittest import mock

import pytest

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.services import battle_saga
from apps.warband.skirmish.services.battle_saga import saga_for_blow
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory

CHOICE = "apps.warband.skirmish.services.battle_saga._WORDING.choice"

# The parts every thrown blow is assembled from. Both men of a pair strike each round, so these come round
# twice a round, every round, and are the ones a long fight must not repeat.
EVERY_ROUND_PHRASINGS = [
    *battle_saga.APPROACH.values(),
    *battle_saga.COUNTER_APPROACH.values(),
    battle_saga.OFF_BALANCE_COUNTER_APPROACH,
    *battle_saga.MEETING.values(),
    battle_saga.RESULT_MISSED,
    battle_saga.RESULT_ABSORBED,
    battle_saga.RESULT_GRAZE,
    battle_saga.RESULT_SOLID,
    battle_saga.RESULT_HEAVY,
    battle_saga.UNOPPOSED_PREFIX,
]

OCCASIONAL_PHRASINGS = [
    *battle_saga.NOT_THROWN.values(),
    battle_saga.KILLED,
    battle_saga.INCAPACITATED,
    battle_saga.FLED,
    battle_saga.WITHDREW,
    battle_saga.INJURED,
    battle_saga.CAPTURED,
    battle_saga.ASSAULTED,
    battle_saga.FORTIFICATION_FELL,
    battle_saga.RALLIED,
    battle_saga.RALLIED_NOBODY,
    battle_saga.SKIRMISH_FINISHED,
]

ALL_PHRASINGS = [*EVERY_ROUND_PHRASINGS, *OCCASIONAL_PHRASINGS]


@pytest.mark.parametrize("phrasings", EVERY_ROUND_PHRASINGS)
def test_every_round_phrasings_come_in_at_least_five_variants(phrasings):
    assert len(set(phrasings)) >= 5


@pytest.mark.parametrize("phrasings", OCCASIONAL_PHRASINGS)
def test_occasional_phrasings_come_in_at_least_three_variants(phrasings):
    assert len(set(phrasings)) >= 3


@pytest.mark.parametrize("phrasings", ALL_PHRASINGS)
def test_phrasings_carry_no_numbers(phrasings):
    """
    The saga is the account without the arithmetic. A digit in a template is a roll or a price that
    belongs in the Tally.
    """
    assert any(character.isdigit() for phrasing in phrasings for character in phrasing) is False


def test_approach_words_exactly_the_actions_that_throw_a_blow():
    assert set(battle_saga.APPROACH) == {
        SkirmishActionChoices.SIMPLE_ATTACK,
        SkirmishActionChoices.RISKY_ATTACK,
        SkirmishActionChoices.FAST_ATTACK,
    }


def test_counter_approach_words_exactly_the_actions_that_throw_a_blow():
    """
    Only a man whose order throws a blow swings back, so the strike-backs cover what "APPROACH" covers.
    """
    assert set(battle_saga.COUNTER_APPROACH) == set(battle_saga.APPROACH)


def test_meeting_words_every_order_a_paired_defender_can_hold():
    """
    A man ordered to flee has left before anybody is paired, so he is the one order no blow can meet.
    """
    assert set(battle_saga.MEETING) == set(SkirmishActionChoices) - {SkirmishActionChoices.FLEE}


def test_not_thrown_words_exactly_the_actions_that_throw_nothing():
    assert set(battle_saga.NOT_THROWN) == {
        SkirmishActionChoices.DEFENSIVE_STANCE,
        SkirmishActionChoices.ASSAULT_FORTIFICATION,
        SkirmishActionChoices.RALLY,
    }


def test_saga_for_blow_tells_a_graze():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.FAST_ATTACK,
            defender=WarriorFactory.build(name="Cuthred", max_health=20),
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=2,
        )

    assert result == "Beorn darts in at Cuthred; Cuthred is braced behind his shield — the edge only grazes him."


def test_saga_for_blow_tells_a_solid_hit():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=WarriorFactory.build(name="Cuthred", max_health=20),
            defender_action=SkirmishActionChoices.FAST_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=5,
        )

    assert result == "Beorn cuts at Cuthred; Cuthred tries to dance clear — the blow lands hard."


def test_saga_for_blow_tells_a_blow_that_nearly_ends_him():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            defender=WarriorFactory.build(name="Cuthred", max_health=20),
            defender_action=SkirmishActionChoices.RISKY_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=7,
        )

    assert result == (
        "Beorn takes a huge swing at Cuthred; Cuthred, winding up a great blow of his own, is caught open — "
        "the blow staggers him."
    )


def test_saga_for_blow_tells_a_miss():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            defender=WarriorFactory.build(name="Cuthred"),
            defender_action=SkirmishActionChoices.RALLY,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_MISSED,
            damage=0,
        )

    assert result == (
        "Beorn takes a huge swing at Cuthred; Cuthred, shouting to his men, turns too late — the blow goes wide."
    )


def test_saga_for_blow_tells_armour_that_took_the_whole_blow():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=WarriorFactory.build(name="Cuthred"),
            defender_action=SkirmishActionChoices.ASSAULT_FORTIFICATION,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_ABSORBED,
            damage=0,
        )

    assert result == "Beorn cuts at Cuthred; Cuthred, hacking at the wall, barely turns — his mail turns the edge."


def test_saga_for_blow_tells_a_stand_off_without_a_blow_to_meet():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Offa"),
            attacker_action=SkirmishActionChoices.RALLY,
            defender=WarriorFactory.build(name="Cuthred"),
            defender_action=SkirmishActionChoices.RALLY,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
            damage=0,
        )

    assert result == "Offa is shouting to his men and lets Cuthred be."


def test_saga_for_blow_says_nobody_was_left_to_face_him():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=WarriorFactory.build(name="Cuthred", max_health=20),
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_UNOPPOSED,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=5,
        )

    assert result == (
        "With nobody left to face him, Beorn cuts at Cuthred; Cuthred brings his own blade round to parry — "
        "the blow lands hard."
    )


def test_saga_for_blow_tells_a_counter_as_a_strike_back():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Cuthred"),
            attacker_action=SkirmishActionChoices.FAST_ATTACK,
            defender=WarriorFactory.build(name="Beorn", max_health=20),
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_COUNTER,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=2,
        )

    assert result == (
        "Cuthred answers with a quick jab at Beorn; Beorn brings his own blade round to parry — the edge only "
        "grazes him."
    )


def test_saga_for_blow_tells_a_counter_a_fast_attack_threw_off_balance():
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[0]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Cuthred"),
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=WarriorFactory.build(name="Beorn", max_health=20),
            defender_action=SkirmishActionChoices.FAST_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_COUNTER,
            outcome=BlowOutcomeChoices.OUTCOME_ABSORBED,
            damage=0,
        )

    assert result == (
        "Caught off-balance, Cuthred swings back weakly at Beorn; Beorn tries to dance clear — his mail turns the edge."
    )


def test_saga_for_blow_refuses_a_strike_back_it_has_no_wording_for():
    with pytest.raises(RuntimeError, match=r"No saga wording for the strike-back of skirmish action 5\."):
        saga_for_blow(
            attacker=WarriorFactory.build(name="Cuthred"),
            attacker_action=SkirmishActionChoices.FLEE,
            defender=WarriorFactory.build(name="Beorn"),
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_COUNTER,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=5,
        )


def test_saga_for_blow_draws_each_part_on_its_own():
    """
    The three parts are drawn separately, so twenty rounds of the same two orders still vary.
    """
    with mock.patch(CHOICE, side_effect=lambda phrasings: phrasings[-1]):
        result = saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=WarriorFactory.build(name="Cuthred", max_health=20),
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=5,
        )

    assert result == (
        "Beorn comes on at Cuthred with a level stroke; Cuthred swings to meet it — he grunts as it strikes home."
    )


def test_saga_for_blow_refuses_an_action_it_has_no_wording_for():
    with pytest.raises(RuntimeError, match=r"No saga wording for the approach of skirmish action 5\."):
        saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.FLEE,
            defender=WarriorFactory.build(name="Cuthred"),
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=5,
        )


def test_saga_for_blow_refuses_an_outcome_it_has_no_wording_for():
    with pytest.raises(RuntimeError, match=r"No saga wording for blow outcome 0\."):
        saga_for_blow(
            attacker=WarriorFactory.build(name="Beorn"),
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=WarriorFactory.build(name="Cuthred"),
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            initiative=InitiativeChoices.INITIATIVE_WON_THE_ROLL,
            outcome=0,
            damage=0,
        )
