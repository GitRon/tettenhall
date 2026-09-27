from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.exceptions import UnknownSkirmishActionError
from apps.warband.skirmish.services.actions.assault_fortification import AssaultFortificationService
from apps.warband.skirmish.services.actions.base import SkirmishActionService
from apps.warband.skirmish.services.actions.defensive_stance import DefensiveStanceService
from apps.warband.skirmish.services.actions.fast_attack import FastAttackService
from apps.warband.skirmish.services.actions.rally import RallyService
from apps.warband.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.warband.skirmish.services.actions.simple_attack import SimpleAttackService


def get_service_by_skirmish_action(*, skirmish_action: int) -> type[SkirmishActionService]:
    if skirmish_action == SkirmishActionChoices.SIMPLE_ATTACK:
        return SimpleAttackService
    if skirmish_action == SkirmishActionChoices.RISKY_ATTACK:
        return RiskyAttackService
    if skirmish_action == SkirmishActionChoices.FAST_ATTACK:
        return FastAttackService
    if skirmish_action == SkirmishActionChoices.DEFENSIVE_STANCE:
        return DefensiveStanceService
    if skirmish_action == SkirmishActionChoices.ASSAULT_FORTIFICATION:
        return AssaultFortificationService
    if skirmish_action == SkirmishActionChoices.RALLY:
        return RallyService
    # The action arrives in a request, so this is bad input and not an unreachable state - a caller
    # without a boundary of its own has to be able to catch it and answer 400 rather than 500.
    raise UnknownSkirmishActionError(f"Action {skirmish_action} is not a skirmish action.")
