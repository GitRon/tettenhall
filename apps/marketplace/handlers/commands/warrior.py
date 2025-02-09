import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.models.culture import Culture
from apps.marketplace.messages.commands.warrior import RestockPubMercenaries
from apps.marketplace.messages.events.warrior import PubMercenariesRestocked
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_command(command=RestockPubMercenaries)
def handle_restock_pub_mercenaries(*, context: RestockPubMercenaries) -> list[Event] | Event:
    # Clean up previous stock
    context.marketplace.available_mercenaries.all().delete()

    no_warriors = random.randrange(2, 4)
    for _ in range(no_warriors):
        warrior_generator = MercenaryWarriorGenerator(
            culture=Culture.objects.all().order_by("?").first(),
            faction=None,
            savegame_id=context.marketplace.savegame.id,
        )
        warrior = warrior_generator.process()

        context.marketplace.available_mercenaries.add(warrior)

    return PubMercenariesRestocked(marketplace=context.marketplace, week=context.week)
