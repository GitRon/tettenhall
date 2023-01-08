import random

from apps.core.domain import event_registry
from apps.core.domain.events import EventConsumer
from apps.skirmish.events import item
from apps.skirmish.models.item import Item


class LootEventConsumer(EventConsumer):

    # todo hier brauch ich n command :D
    @event_registry.register(event=item.ItemLootDropped)
    def handle_warrior_drops_loot(self, context: item.ItemLootDropped):
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
