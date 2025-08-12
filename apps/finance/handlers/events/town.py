from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.town.messages.events import town


@message_registry.register_event(event=town.TownBuildingUpgraded)
def handle_pay_building_costs_for_town_buildings(*, context: town.TownBuildingUpgraded) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=-context.costs,
        reason=f"Building {context.building_type!r} level {context.new_level} constructed.",
        month=context.month,
    )
