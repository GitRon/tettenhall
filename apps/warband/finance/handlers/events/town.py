from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.town.messages.events import town


@message_registry.register_event(event=town.TownBuildingUpgraded)
def handle_pay_building_costs_for_town_buildings(*, context: town.TownBuildingUpgraded) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=-context.costs,
        reason=f"Building {context.building_type!r} level {context.new_level} constructed",
        month=context.month,
    )


@message_registry.register_event(event=town.FeastThrown)
def handle_pay_for_feast(*, context: town.FeastThrown) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=-context.costs,
        reason=f"Feast for {len(context.warrior_list)} {'man' if len(context.warrior_list) == 1 else 'men'}",
        month=context.month,
    )


@message_registry.register_event(event=town.GeldCalled)
def handle_receive_geld(*, context: town.GeldCalled) -> Command:
    return CreateTransaction(
        faction=context.faction,
        amount=context.silver,
        reason="Geld paid by the village",
        month=context.month,
    )
