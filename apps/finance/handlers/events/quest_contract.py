from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_victorious_faction_gets_quest_reward(*, context: skirmish.SkirmishFinished) -> Command | None:
    if context.quest_loot > 0:
        return CreateTransaction(
            faction=context.skirmish.victorious_faction,
            amount=context.quest_loot,
            reason=f"Quest {context.quest_name!r} finished! {context.quest_loot} silver looted.",
            month=context.month,
        )
    return None
