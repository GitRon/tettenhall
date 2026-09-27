import pytest

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.exceptions import UnknownSkirmishActionError
from apps.warband.skirmish.services.actions.assault_fortification import AssaultFortificationService
from apps.warband.skirmish.services.actions.defensive_stance import DefensiveStanceService
from apps.warband.skirmish.services.actions.fast_attack import FastAttackService
from apps.warband.skirmish.services.actions.rally import RallyService
from apps.warband.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.warband.skirmish.services.actions.simple_attack import SimpleAttackService
from apps.warband.skirmish.services.actions.utils import get_service_by_skirmish_action


def test_get_service_by_skirmish_action_simple_attack():
    result = get_service_by_skirmish_action(skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK)

    assert result == SimpleAttackService


def test_get_service_by_skirmish_action_risky_attack():
    result = get_service_by_skirmish_action(skirmish_action=SkirmishActionChoices.RISKY_ATTACK)

    assert result == RiskyAttackService


def test_get_service_by_skirmish_action_fast_attack():
    result = get_service_by_skirmish_action(skirmish_action=SkirmishActionChoices.FAST_ATTACK)

    assert result == FastAttackService


def test_get_service_by_skirmish_action_defensive_stance():
    result = get_service_by_skirmish_action(skirmish_action=SkirmishActionChoices.DEFENSIVE_STANCE)

    assert result == DefensiveStanceService


def test_get_service_by_skirmish_action_assault_fortification():
    result = get_service_by_skirmish_action(skirmish_action=SkirmishActionChoices.ASSAULT_FORTIFICATION)

    assert result == AssaultFortificationService


def test_get_service_by_skirmish_action_rally():
    result = get_service_by_skirmish_action(skirmish_action=SkirmishActionChoices.RALLY)

    assert result == RallyService


def test_get_service_by_skirmish_action_unknown_action():
    with pytest.raises(UnknownSkirmishActionError, match="Action 99 is not a skirmish action"):
        get_service_by_skirmish_action(skirmish_action=99)
