from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import NewFactionCreated
from apps.marketplace.messages.commands.quest import OfferNewQuestsOnBoard
from apps.month.messages.events.month import MonthPrepared
from apps.quest.messages.events.quest import QuestAccepted


@message_registry.register_event(event=QuestAccepted)
def handle_removed_accepted_quest_from_available_quests(*, context: QuestAccepted):
    marketplace = context.quest.target_faction.savegame.marketplace
    marketplace.available_quests.remove(context.quest)


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=MonthPrepared)
def handle_offer_new_quests_in_marketplace_for_new_month(
    *, context: MonthPrepared | NewFactionCreated
) -> list[Command]:
    return [OfferNewQuestsOnBoard(marketplace=context.marketplace, month=context.current_month)]
