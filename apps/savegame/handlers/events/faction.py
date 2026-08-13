from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import FactionWasDefeated
from apps.savegame.messages.commands.savegame import DetermineSavegameOutcome


@message_registry.register_event(event=FactionWasDefeated)
def handle_determine_savegame_outcome(*, context: FactionWasDefeated) -> Command:
    # Whether this was the last rival standing, or the player himself, is a question for the database
    return DetermineSavegameOutcome(savegame=context.savegame)
