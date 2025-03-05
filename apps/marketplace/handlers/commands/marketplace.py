from queuebie import message_registry
from queuebie.messages import Event

from apps.marketplace.messages.commands.marketplace import CreateNewMarketplace
from apps.marketplace.messages.events.marketplace import NewMarketplaceCreated
from apps.marketplace.models import Marketplace


@message_registry.register_command(command=CreateNewMarketplace)
def handle_create_new_marketplace(*, context: CreateNewMarketplace) -> list[Event] | Event:
    marketplace = Marketplace.objects.create(town_name=context.town_name, savegame=context.savegame)

    return NewMarketplaceCreated(marketplace=marketplace)
