from django.core.exceptions import ObjectDoesNotExist

from apps.core.domain import message_registry
from apps.finance.models import Transaction
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishCreated)
def handle_link_quest_contract_to_its_skirmish(*, context: skirmish.SkirmishCreated.Context) -> None:
    quest_contract = context.quest_contract
    quest_contract.skirmish = context.skirmish
    quest_contract.save()


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_finish_quest_contract(*, context: skirmish.SkirmishFinished.Context) -> None:
    # TODO: fixme
    # TODO: commands dürfen nicht in anderen apps importiert werden, nur events
    # TODO: commands machen explizit, wie services/BL miteinander redet, events sind für cross-app concerns
    # emit command FinishQuestContract
    #  -> QuestContractFinished emitted -> Transaction lauscht darauf, sonst würde ich das Command übergeben cross-app
    #    -> CreateTransaction(reason="Quest finished", loot=543) für victorious faction, nicht nur für mich
    #    -> Fraction hat Quest nicht mehr aktiv
    #    -> ...

    victorious_faction = context.skirmish.victorious_faction
    try:
        quest_contract = context.skirmish.quest_contract
    except ObjectDoesNotExist:
        # There might be skirmishes with no assigned quest contract
        return

    # Unset active quest in faction
    context.skirmish.player_faction.active_quests.remove(quest_contract)

    # If the player won the quest contracts skirmish, they get the loot
    if context.skirmish.quest_contract.faction == victorious_faction:
        Transaction.objects.create_transaction(
            faction=victorious_faction,
            amount=quest_contract.quest.loot,
            reason=f"Quest {quest_contract.quest.name!r} finished! {quest_contract.quest.loot} silver looted.",
        )
