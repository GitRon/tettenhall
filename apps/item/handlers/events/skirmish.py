from queuebie import message_registry
from queuebie.messages import Command

from apps.item.messages.commands.item import ChangeOwnership
from apps.skirmish.messages.events.item import ItemDroppedAsLoot


@message_registry.register_event(event=ItemDroppedAsLoot)
def handle_looted_item_changes_ownership(*, context: ItemDroppedAsLoot) -> Command:
    return ChangeOwnership(previous_owner=context.warrior, item=context.item, new_owner=context.new_owner)
