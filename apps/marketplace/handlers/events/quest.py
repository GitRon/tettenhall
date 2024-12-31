from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.marketplace.messages.commands.quest import OfferNewQuestsOnBoard
from apps.marketplace.models.marketplace import Marketplace
from apps.quest.messages.events.quest import QuestAccepted
from apps.week.messages.events.week import WeekPrepared


@message_registry.register_event(event=QuestAccepted)
def handle_removed_accepted_quest_from_available_quests(*, context: QuestAccepted.Context):
    marketplace = Marketplace.objects.all().first()
    marketplace.available_quests.remove(context.quest)


@message_registry.register_event(event=WeekPrepared)
def handle_offer_new_quests_in_marketplace_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        OfferNewQuestsOnBoard(OfferNewQuestsOnBoard.Context(marketplace=context.marketplace, week=context.current_week))
    ]
