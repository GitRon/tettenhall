from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.marketplace.models.marketplace import Marketplace


class PubMercenariesRestocked(Event):
    @dataclass
    class Context:
        marketplace: Marketplace
        week: int
