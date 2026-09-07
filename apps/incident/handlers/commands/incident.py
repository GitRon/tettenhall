import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.incident.incidents import INCIDENTS, QUIET_MONTH_WEIGHT
from apps.incident.messages.commands.incident import ChooseIncident
from apps.incident.messages.events.incident import IncidentOccurred


@message_registry.register_command(command=ChooseIncident)
def handle_choose_incident(*, context: ChooseIncident) -> Event | None:
    """
    Draw one month's incident out of the pool, or draw the quiet month.

    A query over candidates rather than a pick from the whole tuple: an entry says for itself
    whether it can happen to this faction at all, which is what lets a cost check the treasury and a
    loss check that there is something losable. An omen (#74) joins the pool as another row without
    this step changing.

    Nothing happening is a weight in that draw, not a branch around it. Two things follow: the odds
    of a quiet month are one number somebody chose rather than a side effect of how many entries
    exist, and a month with no possible candidate is quiet for the same reason as any other.
    """
    candidates = [incident for incident in INCIDENTS if incident.is_possible(faction=context.faction)]

    # "None" stands in the pool for the quiet month, so it is drawn the same way the incidents are
    chosen_incident = random.choices(
        (None, *candidates),
        weights=(QUIET_MONTH_WEIGHT, *[incident.WEIGHT for incident in candidates]),
    )[0]

    if chosen_incident is None:
        return None

    return IncidentOccurred(
        faction=context.faction,
        month=context.month,
        outcome=chosen_incident.resolve(faction=context.faction),
    )
