from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.town.buildings.marketplace import Marketplace


def get_sell_payout(*, item: Item, faction: Faction) -> int:
    """
    The silver "faction" is paid for selling "item" at its town's current marketplace.

    The one place both ends ask: "handle_sell_item" credits this amount and the sell card prints it,
    so the number on the button and the silver in the purse cannot come apart.
    """
    marketplace = Marketplace.get_building_by_type(building_type=faction.town.marketplace)

    return marketplace.get_sell_payout(price=item.price)
