from dataclasses import dataclass

from queuebie.messages import Command

from apps.marketplace.models.marketplace import Marketplace


@dataclass(kw_only=True)
class RestockPubMercenaries(Command):
    marketplace: Marketplace
    week: int
