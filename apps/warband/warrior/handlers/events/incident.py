from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.warrior.messages.commands.warrior import AwardDeedNickname, ChangeWarriorMaxMorale


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_max_morale(*, context: IncidentOccurred) -> Command | None:
    """
    A permanent change to one man's morale ceiling.

    Keyed on the share rather than on the warrior: an entry may name a man for its title without
    touching his nerve, so the man an incident happened to is not always the lever it pulls.
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
def handle_incident_deed_nickname(*, context: IncidentOccurred) -> Command | None:
    """
    One man named for what the incident made him do or carry.

    Keyed on the state rather than on the warrior, for the reason the ceiling handler above is keyed on
    its share: most entries that name a man do not name him for it.
    """
    if context.outcome.nickname_state is None:
        return None

    return AwardDeedNickname(
        warrior=context.outcome.warrior,
        nickname_state=context.outcome.nickname_state,
        month=context.month,
    )
