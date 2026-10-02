from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.item.messages.commands.item import CreateItem
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned


@message_registry.register_event(event=QuestContractReturned)
def handle_quest_item(*, context: QuestContractReturned) -> Command | None:
    # Into the stores, owned and unworn, like anything the faction buys: who carries it is the
    # player's to decide
    if context.outcome.item_function is None:
        return None

    return CreateItem(
        owner=context.faction,
        faction=context.faction,
        generator_class=context.outcome.item_generator_class,
        item_function=context.outcome.item_function,
        month=context.month,
        quality_bonus=context.outcome.item_quality_bonus,
    )
