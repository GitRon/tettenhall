from apps.core.domain import message_registry
from apps.marketplace.models.marketplace import Marketplace
from apps.quest.messages.events.quest import QuestAccepted


@message_registry.register_event(event=QuestAccepted)
def handle_removed_accepted_quest_from_available_quests(context: QuestAccepted.Context):
    marketplace = Marketplace.objects.all().first()
    marketplace.available_quests.remove(context.quest)
