from django import template

from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.domain.knowledge import WarriorKnowledge
from apps.warband.warrior.domain.potential import describe_potential

register = template.Library()


@register.filter
def potential_reading(levels_left: int | None, knowledge: WarriorKnowledge) -> str:
    """
    The word for how far a man can still rise, empty where the viewer is told nothing - see
    [describe_potential].
    """
    return describe_potential(levels_left=levels_left, knowledge=knowledge) or ""


@register.filter
def experience_threshold(warrior: Warrior, knowledge: WarriorKnowledge) -> int | None:
    """
    The threshold his experience is shown against, or None for one of the viewer's own men or a man he
    holds who has reached his ceiling. A rival's man is shown the threshold he would have without one,
    because his potential is not the viewer's to know, and a missing threshold would give it away.
    """
    if knowledge.potential_is_visible:
        return warrior.experience_for_next_level

    return warrior.experience_for_next_level_ignoring_potential
