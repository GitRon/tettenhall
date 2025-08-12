from queuebie import message_registry
from queuebie.messages import Event

from apps.town.messages.commands.town import UpgradeTownBuilding
from apps.town.messages.events.town import TownBuildingUpgraded


@message_registry.register_command(command=UpgradeTownBuilding)
def handle_upgrade_town_building(*, context: UpgradeTownBuilding) -> list[Event] | Event:
    setattr(context.town, context.building_type, context.new_level)
    context.town.save()

    return TownBuildingUpgraded(
        town=context.town,
        faction=context.faction,
        building_type=context.building_type,
        new_level=context.new_level,
        costs=context.costs,
        month=context.month,
    )
