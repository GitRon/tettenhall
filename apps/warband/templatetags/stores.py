from django import template

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.item.services.sale import get_sell_payout

register = template.Library()


@register.filter
def sell_payout(item: Item, faction: Faction) -> int:  # noqa: PBR001 - a filter is called positionally
    """
    What the Sell button on this item's card pays, from the same function the sale itself credits.

    The faction is handed in rather than read off the item, so a column of cards shares the one
    faction instance and its cached town instead of reaching the town once per card.
    """
    return get_sell_payout(item=item, faction=faction)
