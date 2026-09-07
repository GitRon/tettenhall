from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import ChangeFyrdReserve
from apps.finance.messages.commands.transaction import CreateTransaction
from apps.incident.messages.events.incident import IncidentOccurred
from apps.item.messages.commands.item import LoseItem
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.models.player_month_log import PlayerMonthLog
from apps.warrior.messages.commands.warrior import ChangeWarriorMaxMorale

# One handler per lever, each refusing an outcome that does not name its own. An incident is applied
# by the apps that own the rows it moves, never by the one that chose it - so what a new entry costs
# is a class, and what a new lever costs is a field and a handler here.


@message_registry.register_event(event=IncidentOccurred)
def handle_write_incident_to_month_log(*, context: IncidentOccurred) -> Command:
    """
    The only reaction every incident has: the player reads about it.

    One kind for all of them, so the chronicle is a weight in the log rather than twelve kinds
    nobody groups by, and the body is the sentence the title had no room for.
    """
    return CreatePlayerMonthLog(
        title=context.outcome.title,
        body=context.outcome.body,
        kind=PlayerMonthLog.KindChoices.KIND_INCIDENT,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_silver(*, context: IncidentOccurred) -> Command | None:
    """
    What the incident cost or brought, as a ledger row like any other.

    The title is the reason, so the ledger reads as the chronicle does rather than as
    "Incident #7" - both columns hold at most 100 characters, so the one fits the other.
    """
    if context.outcome.silver_change == 0:
        return None

    return CreateTransaction(
        reason=context.outcome.title,
        amount=context.outcome.silver_change,
        faction=context.faction,
        month=context.month,
    )


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_fyrd_reserve(*, context: IncidentOccurred) -> Command | None:
    if context.outcome.fyrd_change == 0:
        return None

    return ChangeFyrdReserve(
        faction=context.faction,
        change=context.outcome.fyrd_change,
        month=context.month,
    )


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_max_morale(*, context: IncidentOccurred) -> Command | None:
    """
    A permanent change to one man's morale ceiling.

    Keyed on the share rather than on the warrior: an entry may name a man for its title without
    touching his nerve, and the man an incident happened to is not always the lever it pulls.
    """
    if context.outcome.max_morale_share == 0:
        return None

    return ChangeWarriorMaxMorale(
        warrior=context.outcome.warrior,
        faction=context.faction,
        share=context.outcome.max_morale_share,
        month=context.month,
    )


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_lost_item(*, context: IncidentOccurred) -> Command | None:
    if context.outcome.lost_item is None:
        return None

    return LoseItem(
        faction=context.faction,
        item=context.outcome.lost_item,
        month=context.month,
    )
