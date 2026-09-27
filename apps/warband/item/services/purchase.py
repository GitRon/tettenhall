from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models import Transaction
from apps.warband.item.models.item import Item

UNAFFORDABLE_REFUSAL = "You don't have enough money to buy this item."


def get_purchase_refusal(*, item: Item, faction: Faction) -> str | None:
    """
    Why this faction may not buy "item" off its shop shelf, or None if it may.

    The first of two enforcement points, and the one the player hears from. "handle_buy_item" re-checks
    that the item is still for sale as a conditional UPDATE, which is what keeps a double click from
    charging for it twice.
    """
    if Transaction.objects.current_balance(faction_id=faction.id) < item.price:
        return UNAFFORDABLE_REFUSAL

    return None
