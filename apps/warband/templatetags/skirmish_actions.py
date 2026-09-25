from django import template

from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior

register = template.Library()


@register.simple_tag
def offered_actions(warrior: Warrior, skirmish: Skirmish) -> list[tuple]:  # noqa: PBR001 - a tag is called positionally
    """
    What the player may order this man to do in this fight. A tag because the answer depends on the
    fight as well as the man, and a template cannot hand a method an argument.
    """
    return warrior.get_skirmish_actions(skirmish=skirmish)


@register.simple_tag
def decided_action(warrior: Warrior, skirmish: Skirmish) -> str:  # noqa: PBR001 - a tag is called positionally
    """
    The name of what the AI orders this man to do in this fight, for the side the player does not command.
    """
    return warrior.decide_skirmish_action(skirmish=skirmish)[1]
