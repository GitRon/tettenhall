from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.quest.messages.commands.quest_contract import (
    AssignSkirmishToQuestContract,
    RemoveQuestContractAsActiveQuest,
)
from apps.warband.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishCreated)
def handle_link_quest_contract_to_its_skirmish(*, context: skirmish.SkirmishCreated) -> Command | None:
    # Not every skirmish comes from a quest: attacking a rival faction creates one without a
    # contract, and there is nothing to link then
    if context.quest_contract is None:
        return None

    return AssignSkirmishToQuestContract(quest_contract=context.quest_contract, skirmish=context.skirmish)


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_finish_quest_contract(*, context: skirmish.SkirmishFinished) -> Command | None:
    # An attack on a rival is fought for nobody's contract, and there is nothing to close then
    if context.quest_contract is None:
        return None

    return RemoveQuestContractAsActiveQuest(quest_contract=context.quest_contract)
