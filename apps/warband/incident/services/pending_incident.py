from dataclasses import dataclass

from apps.warband.finance.models.transaction import Transaction
from apps.warband.incident.incidents import INCIDENTS_BY_NAME
from apps.warband.incident.incidents.base import IncidentOption
from apps.warband.incident.models.pending_incident import PendingIncident


@dataclass(kw_only=True)
class OpenQuestion:
    """
    A pending question together with the answers its entry accepts, which is what its card renders.
    """

    pending_incident: PendingIncident
    options: tuple[IncidentOption, ...]


def get_open_questions(*, faction_id: int) -> list[OpenQuestion]:
    """
    The questions the player still has to answer, each with the options its entry declares.
    """
    return [
        OpenQuestion(
            pending_incident=pending_incident,
            options=INCIDENTS_BY_NAME[pending_incident.incident].OPTIONS,
        )
        for pending_incident in PendingIncident.objects.for_player_faction(faction_id=faction_id)
    ]


def get_pending_incident_answer_refusal(*, pending_incident: PendingIncident, option: IncidentOption) -> str | None:
    """
    Why this answer cannot be given any more, or None when it can.

    A question is only asked of a player who could give every answer, but the month goes on while it
    waits: the silver can be spent and the gear it was about sold or lost. A default never needs this
    check - it never costs silver, and a default that sold gear would have nothing to sell.
    """
    if (
        option.silver_change < 0
        and Transaction.objects.current_balance(faction_id=pending_incident.faction_id) < -option.silver_change
    ):
        return "The treasury no longer covers that answer."

    if option.sells_item and (
        pending_incident.item is None or pending_incident.item.owner_id != pending_incident.faction_id
    ):
        return "That piece of gear is no longer yours to sell."

    return None
