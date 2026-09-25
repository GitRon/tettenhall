import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome, roster


class WergildClaimed(Incident):
    """
    A man's price is owed for a killing the player never ordered, and the war band pays it.

    Reported plainly: it is a killing, and the register never makes the dead the joke. The man it is
    claimed against is named in the title but not carried on the outcome, where "warrior" belongs to
    the morale lever - this costs silver and nothing else.

    Priced at a little under a third of a small hall's month, and weighted with the common costs:
    the law catching up with a war band is ordinary, not rare.
    """

    WEIGHT = 3

    TITLE = "Kin from across the river claimed wergild against {warrior}."
    BODY = "The reeve heard them out and found for the kin. The silver went back across the river with them."

    SILVER_CHANGE = -100

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return super().is_possible(faction=faction) and bool(roster(faction=faction))

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        warrior = random.choice(roster(faction=faction))

        return IncidentOutcome(
            title=cls.TITLE.format(warrior=warrior),
            body=cls.BODY,
            silver_change=cls.SILVER_CHANGE,
        )
