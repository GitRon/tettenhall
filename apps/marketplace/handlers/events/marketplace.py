from queuebie import message_registry
from queuebie.messages import Command

from apps.marketplace.messages.commands.marketplace import CreateNewMarketplace
from apps.savegame.messages.events.savegame import NewSavegameCreated


@message_registry.register_event(event=NewSavegameCreated)
def handle_create_new_marketplace_for_new_savegame(*, context: NewSavegameCreated) -> Command:
    return CreateNewMarketplace(
        town_name=context.town_name,
        savegame=context.savegame,
    )
