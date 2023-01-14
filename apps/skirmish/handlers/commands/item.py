import random

from apps.core.domain import message_registry
from apps.skirmish.messages.commands import item
from apps.skirmish.models.item import Item


@message_registry.register_command(command=item.ItemLootDropped)
def handle_warrior_drops_loot(context: item.ItemLootDropped):
    spoils_of_war: list[Item] = []
    if bool(random.getrandbits(1)):
        spoils_of_war.append(context.warrior.weapon)
    if bool(random.getrandbits(1)):
        spoils_of_war.append(context.warrior.armor)

    # if spoils_of_war:
    # todo move to battle history consumer and raise event here
    # BattleHistory.objects.create_record(
    #     skirmish=self.skirmish,
    #     message=f"{context.warrior} dropped the following items: {', '.join([str(dropped_item) for
    #     dropped_item in spoils_of_war])}.",
    # )

    return spoils_of_war
