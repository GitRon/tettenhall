from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.marketplace.models.marketplace import Marketplace


class RestockMarketplaceItems(Command):
    @dataclass(kw_only=True)
    class Context:
        marketplace: Marketplace
        week: int
