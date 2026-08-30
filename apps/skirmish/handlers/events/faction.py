from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import FactionWasOccupied
from apps.skirmish.messages.commands.warrior import CaptureWarrior


@message_registry.register_event(event=FactionWasOccupied)
def handle_seize_leader_of_occupied_faction(*, context: FactionWasOccupied) -> Command:
    """
    Takes the leader of an occupied town prisoner where he stands.

    Through the ordinary capture rather than by raising "FactionWasDefeated" here: that would give
    the game a second, independent way to knock a faction out, to be kept in step with the first for
    ever. This way the occupation ends a faction for exactly the reason a lost battle does - its
    leader is gone - and "handle_defeat_faction_of_a_lost_leader" is the only place that decides it.

    No skirmish, because there was no fight. That is what the nullable field on the command is for,
    and the battle-history listener sits the occupation out for the same reason.
    """
    return CaptureWarrior(
        skirmish=None,
        warrior=context.leader,
        capturing_faction=context.occupying_faction,
    )
