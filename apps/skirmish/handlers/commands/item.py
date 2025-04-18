from queuebie import message_registry
from queuebie.messages import Event

from apps.skirmish.messages.commands import item
from apps.skirmish.messages.events.item import ItemDroppedAsLoot


@message_registry.register_command(command=item.WarriorDropsLoot)
def handle_warrior_drops_loot(*, context: item.WarriorDropsLoot) -> list[Event] | Event:
    message_list = []

    if context.warrior.weapon:
        message_list.append(
            ItemDroppedAsLoot(
                skirmish=context.skirmish,
                warrior=context.warrior,
                item=context.warrior.weapon,
                item_name=context.warrior.weapon.display_name,
                new_owner=context.new_owner,
            )
        )

    if context.warrior.armor:
        message_list.append(
            ItemDroppedAsLoot(
                skirmish=context.skirmish,
                warrior=context.warrior,
                item=context.warrior.armor,
                item_name=context.warrior.armor.display_name,
                new_owner=context.new_owner,
            )
        )

    return message_list
