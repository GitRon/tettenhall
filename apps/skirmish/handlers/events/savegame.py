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

    The skirmish itself only knows an attacking and a defending side, so which of them the outcome
    favours is a question for the savegame: the player faction sits on exactly one of them. Asking it
    costs no query - "player_faction_id" is a column on the savegame already in hand, and the command
    handler raising this event pulls both faction sides in with the skirmishes, which is the query
    strict mode forbids here.
    """
    player_won = context.outcome == Savegame.OutcomeChoices.OUTCOME_WON
    message_list = []

    for skirmish in context.open_skirmish_list:
        # Asked as "is the player the attacker" rather than the other way round on purpose: a savegame
        # with no player faction yet, or - once AI factions fight each other - a skirmish the player is
        # not in at all, must not come out as "the player marched". Those land on the defending side,
        # which is wrong for nobody today, because every skirmish that exists is one the player started
        player_attacks = skirmish.attacking_faction_id == context.savegame.player_faction_id

        message_list.append(
            WinSkirmish(
                skirmish=skirmish,
                victorious_faction=(
                    skirmish.attacking_faction if player_attacks == player_won else skirmish.defending_faction
                ),
                month=context.month,
            )
        )

    return message_list
