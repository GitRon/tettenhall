import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.faction import AddWarriorToPub
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RestockTownMercenaries
from apps.faction.messages.events.faction import WarriorWasAddedToPub
from apps.faction.messages.events.warrior import RequestWarriorForPub, WarriorRecruited
from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction
from apps.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_command(command=RestockTownMercenaries)
def handle_restock_pub_mercenaries(*, context: RestockTownMercenaries) -> list[Event] | Event:
    # Clean up previous stock
    context.faction.available_mercenaries.all().delete()

    events = []

    no_warriors = random.randrange(2, 4)
    for _ in range(no_warriors):
        events.append(
            RequestWarriorForPub(
                savegame=context.faction.savegame,
                faction=None,
                culture=Culture.objects.all().order_by("?").first(),
                generator_class=MercenaryWarriorGenerator,
                month=context.month,
            )
        )
        # TODO: create event to show the user that we've finished and let user log listend to it

    return events


@message_registry.register_command(command=AddWarriorToPub)
def handle_add_warrior_to_pub(*, context: AddWarriorToPub) -> list[Event] | Event:
    context.savegame.player_faction.available_mercenaries.add(context.warrior)

    return WarriorWasAddedToPub(faction=context.faction, warrior=context.warrior, month=context.month)


@message_registry.register_command(command=DraftWarriorFromFyrd)
def handle_draft_warrior_from_fyrd(*, context: DraftWarriorFromFyrd) -> list[Event] | Event | None:
    if context.faction.fyrd_reserve <= 0:
        return None

    # Create warrior
    warrior_generator = FyrdWarriorGenerator(
        culture=context.faction.culture, faction=context.faction, savegame_id=context.faction.savegame_id
    )
    warrior = warrior_generator.process()

    # Update reserve
    Faction.objects.reduce_fyrd_reserve(faction=context.faction, drafted_warriors=1)

    return WarriorRecruited(
        faction=context.faction,
        warrior=warrior,
        recruitment_price=0,
        month=context.month,
    )
