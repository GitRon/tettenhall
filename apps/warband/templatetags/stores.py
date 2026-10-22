from django import template

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.item.services.sale import get_sell_payout
from apps.warband.item.services.upgrade import get_item_upgrade_offer

register = template.Library()


@register.filter
def sell_payout(item: Item, faction: Faction) -> int:
    """
    What the Sell button on this item's card pays, from the same function the sale itself credits.

    The faction is handed in rather than read off the item, so a column of cards shares the one
    faction instance and its cached town instead of reaching the town once per card.
    """
    return get_sell_payout(item=item, faction=faction)


@register.simple_tag
def item_upgrade_offer(*, item: Item, faction: Faction, month: int, balance: int) -> dict | None:
    """
    What the weaponsmith offers for this item's card, from the same refusal the upgrade view asks.

    The month and the purse are handed in from the request's own context rather than read here, so a
    column of cards costs no ledger sum per card.
    """
    return get_item_upgrade_offer(item=item, faction=faction, month=month, balance=balance)
