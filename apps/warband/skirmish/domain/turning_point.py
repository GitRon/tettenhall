from dataclasses import dataclass

from apps.warband.skirmish.choices.fight_directive import FightDirectiveChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.choices.turning_point import TurningPointChoices

# Below this share of his health a leader is in trouble, which stops the fight once for each side.
# Deliberately above "SkirmishActionDecisionService.DESPERATE_HEALTH_SHARE": the player is asked before
# his leader's own judgement turns defensive, not after
LEADER_IN_TROUBLE_HEALTH_SHARE = 0.5


@dataclass(frozen=True, kw_only=True)
class DirectiveOrder:
    """
    What a directive tells the player's men for one round, and which of them it is meant for.
    """

    action: SkirmishActionChoices
    # Whether only the man who leads the side is meant, or every man on it
    leader_only: bool


DIRECTIVE_ORDERS: dict[int, DirectiveOrder] = {
    FightDirectiveChoices.RALLY: DirectiveOrder(action=SkirmishActionChoices.RALLY, leader_only=True),
    FightDirectiveChoices.SOUND_THE_RETREAT: DirectiveOrder(action=SkirmishActionChoices.FLEE, leader_only=False),
    FightDirectiveChoices.HOLD_BACK: DirectiveOrder(action=SkirmishActionChoices.DEFENSIVE_STANCE, leader_only=True),
    FightDirectiveChoices.LEAVE_THE_FIELD: DirectiveOrder(action=SkirmishActionChoices.FLEE, leader_only=True),
    FightDirectiveChoices.PRESS_THE_ATTACK: DirectiveOrder(
        action=SkirmishActionChoices.RISKY_ATTACK, leader_only=False
    ),
}

# The answers each stop offers on top of fighting on and taking command, which every stop offers. The
# ones offered nobody on the player's side are left out when the stop is shown - see
# "TurningPointService.get_offered_directives"
TURNING_POINT_DIRECTIVES: dict[int, tuple[FightDirectiveChoices, ...]] = {
    TurningPointChoices.LEADER_THREATENED: (
        FightDirectiveChoices.HOLD_BACK,
        FightDirectiveChoices.LEAVE_THE_FIELD,
        FightDirectiveChoices.RALLY,
    ),
    TurningPointChoices.MAN_DOWN: (
        FightDirectiveChoices.RALLY,
        FightDirectiveChoices.SOUND_THE_RETREAT,
    ),
    TurningPointChoices.ENEMY_LEADER_EXPOSED: (FightDirectiveChoices.PRESS_THE_ATTACK,),
}


@dataclass(frozen=True, kw_only=True)
class TurningPointFinding:
    """
    What one finished round left for the player: the stop it shows, and what it saw on the way there.
    """

    # The one stop the round shows, or None when it brought none and the fight goes on by itself
    turning_point: TurningPointChoices | None
    # The player's men a "man down" stop names, and nobody when it is another stop or none
    warriors: list
    # Whether each side's leader was seen in trouble this round, whether or not that became the stop -
    # an outranked one is spent all the same, or it would stop the next round over a moment now past
    attacking_leader_in_trouble: bool
    defending_leader_in_trouble: bool


def is_in_trouble(*, current_health: int, max_health: int) -> bool:
    return current_health < max_health * LEADER_IN_TROUBLE_HEALTH_SHARE


def most_important(*, turning_points: list[TurningPointChoices]) -> TurningPointChoices | None:
    """
    The one stop a round that brought several of them shows. The choices are numbered by importance.
    """
    return min(turning_points, default=None)
