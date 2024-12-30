from django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor import RelatedObjectDoesNotExist

from apps.core.domain import message_registry
from apps.finance.models import Transaction
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishCreated)
def handle_link_quest_contract_to_its_skirmish(*, context: skirmish.SkirmishCreated.Context):
    quest_contract = context.quest_contract
    quest_contract.skirmish = context.skirmish
    quest_contract.save()


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_finish_quest_contract(*, context: skirmish.SkirmishFinished.Context) -> None:
    victorious_faction = context.skirmish.victorious_faction
    try:
        quest_contract = context.skirmish.quest_contract
    except RelatedObjectDoesNotExist:
        # There might be skirmishes with no assigned quest contract
        return

    # If the player won the quest contracts skirmish, they get the loot
    if context.skirmish.quest_contract.faction == victorious_faction:
        Transaction.objects.create_transaction(
            faction=victorious_faction,
            amount=quest_contract.quest.loot,
            reason=f"Quest {quest_contract.quest.name!r} finished! {quest_contract.quest.loot} silver looted.",
        )
