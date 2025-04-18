from queuebie import message_registry
from queuebie.messages import Event

from apps.quest.messages.commands.quest import AcceptQuest, CreateNewQuest
from apps.quest.messages.events.quest import NewQuestCreated, QuestAccepted
from apps.quest.models.quest_contract import QuestContract
from apps.quest.services.generators.quest import QuestGenerator


@message_registry.register_command(command=CreateNewQuest)
def handle_create_new_quest(*, context: CreateNewQuest) -> list[Event] | Event:
    quest_generator = QuestGenerator(savegame=context.savegame)
    quest = quest_generator.process()
    context.faction.available_quests.add(quest)

    return NewQuestCreated(quest=quest, faction=context.faction, month=context.month)


@message_registry.register_command(command=AcceptQuest)
def handle_accept_quest(*, context: AcceptQuest) -> list[Event] | Event:
    quest_contract = QuestContract.objects.create(
        faction=context.accepting_faction, quest=context.quest, accepted_in_month=context.month
    )
    quest_contract.assigned_warriors.add(*context.assigned_warriors)
    context.accepting_faction.active_quests.add(quest_contract)
    context.accepting_faction.available_quests.remove(quest_contract.quest)

    return QuestAccepted(
        accepting_faction=context.accepting_faction,
        target_faction=context.quest.target_faction,
        quest=context.quest,
        quest_contract=quest_contract,
        month=context.month,
    )
