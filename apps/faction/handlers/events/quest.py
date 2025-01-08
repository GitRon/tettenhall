from apps.core.domain import message_registry
from apps.quest.messages.events.quest import QuestAccepted


@message_registry.register_event(event=QuestAccepted)
def handle_set_active_quest_on_acceptance(*, context: QuestAccepted.Context):
    faction = context.accepting_faction
    faction.active_quests.add(context.quest_contract)
