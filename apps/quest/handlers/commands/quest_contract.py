from queuebie import message_registry
from queuebie.messages import Event

from apps.quest.messages.commands.quest_contract import AssignSkirmishToQuestContract
from apps.quest.messages.events.quest_contract import SkirmishToQuestContractAssigned


@message_registry.register_command(command=AssignSkirmishToQuestContract)
def handle_assign_skirmish_to_quest_contract(*, context: AssignSkirmishToQuestContract) -> Event:
    quest_contract = context.quest_contract
    quest_contract.skirmish = context.skirmish
    quest_contract.save()

    return SkirmishToQuestContractAssigned(quest_contract=quest_contract)
