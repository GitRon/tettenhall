from queuebie import message_registry
from queuebie.messages import Event

from apps.town.messages.commands.town import UpgradeTownBuilding
from apps.town.messages.events.town import TownBuildingUpgraded
from apps.town.models import Town


@message_registry.register_command(command=UpgradeTownBuilding)
def handle_upgrade_town_building(*, context: UpgradeTownBuilding) -> Event | None:
    # One conditional UPDATE rather than read-modify-save, so the once-per-month rule survives two
    # overlapping requests. The view checks the same guard to give the player a message, but both
    # requests pass that check on a double-clicked button, and only one of them may be charged.
    upgraded_rows = (
        Town.objects.filter(pk=context.town.pk)
        .exclude(last_constructed_building_at=context.month)
        .update(**{context.building_type: context.new_level}, last_constructed_building_at=context.month)
    )
    if not upgraded_rows:
        return None

    # The UPDATE went around the instance, so bring it in line for the handlers downstream
    setattr(context.town, context.building_type, context.new_level)
    context.town.last_constructed_building_at = context.month

    return TownBuildingUpgraded(
        town=context.town,
        faction=context.faction,
        building_type=context.building_type,
        new_level=context.new_level,
        costs=context.costs,
        month=context.month,
    )
