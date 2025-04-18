from queuebie import message_registry
from queuebie.messages import Event

from apps.quest.messages.commands.quest_contract import AssignSkirmishToQuestContract, RemoveQuestContractAsActiveQuest
from apps.quest.messages.events.quest_contract import QuestContractAsActiveQuestRemoved, SkirmishToQuestContractAssigned


@message_registry.register_command(command=AssignSkirmishToQuestContract)
def handle_assign_skirmish_to_quest_contract(*, context: AssignSkirmishToQuestContract) -> Event:
    quest_contract = context.quest_contract
    quest_contract.skirmish = context.skirmish
    quest_contract.save()

    return SkirmishToQuestContractAssigned(quest_contract=quest_contract)


@message_registry.register_command(command=RemoveQuestContractAsActiveQuest)
def handle_remove_quest_contract_as_active_quest(*, context: RemoveQuestContractAsActiveQuest) -> Event:
    context.faction.active_quests.remove(context.quest_contract)

    return QuestContractAsActiveQuestRemoved(quest_contract=context.quest_contract, faction=context.faction)
