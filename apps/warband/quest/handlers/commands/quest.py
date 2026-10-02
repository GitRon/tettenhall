from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.quest.messages.commands.quest import AcceptQuest, OfferQuests
from apps.warband.quest.messages.events.quest import QuestAccepted, QuestsOffered
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.services.offer import draw_quests_to_offer


@message_registry.register_command(command=OfferQuests)
def handle_offer_quests(*, context: OfferQuests) -> Event:
    """
    Pin this month's errands to the board, in place of whatever last month's were.

    An offer nobody sent men on lapses with its month: declining is not answering, and there is
    nothing for it to leave behind.
    """
    Quest.objects.filter(faction=context.faction).delete()

    quests = [
        Quest.objects.create(
            faction=context.faction,
            month=context.month,
            quest=entry.__name__,
            title=entry.TITLE,
            body=entry.BODY,
        )
        for entry in draw_quests_to_offer(faction=context.faction)
    ]

    return QuestsOffered(faction=context.faction, quests=quests, month=context.month)


@message_registry.register_command(command=AcceptQuest)
def handle_accept_quest(*, context: AcceptQuest) -> Event | None:
    # The offer leaves the board as its first write, and only the request whose delete takes it may
    # sign the contract: a double click otherwise sends the same men on the same errand twice
    deleted_rows, _ = Quest.objects.filter(pk=context.quest.pk).delete()
    if not deleted_rows:
        return None

    quest_contract = QuestContract.objects.create(
        faction=context.accepting_faction,
        quest=context.quest.quest,
        title=context.quest.title,
        accepted_in_month=context.month,
    )
    quest_contract.assigned_warriors.add(*context.assigned_warriors)

    return QuestAccepted(
        accepting_faction=context.accepting_faction,
        quest_contract=quest_contract,
        assigned_warriors=list(context.assigned_warriors),
        month=context.month,
    )
