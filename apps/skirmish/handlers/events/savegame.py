from queuebie import message_registry
from queuebie.messages import Command

from apps.savegame.messages.events.savegame import SavegameEnded
from apps.savegame.models.savegame import Savegame
from apps.skirmish.messages.commands.skirmish import WinSkirmish


@message_registry.register_event(event=SavegameEnded)
def handle_win_open_skirmishes_when_the_game_ends(*, context: SavegameEnded) -> list[Command]:
    """
    Decides the fight the game ended in, in favour of whichever side the outcome already favours.

    It goes through WinSkirmish like any other victory rather than just stamping a victor on the row,
    so the loot, the prisoners, the experience and the quest contract all behave the way they would
    have if the fight had run its course.
    """
    message_list = []

    for skirmish in context.open_skirmish_list:
        message_list.append(
            WinSkirmish(
                skirmish=skirmish,
                victorious_faction=(
                    skirmish.player_faction
                    if context.outcome == Savegame.OutcomeChoices.OUTCOME_WON
                    else skirmish.non_player_faction
                ),
                month=context.month,
            )
        )

    return message_list
