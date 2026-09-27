from unittest import mock

import pytest

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.services import battle_saga
from apps.warband.skirmish.services.battle_saga import saga_for_blow
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory

CHOICE = "apps.warband.skirmish.services.battle_saga.random.choice"

ALL_PHRASINGS = [
    *battle_saga.APPROACH.values(),
    *battle_saga.MEETING.values(),
    battle_saga.RESULT_MISSED,
    battle_saga.RESULT_ABSORBED,
    battle_saga.RESULT_GRAZE,
    battle_saga.RESULT_SOLID,
    battle_saga.RESULT_HEAVY,
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

# The three parts every thrown blow is assembled from, and the stand-offs told whole in their place.
# These are what a long fight repeats, so these are the ones that must not read as one sentence twice.
BLOW_PHRASINGS = [
    *battle_saga.APPROACH.values(),
    *battle_saga.MEETING.values(),
    battle_saga.RESULT_MISSED,
    battle_saga.RESULT_ABSORBED,
    battle_saga.RESULT_GRAZE,
    battle_saga.RESULT_SOLID,
    battle_saga.RESULT_HEAVY,
    *battle_saga.NOT_THROWN.values(),
]


@pytest.mark.parametrize("phrasings", BLOW_PHRASINGS)
def test_blow_phrasings_come_in_at_least_three_variants(phrasings):
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

    assert result == "Beorn brings his blade down at Cuthred; Cuthred tries to turn it aside — it catches him squarely."


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
