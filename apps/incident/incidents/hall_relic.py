import random

from apps.faction.models.faction import Faction
from apps.incident.incidents.base import Incident, IncidentOutcome, roster


class HallRelic(Incident):
    """
    A relic reaches the hall, and one man's nerve is permanently the better for carrying it.

    The morale ceiling rather than this month's morale, because
    "handle_replenish_warrior_morale" refills every warrior to his maximum far later in the same
    month: a change to "current_morale" made where incidents are chosen is erased in the same tick.
    The ceiling is the one morale number a month does not touch.

    Weighted level with [DevilAtTheFord] and carrying the same share, so the ceiling nets out flat
    across a savegame. It is close to a one-way ratchet - "max_morale" otherwise only moves on a
    level-up - so a drift either way accumulates over fifty months with nothing to correct it.
    """

    WEIGHT = 3

    TITLE = "A relic came to the hall, and {warrior} was given it to carry."
    BODY = "The priest who sold it named three saints it might belong to, and would not be pressed on which."

    MAX_MORALE_SHARE = 0.2

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
