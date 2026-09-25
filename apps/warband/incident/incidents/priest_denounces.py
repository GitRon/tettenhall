import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome, roster


class PriestDenounces(Incident):
    """
    The church turns on the war band in public, and the man it names carries it.

    Half the share of [DevilAtTheFord]: being shamed from the steps is a smaller blow to a man's nerve
    than being frightened out of it. Reported plainly, so the pool's dry register stays under a third.
    """

    WEIGHT = 2

    TITLE = "A priest denounced the war band from the church steps, and named {warrior}."
    BODY = "He has not been back to the church since, and the men who were there do not sit beside him."

    MAX_MORALE_SHARE = -0.1

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
