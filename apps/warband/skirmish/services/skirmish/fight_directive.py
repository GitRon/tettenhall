import typing

from apps.warband.skirmish.choices.fight_directive import FightDirectiveChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.domain.turning_point import DIRECTIVE_ORDERS, TURNING_POINT_DIRECTIVES

if typing.TYPE_CHECKING:
    from apps.warband.skirmish.models import Skirmish, Warrior


def get_directed_action(
    *, directive: FightDirectiveChoices, warrior: Warrior, skirmish: Skirmish
) -> SkirmishActionChoices | None:
    """
    The action a directive gives this man for the round, or None when it gives him nothing.

    Nothing is the answer for a man the directive does not mean - everyone but the leader, for an order
    meant for him alone - and for a man who is not offered the action, through the same rule his select
    is built from. Either way he decides for himself, so a directive can never hand anybody an action
    he could not have been ordered to take by hand.
    """
    order = DIRECTIVE_ORDERS.get(directive)
    if order is None:
        return None
    if order.leader_only and not skirmish.is_side_led_by(warrior=warrior):
        return None
    if order.action not in {action for action, _label in warrior.get_skirmish_actions(skirmish=skirmish)}:
        return None

    return order.action


def get_offered_directives(
    *, turning_point: int, skirmish: Skirmish, roster: list[Warrior]
) -> list[FightDirectiveChoices]:
    """
    The answers a stop offers the player's side, without the ones nobody on it could carry out.

    A defender cannot sound the retreat and a band of novices cannot press the attack, and a button
    that changes nothing is worse than no button.
    """
    healthy = [warrior for warrior in roster if warrior.is_healthy]

    return [
        directive
        for directive in TURNING_POINT_DIRECTIVES[turning_point]
        if any(
            get_directed_action(directive=directive, warrior=warrior, skirmish=skirmish) is not None
            for warrior in healthy
        )
    ]
