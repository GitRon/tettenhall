from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.incident.incidents.base import IncidentOutcome


@dataclass(kw_only=True)
class IncidentOccurred(Event):
    """
    Something happened to a faction that it did not decide.

    Carries the resolved outcome rather than the incident class: everything that needed a query -
    which man, which item, how much of a reserve is left to lose - was answered in the command
    handler, because the handlers reacting to this run under strict mode's database blocker.
    """

    faction: Faction
    month: int
    outcome: IncidentOutcome
