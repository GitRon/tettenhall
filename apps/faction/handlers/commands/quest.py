import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.messages.events.quest import BulletinBoardQuestsOffered, NewBulletinBoardQuestRequired


@message_registry.register_command(command=OfferNewQuestsOnBulletinBoard)
def handle_offer_quests(*, context: OfferNewQuestsOnBulletinBoard) -> list[Event]:
    # The bulletin board is the player's alone: QuestAcceptView is scoped to his faction, no game
    # rule reads a rival's board, and QuestGenerator picks its target with the player excluded - so
    # the cards a rival got would name other rivals, chosen by logic that only makes sense for him.
    # Offering to a rival - which NewFactionCreated does for each of them - is a board nothing
    # refreshes and nobody can act on. The guard belongs here because the producers are event
    # handlers, where strict mode's database blocker forbids the traversal below; this command
    # handler may query, and every producer passes through it.
    if context.faction.savegame.player_faction_id != context.faction.id:
        return []

    # Clean up previous quests
    context.faction.available_quests.all().delete()

    events = []
    no_items = random.randrange(1, 4)
    for _ in range(no_items):
        events.append(
            NewBulletinBoardQuestRequired(
                savegame=context.faction.savegame, faction=context.faction, month=context.month
            )
        )

    # After the loop, and counting the whole board rather than each quest: the player wants to know
    # whether it is worth walking over, not that a slot was filled
    events.append(BulletinBoardQuestsOffered(faction=context.faction, new_quests=no_items, month=context.month))

    return events
