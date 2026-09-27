from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import IncidentOption
from apps.warband.incident.models.pending_incident import PendingIncident


@dataclass(kw_only=True)
class AnswerPendingIncident(Command):
    """
    The player's answer to a question the world put to him.

    Carries the option itself rather than its key: the key came from a request, and it is checked
    against the entry before this is built, so nothing downstream has a key naming nothing to handle.
    """

    pending_incident: PendingIncident
    option: IncidentOption
    month: int


@dataclass(kw_only=True)
class AnswerOpenPendingIncidents(Command):
    """
    Give every question still open from an earlier month its default answer.

    Not answering is an answer, so a month that ends with a question open lands the default exactly
    as if the player had chosen it.
    """

    faction: Faction
    month: int
