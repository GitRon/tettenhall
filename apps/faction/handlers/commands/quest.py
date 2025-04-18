import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.messages.events.quest import NewBulletinBoardQuestRequired


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
        # TODO: create event to show the user that we've finished and let user log listend to it

    return events
