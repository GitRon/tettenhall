import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome, losable_items


class MoorLostGear(Incident):
    """
    A man comes back from the moor without what he went in with.

    The issue's own example, and the entry the weights are most careful with: gear is the only lever
    here that destroys something the player paid for. Rare, and never the good stuff - see
    [losable_items].
    """

    WEIGHT = 2

    TITLE = "{warrior} has lost his {item} in the moor."
    BODY = "He reports a revenant. Others report beer."

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return bool(losable_items(faction=faction))

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        lost_item = random.choice(losable_items(faction=faction))

        # Only worn items are losable, so there is always a man to name - and he is named in the
        # title rather than carried on the outcome, where "warrior" belongs to the morale lever
        return IncidentOutcome(
            title=cls.TITLE.format(warrior=lost_item.worn_by, item=lost_item.type.name.lower()),
            body=cls.BODY,
            lost_item=lost_item,
        )
