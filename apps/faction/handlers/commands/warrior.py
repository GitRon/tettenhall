from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.messages.events.warrior import WarriorRecruited
from apps.faction.models.faction import Faction
from apps.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator


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
