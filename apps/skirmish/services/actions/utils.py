from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.exceptions import UnknownSkirmishActionError
from apps.skirmish.services.actions.base import AttackService
from apps.skirmish.services.actions.defensive_stance import DefensiveStanceService
from apps.skirmish.services.actions.fast_attack import FastAttackService
from apps.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.skirmish.services.actions.simple_attack import SimpleAttackService


def get_service_by_attack_action(*, attack_action: int) -> type[AttackService]:
    if attack_action == SkirmishActionChoices.SIMPLE_ATTACK:
        return SimpleAttackService
    if attack_action == SkirmishActionChoices.RISKY_ATTACK:
        return RiskyAttackService
    if attack_action == SkirmishActionChoices.FAST_ATTACK:
        return FastAttackService
    if attack_action == SkirmishActionChoices.DEFENSIVE_STANCE:
        return DefensiveStanceService
    # The action arrives in a request, so this is bad input and not an unreachable state - a caller
    # without a boundary of its own has to be able to catch it and answer 400 rather than 500.
    raise UnknownSkirmishActionError(f"Attack action {attack_action} is not a skirmish action.")
