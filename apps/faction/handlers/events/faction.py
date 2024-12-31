from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.faction.messages.commands.faction import (
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    PayWeeklyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.messages.events.faction import FactionWarriorsWithLowMoraleDetermined
from apps.faction.messages.events.warrior import WarriorRecruited, WarriorWasSoldIntoSlavery
from apps.finance.models.transaction import Transaction
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale
from apps.week.messages.events.week import WeekPrepared


@message_registry.register_event(event=FactionWarriorsWithLowMoraleDetermined)
def handle_warriors_with_low_morale_determined(
    *, context: FactionWarriorsWithLowMoraleDetermined.Context
) -> list[Command]:
    event_list = []
    for warrior in context.warrior_list:
        event_list.append(
            ReplenishWarriorMorale(
                ReplenishWarriorMorale.Context(
                    warrior=warrior,
                    week=context.week,
                )
            )
        )
    return event_list


@message_registry.register_event(event=WarriorRecruited)
def handle_warrior_recruited(*, context: WarriorRecruited.Context) -> None:
    # Pay the money
    Transaction.objects.create_transaction(
        reason=f"{context.warrior} recruited", amount=-context.recruitment_price, faction=context.faction
    )


@message_registry.register_event(event=WarriorWasSoldIntoSlavery)
def handle_warrior_sold_into_slavery(*, context: WarriorWasSoldIntoSlavery.Context) -> None:
    # Pay the money
    Transaction.objects.create_transaction(
        reason=f"{context.warrior} was sold into slavery",
        amount=context.warrior.slavery_selling_price,
        faction=context.selling_faction,
    )


@message_registry.register_event(event=WeekPrepared)
def handle_replenish_fyrd_reserve_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [ReplenishFyrdReserve(ReplenishFyrdReserve.Context(faction=context.faction, week=context.current_week))]


@message_registry.register_event(event=WeekPrepared)
def handle_pay_weekly_warrior_salaries_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        PayWeeklyWarriorSalaries(PayWeeklyWarriorSalaries.Context(faction=context.faction, week=context.current_week))
    ]


@message_registry.register_event(event=WeekPrepared)
def handle_determine_warriors_with_low_morale_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        DetermineWarriorsWithLowMorale(
            DetermineWarriorsWithLowMorale.Context(faction=context.faction, week=context.current_week)
        )
    ]


@message_registry.register_event(event=WeekPrepared)
def handle_determine_injured_warriors_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        DetermineInjuredWarriors(DetermineInjuredWarriors.Context(faction=context.faction, week=context.current_week))
    ]
