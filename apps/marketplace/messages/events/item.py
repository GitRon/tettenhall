from dataclasses import dataclass

from queuebie.messages import Event

from apps.marketplace.models.marketplace import Marketplace


@dataclass(kw_only=True)
class MarketplaceItemsRestocked(Event):
    marketplace: Marketplace
    week: int
