import random

from faker import Faker
from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import (
    CreateNewFaction,
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    PayMonthlyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.messages.events.faction import FactionWarriorsWithLowMoraleDetermined
from apps.faction.models import Culture
from apps.month.messages.events.month import MonthPrepared
from apps.savegame.messages.events.savegame import NewSavegameCreated
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale


@message_registry.register_event(event=NewSavegameCreated)
def handle_create_player_faction_for_new_savegame(*, context: NewSavegameCreated) -> list[Command]:
    culture = Culture.objects.get_or_none(id=context.faction_culture_id)
    faker = Faker([culture.locale])
    return [
        CreateNewFaction(
            name=context.faction_name,
            savegame=context.savegame,
            culture_id=context.faction_culture_id,
            is_player_faction=True,
        )
    ] + [
        CreateNewFaction(
            name=faker.city(),
            culture_id=random.choice(Culture.objects.all()).id,
            savegame=context.savegame,
            is_player_faction=False,
        )
        for _ in range(random.randint(3, 5))
    ]


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
def handle_pay_monthly_warrior_salaries_for_new_month(*, context: MonthPrepared) -> Command:
    return PayMonthlyWarriorSalaries(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=MonthPrepared)
def handle_determine_warriors_with_low_morale_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [DetermineWarriorsWithLowMorale(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=MonthPrepared)
def handle_determine_injured_warriors_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [DetermineInjuredWarriors(faction=context.faction, month=context.current_month)]
