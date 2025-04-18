from queuebie import message_registry
from queuebie.messages import Command

from apps.item.models.item import Item
from apps.skirmish.messages.commands.item import WarriorDropsLoot
from apps.skirmish.messages.commands.transaction import WarriorDropsSilver
from apps.skirmish.messages.events import item, skirmish
from apps.skirmish.models.warrior import Warrior


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_distribute_loot(*, context: skirmish.SkirmishFinished) -> list[Command]:
    message_list = []

    for warrior in context.incapacitated_warriors:
        # Reassign items
        message_list.append(
            WarriorDropsLoot(
                skirmish=context.skirmish,
                warrior=warrior,
                new_owner=context.skirmish.victorious_faction,
            )
        )
        # Give out money
        message_list.append(
            WarriorDropsSilver(
                skirmish=context.skirmish,
                warrior=warrior,
                gaining_faction=context.skirmish.victorious_faction,
                month=context.month,
            )
        )

    return message_list


@message_registry.register_event(event=item.ItemDroppedAsLoot)
def handle_looted_item_changes_ownership(*, context: item.ItemDroppedAsLoot):
    # Take item away from previous owner
    Warrior.objects.take_item_away(item=context.item)

    # Set ownership in the item itself, so it belongs to the winning faction
    Item.objects.update_ownership(item=context.item, new_owner=context.new_owner)
