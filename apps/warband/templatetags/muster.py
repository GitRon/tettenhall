from django import template

from apps.warband.skirmish.models.warrior import Warrior

register = template.Library()


@register.filter
def still_up(warrior_list: list[Warrior]) -> int:  # noqa: PBR001 - a filter is called positionally
    """
    How many of a band are still on their feet.

    A plain count rather than a queryset filter: the caller is a fight panel that has already
    evaluated its roster to render the rows, so counting in Python costs nothing and a second query
    would.
    """
    return sum(1 for warrior in warrior_list if warrior.is_healthy)
