from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import (
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    PayMonthlyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.messages.events.faction import FactionWarriorsWithLowMoraleDetermined
from apps.month.messages.events.month import MonthPrepared
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale


@message_registry.register_event(event=FactionWarriorsWithLowMoraleDetermined)
def handle_warriors_with_low_morale_determined(*, context: FactionWarriorsWithLowMoraleDetermined) -> list[Command]:
    event_list = []
    for warrior in context.warrior_list:
        event_list.append(
            ReplenishWarriorMorale(
                warrior=warrior,
                month=context.month,
            )
        )
    return event_list


@message_registry.register_event(event=MonthPrepared)
def handle_replenish_fyrd_reserve_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [ReplenishFyrdReserve(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=MonthPrepared)
def handle_pay_monthly_warrior_salaries_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [PayMonthlyWarriorSalaries(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=MonthPrepared)
def handle_determine_warriors_with_low_morale_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [DetermineWarriorsWithLowMorale(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=MonthPrepared)
def handle_determine_injured_warriors_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [DetermineInjuredWarriors(faction=context.faction, month=context.current_month)]
