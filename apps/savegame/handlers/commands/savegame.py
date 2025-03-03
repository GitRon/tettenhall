from queuebie import message_registry
from queuebie.messages import Event

from apps.savegame.messages.commands.savegame import CreateNewSavegame
from apps.savegame.messages.events.savegame import NewSavegameCreated
from apps.savegame.models.savegame import Savegame


@message_registry.register_command(command=CreateNewSavegame)
def handle_create_new_savegame(*, context: CreateNewSavegame) -> list[Event] | Event:
    # Create savegame object
    savegame = Savegame.objects.create(
        name=f"{context.town_name}/{context.faction_name}",
        created_by_id=context.created_by_id,
    )

    # Set savegame as active savegame and set all others of the current user as inactive
    Savegame.objects.activate_savegame(savegame=savegame)

    return NewSavegameCreated(
        savegame=savegame,
        faction_name=context.faction_name,
        town_name=context.town_name,
        faction_culture_id=context.faction_culture_id,
    )
