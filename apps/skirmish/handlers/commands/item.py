import random

from apps.core.domain import message_registry
from apps.skirmish.messages.commands import item
from apps.skirmish.messages.events.item import ItemDroppedAsLoot


@message_registry.register_command(command=item.WarriorDropsLoot)
def handle_warrior_drops_loot(context: item.WarriorDropsLoot.Context):
    message_list = []
    # 50% chance that weapon or armor is dropped
    # todo refine this logic
    if context.warrior.weapon and bool(random.getrandbits(1)):
        message_list.append(
            ItemDroppedAsLoot.generator(
                context_data={
                    "skirmish": context.skirmish,
                    "warrior": context.warrior,
                    "item": context.warrior.weapon,
                    "new_owner": context.new_owner,
                }
            )
        )

    if context.warrior.armor and bool(random.getrandbits(1)):
        message_list.append(
            ItemDroppedAsLoot.generator(
                context_data={
                    "skirmish": context.skirmish,
                    "warrior": context.warrior,
                    "item": context.warrior.armor,
                    "new_owner": context.new_owner,
                }
            )
        )

    return message_list
