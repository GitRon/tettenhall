from dataclasses import dataclass

from queuebie.messages import Event

from apps.marketplace.models.marketplace import Marketplace


@dataclass(kw_only=True)
class NewMarketplaceCreated(Event):
    marketplace: Marketplace
    current_week: int = 1
