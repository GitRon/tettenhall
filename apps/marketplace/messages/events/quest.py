from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.marketplace.models.marketplace import Marketplace


class NewQuestsOffered(Event):
    @dataclass(kw_only=True)
    class Context:
        marketplace: Marketplace
        week: int
