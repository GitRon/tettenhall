import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.marketplace.messages.commands.quest import OfferNewQuestsOnBoard
from apps.marketplace.messages.events.quest import NewQuestsOffered
from apps.quest.messages.commands.quest import AcceptQuest
from apps.quest.messages.events.quest import QuestAccepted
from apps.quest.models.quest_contract import QuestContract
from apps.quest.services.generators.quest import QuestGenerator


@message_registry.register_command(command=OfferNewQuestsOnBoard)
def handle_offer_quests(*, context: OfferNewQuestsOnBoard) -> list[Event] | Event:
    # Clean up previous quests
    context.marketplace.available_quests.all().delete()

    no_items = random.randrange(1, 4)
    for _ in range(no_items):
        quest_generator = QuestGenerator(savegame=context.marketplace.savegame)
        quest = quest_generator.process()
        context.marketplace.available_quests.add(quest)

    return NewQuestsOffered(marketplace=context.marketplace, month=context.month)


@message_registry.register_command(command=AcceptQuest)
def handle_accept_quest(*, context: AcceptQuest) -> list[Event] | Event:
    quest_contract = QuestContract.objects.create(
        faction=context.accepting_faction, quest=context.quest, accepted_in_month=context.month
    )
    quest_contract.assigned_warriors.add(*context.assigned_warriors)

    return QuestAccepted(
        accepting_faction=context.accepting_faction,
        quest=context.quest,
        quest_contract=quest_contract,
    )
