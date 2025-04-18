from django.core.exceptions import ObjectDoesNotExist
from queuebie import message_registry
from queuebie.messages import Command

from apps.quest.messages.commands.quest_contract import AssignSkirmishToQuestContract
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishCreated)
def handle_link_quest_contract_to_its_skirmish(*, context: skirmish.SkirmishCreated) -> Command:
    return AssignSkirmishToQuestContract(quest_contract=context.quest_contract, skirmish=context.skirmish)


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_finish_quest_contract(*, context: skirmish.SkirmishFinished) -> None:
    # TODO: fixme
    # TODO: commands dürfen nicht in anderen apps importiert werden, nur events
    # TODO: commands machen explizit, wie services/BL miteinander redet, events sind für cross-app concerns
    # emit command FinishQuestContract
    #  -> QuestContractFinished emitted -> Transaction lauscht darauf, sonst würde ich das Command übergeben cross-app
    #    -> CreateTransaction(reason="Quest finished", loot=543) für victorious faction, nicht nur für mich
    #    -> Fraction hat Quest nicht mehr aktiv
    #    -> ...

    try:
        quest_contract = context.skirmish.quest_contract
    except ObjectDoesNotExist:
        # There might be skirmishes with no assigned quest contract
        return

    # Unset active quest in faction
    # TODO: rename handler to reflect that we only do this now and nothing else
    context.skirmish.player_faction.active_quests.remove(quest_contract)
