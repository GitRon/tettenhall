from django.core.exceptions import ObjectDoesNotExist
from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_victorious_faction_gets_quest_reward(*, context: skirmish.SkirmishFinished) -> Command | None:
    try:
        quest_contract = context.skirmish.quest_contract
    except ObjectDoesNotExist:
        # There might be skirmishes with no assigned quest contract
        # TODO: this shouldn't be handled here that explicitly -> model method?
        return None

    return CreateTransaction(
        faction=context.skirmish.victorious_faction,
        amount=quest_contract.quest.loot,
        reason=f"Quest {quest_contract.quest.name!r} finished! {quest_contract.quest.loot} silver looted.",
        month=context.month,
    )
