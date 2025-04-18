from django.core.exceptions import ObjectDoesNotExist
from queuebie import message_registry
from queuebie.messages import Command

from apps.quest.messages.commands.quest_contract import AssignSkirmishToQuestContract, RemoveQuestContractAsActiveQuest
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishCreated)
def handle_link_quest_contract_to_its_skirmish(*, context: skirmish.SkirmishCreated) -> Command:
    return AssignSkirmishToQuestContract(quest_contract=context.quest_contract, skirmish=context.skirmish)


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_finish_quest_contract(*, context: skirmish.SkirmishFinished) -> Command | None:
    try:
        quest_contract = context.skirmish.quest_contract
    except ObjectDoesNotExist:
        # There might be skirmishes with no assigned quest contract
        return None

    return RemoveQuestContractAsActiveQuest(quest_contract=quest_contract, faction=context.skirmish.player_faction)
