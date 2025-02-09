from dataclasses import dataclass

from queuebie.messages import Event

from apps.marketplace.models.marketplace import Marketplace


@dataclass(kw_only=True)
class NewQuestsOffered(Event):
    marketplace: Marketplace
    week: int
