from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddQuestToBulletinBoard
from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.messages.events.faction import NewFactionCreated
from apps.month.messages.events.month import MonthPrepared
from apps.quest.messages.events.quest import QuestAccepted


@message_registry.register_event(event=QuestAccepted)
def handle_removed_accepted_quest_from_available_quests(*, context: QuestAccepted) -> Command:
    return AddQuestToBulletinBoard(faction=context.accepting_faction, quest=context.quest, month=context.month)


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=MonthPrepared)
def handle_offer_new_quests_on_bulletin_board(*, context: MonthPrepared | NewFactionCreated) -> Command:
    return OfferNewQuestsOnBulletinBoard(faction=context.faction, month=context.current_month)
