import pytest

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.exceptions import UnknownSkirmishActionError
from apps.warband.skirmish.services.actions.defensive_stance import DefensiveStanceService
from apps.warband.skirmish.services.actions.fast_attack import FastAttackService
from apps.warband.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.warband.skirmish.services.actions.simple_attack import SimpleAttackService
from apps.warband.skirmish.services.actions.utils import get_service_by_attack_action


def test_get_service_by_attack_action_simple_attack():
    result = get_service_by_attack_action(attack_action=SkirmishActionChoices.SIMPLE_ATTACK)

    assert result == SimpleAttackService


def test_get_service_by_attack_action_risky_attack():
    result = get_service_by_attack_action(attack_action=SkirmishActionChoices.RISKY_ATTACK)

    assert result == RiskyAttackService


def test_get_service_by_attack_action_fast_attack():
    result = get_service_by_attack_action(attack_action=SkirmishActionChoices.FAST_ATTACK)

    assert result == FastAttackService


def test_get_service_by_attack_action_defensive_stance():
    result = get_service_by_attack_action(attack_action=SkirmishActionChoices.DEFENSIVE_STANCE)

    assert result == DefensiveStanceService


def test_get_service_by_attack_action_unknown_action():
    with pytest.raises(UnknownSkirmishActionError, match="Attack action 99 is not a skirmish action"):
        get_service_by_attack_action(attack_action=99)
