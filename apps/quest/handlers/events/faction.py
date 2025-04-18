from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.quest import NewBulletinBoardQuestRequired
from apps.quest.messages.commands.quest import CreateNewQuest


@message_registry.register_event(event=NewBulletinBoardQuestRequired)
def handle_new_bulletin_board_quest_required(*, context: NewBulletinBoardQuestRequired) -> Command:
    return CreateNewQuest(savegame=context.savegame, faction=context.faction, month=context.month)
