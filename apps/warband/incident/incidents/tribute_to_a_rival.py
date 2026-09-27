import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import (
    Incident,
    IncidentOption,
    IncidentOutcome,
    IncidentQuestion,
)
from apps.warband.incident.models.pending_incident import PendingIncident


class TributeToARival(Incident):
    """
    A rival asks for silver with an army behind the asking, and the player decides whether it gets it.

    The first question in the catalogue, and the one whose default costs something: refusing is what
    happens when nobody answers, and the rival takes it out on the land. The rival arriving at
    strength later is a scheduled consequence, #74's.

    Only a rival still on the board can ask - one knocked out has no army to ask with. And only a
    player who could pay is asked, through the inherited pricing by the dearest answer.
    """

    WEIGHT = 2

    TITLE = "{rival} asked for tribute, with an army behind the asking."
    BODY = "The envoy spoke at length about friendship. The army did not need to."

    OPTIONS = (
        IncidentOption(
            key="pay",
            label="Pay",
            title="Tribute went to {rival}, who asked for it with an army behind the asking.",
            body="It was handed over with the usual words about friendship. Neither side wrote them down.",
            silver_change=-150,
        ),
        IncidentOption(
            key="refuse",
            label="Refuse",
            title="Tribute was refused to {rival}, who took it out on the land.",
            body="Two steadings burned on the border. Their men are rebuilding rather than answering the call.",
            fyrd_change=-2,
        ),
    )
    DEFAULT_OPTION = "refuse"

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return super().is_possible(faction=faction) and Faction.objects.rivals_in_play(player_faction=faction).exists()

    @classmethod
    def ask(cls, *, faction: Faction) -> IncidentQuestion:
        rival = random.choice(list(Faction.objects.rivals_in_play(player_faction=faction)))

        return IncidentQuestion(title=cls.TITLE.format(rival=rival), body=cls.BODY, rival=rival)

    @classmethod
    def answer(cls, *, option: IncidentOption, pending_incident: PendingIncident) -> IncidentOutcome:
        outcome = super().answer(option=option, pending_incident=pending_incident)
        outcome.title = outcome.title.format(rival=pending_incident.rival)

        return outcome
