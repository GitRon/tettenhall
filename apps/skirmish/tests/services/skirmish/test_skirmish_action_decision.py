import pytest

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.services.skirmish.skirmish_action_decision import SkirmishActionDecisionService
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_determine_decision_badly_wounded_warrior_defends():
    warrior = WarriorFactory(current_health=4, max_health=20, dexterity=20, strength=20)

    result = SkirmishActionDecisionService(warrior=warrior)._determine_decision()

    assert result == SkirmishActionChoices.DEFENSIVE_STANCE


@pytest.mark.django_db
def test_determine_decision_dextrous_warrior_attacks_fast():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=15, strength=15)

    result = SkirmishActionDecisionService(warrior=warrior)._determine_decision()

    assert result == SkirmishActionChoices.FAST_ATTACK


@pytest.mark.django_db
def test_determine_decision_strong_warrior_attacks_riskily():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=15)

    result = SkirmishActionDecisionService(warrior=warrior)._determine_decision()

    assert result == SkirmishActionChoices.RISKY_ATTACK


@pytest.mark.django_db
def test_determine_decision_average_warrior_attacks_simply():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=10)

    result = SkirmishActionDecisionService(warrior=warrior)._determine_decision()

    assert result == SkirmishActionChoices.SIMPLE_ATTACK


@pytest.mark.django_db
def test_process_returns_value_and_label():
    warrior = WarriorFactory(current_health=20, max_health=20, dexterity=10, strength=10)

    result = SkirmishActionDecisionService(warrior=warrior).process()

    assert result == (SkirmishActionChoices.SIMPLE_ATTACK.value, SkirmishActionChoices.SIMPLE_ATTACK.label)
