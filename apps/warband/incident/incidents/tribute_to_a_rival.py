import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import Incident, IncidentOutcome


class TributeToARival(Incident):
    """
    A rival asks for silver with an army behind the asking, and gets it.

    The half of a tribute demand that needs no decision: the choice to refuse is #75's, and the
    rival arriving at strength when refused is a scheduled consequence, #74's. What is left is the
    dearest ordinary cost after the hall roof, weighted low for being the one entry that names an
    enemy.

    Only a rival still on the board can ask - one knocked out has no army to ask with.
    """

    WEIGHT = 2

    TITLE = "Tribute went to {rival}, who asked for it with an army behind the asking."
    BODY = "It was handed over with the usual words about friendship. Neither side wrote them down."

    SILVER_CHANGE = -150

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return super().is_possible(faction=faction) and Faction.objects.rivals_in_play(player_faction=faction).exists()

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        rival = random.choice(list(Faction.objects.rivals_in_play(player_faction=faction)))

        return IncidentOutcome(
            title=cls.TITLE.format(rival=rival),
            body=cls.BODY,
            silver_change=cls.SILVER_CHANGE,
        )
