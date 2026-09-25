import typing
from dataclasses import dataclass

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices

if typing.TYPE_CHECKING:
    from apps.warband.skirmish.models import Skirmish, Warrior


@dataclass(frozen=True, kw_only=True)
class ActionRequirement:
    """
    What a man has to have learned and to be holding before he may pick an action.

    Two filters, intersected, rather than one combined requirement: "any weapon, but only from level 3"
    is a level requirement with no gear in it, and a weapon-bound action is a gear requirement that
    may or may not carry a level as well.
    """

    minimum_level: int = 1
    # Names of the weapon types the action comes with. "None" is any weapon at all, the "Unarmed"
    # fallback included, and is what every action shipping today asks for
    weapon_types: frozenset[str] | None = None

    def is_met_by(self, *, warrior: Warrior) -> bool:
        if warrior.level < self.minimum_level:
            return False
        # The weapon is only looked up when it can change the answer, so a rule no action narrows
        # by gear costs no query for the fallback type
        if self.weapon_types is None:
            return True
        # Read the way the fight reads it, so a man with nothing in his hands holds "Unarmed" and is
        # an ordinary gear state rather than a special case
        return warrior.get_weapon_or_fallback().type.name in self.weapon_types


# Never gated, and kept out of the table below so no entry there can gate them. A man with an empty
# list could not be given an order at all, and fleeing is the one action that takes him off the
# field: a player who cannot pick it cannot end a fight he is losing except by losing it.
ALWAYS_OFFERED = frozenset({SkirmishActionChoices.SIMPLE_ATTACK, SkirmishActionChoices.FLEE})

# One action per level threshold, so a level-up adds something to the repertoire rather than only
# to the numbers. The wall is not the man's to earn: whether it may be stormed is the fight's
# question - see "Skirmish.can_be_assaulted_by".
ACTION_REQUIREMENTS: dict[int, ActionRequirement] = {
    SkirmishActionChoices.DEFENSIVE_STANCE: ActionRequirement(minimum_level=2),
    SkirmishActionChoices.FAST_ATTACK: ActionRequirement(minimum_level=3),
    SkirmishActionChoices.RISKY_ATTACK: ActionRequirement(minimum_level=4),
    SkirmishActionChoices.ASSAULT_FORTIFICATION: ActionRequirement(minimum_level=1),
}


def get_offered_actions(*, warrior: Warrior, skirmish: Skirmish) -> list[tuple[int, str]]:
    """
    Every action this man may be ordered to take in this fight, as choices for a select.

    The one place the question is answered: the player's select, the check on the posted round and
    the AI's decision all ask here, so what is offered, what is accepted and what a rival does cannot
    drift apart.
    """
    return [
        (action, label)
        for action, label in SkirmishActionChoices.choices
        if action in ALWAYS_OFFERED
        or (
            ACTION_REQUIREMENTS[action].is_met_by(warrior=warrior)
            and (action != SkirmishActionChoices.ASSAULT_FORTIFICATION or skirmish.can_be_assaulted_by(warrior=warrior))
        )
    ]
