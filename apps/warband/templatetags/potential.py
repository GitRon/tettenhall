from django import template

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
