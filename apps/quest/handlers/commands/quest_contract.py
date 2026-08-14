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
    # The contract's own faction, asked here rather than carried on the command. The caller used to
    # hand in the skirmish's attacking side, which is only the signatory because the faction that
    # accepts a quest is also the one that marches: clearing the active quest of a faction that never
    # signed it is a silent no-op, so the real holder kept a finished quest forever. Reading the
    # relation is a query, which is why it happens in this command handler and not in the event
    # handler that raises the command.
    faction = context.quest_contract.faction
    faction.active_quests.remove(context.quest_contract)

    return QuestContractAsActiveQuestRemoved(quest_contract=context.quest_contract, faction=faction)
