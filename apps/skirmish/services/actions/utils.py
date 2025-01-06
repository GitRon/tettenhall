from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.services.actions.fast_attack import FastAttackService
from apps.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.skirmish.services.actions.simple_attack import SimpleAttackService


def get_service_by_attack_action(*, attack_action: int) -> type[SimpleAttackService]:
    if attack_action == SkirmishActionChoices.SIMPLE_ATTACK:
        return SimpleAttackService
    if attack_action == SkirmishActionChoices.RISKY_ATTACK:
        return RiskyAttackService
    if attack_action == SkirmishActionChoices.FAST_ATTACK:
        return FastAttackService
    raise RuntimeError("Invalid attack action")
