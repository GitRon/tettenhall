from django import template

from apps.warband.skirmish.projections.payroll import Payroll

register = template.Library()


@register.filter
def net_of_wages(income: int, payroll: Payroll) -> str:  # noqa: PBR001 - a filter is called positionally
    """
    What a month leaves the purse with, hall income less wages, signed.

    Off the same payroll the "Wages" line above it prints, rather than a total worked out anywhere
    else, so the three figures on the brief always add up. Only the hall is counted: quest rewards,
    loot and sales are not a rate the player can plan on, and the label says so.

    A sign on every answer, because "30" alone does not say which way the silver is going - and that
    is the whole question the figure is there to answer.
    """
    net = income - payroll.total_amount

    if net == 0:
        return "±0"

    return f"+{net}" if net > 0 else f"\N{MINUS SIGN}{-net}"
