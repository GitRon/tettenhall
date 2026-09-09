import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome, roster


class DevilAtTheFord(Incident):
    """
    Superstition, which the register allows as a joke, at the cost of one man's nerve for good.

    The counterweight to [HallRelic]: same share, same weight, and the same reason for moving the
    ceiling rather than this month's morale.
    """

    WEIGHT = 3

    TITLE = "{warrior} swears he saw the Devil at the ford."
    BODY = "He has been shown the goat. He is not persuaded."

    MAX_MORALE_SHARE = -0.2

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return bool(roster(faction=faction))

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        warrior = random.choice(roster(faction=faction))

        return IncidentOutcome(
            title=cls.TITLE.format(warrior=warrior),
            body=cls.BODY,
            max_morale_share=cls.MAX_MORALE_SHARE,
            warrior=warrior,
        )
