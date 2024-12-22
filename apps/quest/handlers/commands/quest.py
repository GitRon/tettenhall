import random

from apps.core.domain import message_registry
from apps.marketplace.messages.commands.quest import OfferNewQuestsOnBoard
from apps.marketplace.messages.events.quest import NewQuestsOffered
from apps.quest.messages.commands.quest import AcceptQuest
from apps.quest.messages.events.quest import QuestAccepted
from apps.quest.models.quest_contract import QuestContract
from apps.quest.services.generators.quest import QuestGenerator


@message_registry.register_command(command=OfferNewQuestsOnBoard)
def handle_offer_quests(context: OfferNewQuestsOnBoard.Context):
    # Clean up previous quests
    context.marketplace.available_quests.all().delete()

    no_items = random.randrange(1, 4)
    for _ in range(no_items):
        quest_generator = QuestGenerator()
        quest = quest_generator.process()
        context.marketplace.available_quests.add(quest)

    return NewQuestsOffered.generator(context_data={"marketplace": context.marketplace, "week": context.week})


@message_registry.register_command(command=AcceptQuest)
def handle_accept_quest(context: AcceptQuest.Context):
    # todo: create player week log / other info for user in event "QuestAccepted"?
    # todo: remove quest from marketplace "available_quests" when it was accepted
    quest_contract = QuestContract.objects.create(quest=context.quest)
    quest_contract.assigned_warriors.set(context.assigned_warriors)

    return QuestAccepted.generator(
        context_data={
            "quest": context.quest,
            "assigned_warriors": context.assigned_warriors,
        }
    )
