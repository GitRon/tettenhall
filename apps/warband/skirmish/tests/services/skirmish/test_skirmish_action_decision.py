import pytest

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.services.skirmish.skirmish_action_decision import SkirmishActionDecisionService
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.injury_type import InjuryType
from apps.warband.warrior.tests.factories.injury import InjuryFactory
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


@pytest.mark.django_db
def test_determine_decision_badly_wounded_warrior_defends():
    warrior = WarriorFactory(current_health=4, max_health=20, dexterity=20, strength=20, experience=100)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.DEFENSIVE_STANCE


@pytest.mark.django_db
def test_determine_decision_dextrous_warrior_attacks_fast():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=15, strength=15, experience=400)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.FAST_ATTACK


@pytest.mark.django_db
def test_determine_decision_strong_warrior_attacks_riskily():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=15, experience=900)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.RISKY_ATTACK


@pytest.mark.django_db
def test_determine_decision_average_warrior_attacks_simply():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=10)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.SIMPLE_ATTACK


@pytest.mark.django_db
def test_process_returns_value_and_label():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=10)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory()).process()

    assert result == (SkirmishActionChoices.SIMPLE_ATTACK.value, SkirmishActionChoices.SIMPLE_ATTACK.label)


@pytest.mark.django_db
def test_determine_decision_stops_reaching_for_a_swing_an_injury_took_away():
    """
    A man quick enough for the fast attack loses it with his hand, rather than going on picking a
    swing he can no longer make.
    """
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=15, strength=10)
    InjuryFactory(
        warrior=warrior,
        type=InjuryTypeFactory(attribute=InjuryType.AttributeChoices.ATTRIBUTE_DEXTERITY, magnitude=6),
    )

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.SIMPLE_ATTACK


@pytest.mark.django_db
def test_determine_decision_strong_attacker_storms_a_standing_wall():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=15, strength=15)
    skirmish = SkirmishFactory(fortification_strength=20)
    skirmish.attacking_warriors.add(warrior)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=skirmish)._determine_decision()

    assert result == SkirmishActionChoices.ASSAULT_FORTIFICATION


@pytest.mark.django_db
def test_determine_decision_strong_defender_does_not_storm_his_own_wall():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=15, experience=900)
    skirmish = SkirmishFactory(fortification_strength=20)
    skirmish.defending_warriors.add(warrior)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=skirmish)._determine_decision()

    assert result == SkirmishActionChoices.RISKY_ATTACK


@pytest.mark.django_db
def test_determine_decision_badly_wounded_warrior_without_the_stance_attacks_simply():
    """
    His first wish is one his level has not bought him, so it falls through rather than being fought
    with - the enemy card and the round he fights both come from this decision.
    """
    warrior = WarriorFactory(current_health=4, max_health=20, dexterity=10, strength=10, experience=0)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.SIMPLE_ATTACK


@pytest.mark.django_db
def test_determine_decision_falls_through_to_the_next_wish_he_is_offered():
    """
    Strong and quick at level 3, in a fight with no wall: the assault he wants first is not on offer,
    the fast attack is.
    """
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=15, strength=15, experience=400)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.FAST_ATTACK


@pytest.mark.django_db
def test_determine_decision_strong_level_one_man_attacks_simply_rather_than_riskily():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=15, experience=0)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.SIMPLE_ATTACK


@pytest.mark.django_db
def test_determine_decision_rival_leader_never_rallies():
    """
    Offered the rally like any leader, and never reaching for it: rivals do not steady their men, the
    same exemption #177 holds for their morale between months.
    """
    skirmish = SkirmishFactory()
    leader = WarriorFactory(
        faction=skirmish.defending_faction, current_health=20, max_health=20, dexterity=10, strength=10
    )
    skirmish.defending_faction.leader = leader
    skirmish.defending_faction.save()
    skirmish.defending_warriors.add(leader)

    result = SkirmishActionDecisionService(warrior=leader, skirmish=skirmish)._determine_decision()

    assert result == SkirmishActionChoices.SIMPLE_ATTACK
