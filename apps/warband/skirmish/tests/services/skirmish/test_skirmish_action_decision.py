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
    warrior = WarriorFactory(current_health=4, max_health=20, dexterity=20, strength=20)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.DEFENSIVE_STANCE


@pytest.mark.django_db
def test_determine_decision_dextrous_warrior_attacks_fast():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=15, strength=15)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=SkirmishFactory())._determine_decision()

    assert result == SkirmishActionChoices.FAST_ATTACK


@pytest.mark.django_db
def test_determine_decision_strong_warrior_attacks_riskily():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=15)

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
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=15)
    skirmish = SkirmishFactory(fortification_strength=20)
    skirmish.defending_warriors.add(warrior)

    result = SkirmishActionDecisionService(warrior=warrior, skirmish=skirmish)._determine_decision()

    assert result == SkirmishActionChoices.RISKY_ATTACK
