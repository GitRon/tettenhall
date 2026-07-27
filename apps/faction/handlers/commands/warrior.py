import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.faction import AddWarriorToPub, PayMonthlyWarriorSalaries
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RestockTownMercenaries
from apps.faction.messages.events.faction import MonthlyWarriorSalariesPaid, WarriorWasAddedToPub
from apps.faction.messages.events.warrior import RequestWarriorForPub, WarriorRecruited
from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction
from apps.skirmish.models import Warrior
from apps.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_command(command=RestockTownMercenaries)
def handle_restock_pub_mercenaries(*, context: RestockTownMercenaries) -> list[Event] | Event:
    # Only the player's town has a pub that can be visited, and the mercenaries this requests are
    # generated without a faction of their own, so handle_add_warrior_to_pub can only ever stock
    # that one. Restocking a rival - which NewFactionCreated does for each of them - would add its
    # mercenaries to the player's pub on top of the player's own restock.
    if context.faction.savegame.player_faction_id != context.faction.id:
        return []

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
    # The pub belongs to the player, and there is only one player per savegame, so this is the right
    # target - the warrior arrives here without a faction of its own. handle_restock_pub_mercenaries
    # only requests these for the player faction, so nothing else ends up in this pub.
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


@message_registry.register_command(command=PayMonthlyWarriorSalaries)
def handle_warrior_monthly_salaries(*, context: PayMonthlyWarriorSalaries) -> list[Event] | Event:
    amount = Warrior.objects.get_monthly_salary_for_faction(faction=context.faction)

    return MonthlyWarriorSalariesPaid(
        faction=context.faction,
        amount=amount,
        month=context.month,
    )
