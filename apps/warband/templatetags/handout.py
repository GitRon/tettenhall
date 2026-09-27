from django import template
from django.template.defaultfilters import floatformat

from apps.warband.item.models.item import Item
from apps.warband.item.services.handout import improves_anybody
from apps.warband.skirmish.models.warrior import Warrior

register = template.Library()


@register.filter
def gear_gain(warrior: Warrior, item: Item) -> str:  # noqa: PBR001 - a filter is called positionally
    """
    What handing this item to this man would add to what he is already holding.

    The picker names the thing being displaced, and two names settle nothing: the figure that decides
    a "Rusty Seax" against a "Traditional Spear" is the mean of a dice notation, and neither notation
    is on the option either. A difference rather than the two means side by side, because it answers
    the second half of the question as well - not only whether this is an upgrade, but for whom it is
    the biggest one.

    Trimmed the way the card header and the equip select print a mean, so a whole number reads "2"
    rather than "2.0". A sign on every answer, because "1.5" alone is as easily read as the new
    item's own figure repeated.

    Reads "held_gear_values" off the man, which is one query for the column rather than one per
    option - see "annotate_held_gear_values".
    """
    gain = item.expectancy_value - warrior.held_gear_values[item.gear_slot]

    # Trimmed to nothing rather than to "+0": the two are worth the same, and a signed zero reads as
    # a gain of some size
    if gain == 0:
        return "±0"

    return f"+{floatformat(gain)}" if gain > 0 else floatformat(gain)


@register.filter
def improves_nobody(item: Item, roster: list[Warrior]) -> bool:  # noqa: PBR001 - a filter is called positionally
    """
    Whether every man on the roster already holds something at least as good in this item's slot.

    What lets a card say "skip me" before the player has read its dice: on a long shelf or a full
    stores the question is rarely whether an item is good, only whether it is good for anybody here.

    False for an empty roster rather than True: with nobody to compare against there is nothing the
    item has been found worse than, and a rival's stores page hands in no roster at all.
    """
    return bool(roster) and not improves_anybody(item=item, roster=roster)
