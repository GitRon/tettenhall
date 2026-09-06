import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.messages.events.quest import BulletinBoardQuestsOffered, NewBulletinBoardQuestRequired


@message_registry.register_command(command=OfferNewQuestsOnBulletinBoard)
def handle_offer_quests(*, context: OfferNewQuestsOnBulletinBoard) -> list[Event]:
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
