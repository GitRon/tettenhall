from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.faction.messages.commands.faction import (
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    PayWeeklyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.marketplace.messages.commands.item import RestockMarketplaceItems
from apps.marketplace.messages.commands.quest import OfferNewQuestsOnBoard
from apps.marketplace.messages.commands.warrior import RestockPubMercenaries
from apps.training.messages.commands.training import TrainWarriors
from apps.week.messages.events.week import WeekPrepared


@message_registry.register_event(event=WeekPrepared)
def handle_week_prepared(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        # TODO: maybe close all previous messages? do we want to keep them?
        RestockMarketplaceItems(
            RestockMarketplaceItems.Context(marketplace=context.marketplace, week=context.current_week)
        ),
        RestockPubMercenaries(
            RestockPubMercenaries.Context(marketplace=context.marketplace, week=context.current_week)
        ),
        OfferNewQuestsOnBoard(
            OfferNewQuestsOnBoard.Context(marketplace=context.marketplace, week=context.current_week)
        ),
        ReplenishFyrdReserve(ReplenishFyrdReserve.Context(faction=context.faction, week=context.current_week)),
        PayWeeklyWarriorSalaries(PayWeeklyWarriorSalaries.Context(faction=context.faction, week=context.current_week)),
        DetermineWarriorsWithLowMorale(
            DetermineWarriorsWithLowMorale.Context(faction=context.faction, week=context.current_week)
        ),
        DetermineInjuredWarriors(DetermineInjuredWarriors.Context(faction=context.faction, week=context.current_week)),
        TrainWarriors(
            TrainWarriors.Context(faction=context.faction, training=context.training, week=context.current_week)
        ),
    ]
