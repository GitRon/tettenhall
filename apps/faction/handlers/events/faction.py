from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    DetermineInjuredWarriors,
    DetermineWarriorsWithReducedMorale,
    EarnMoneyFromBuildings,
    PayMonthlyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.messages.events.faction import FactionWarriorsWithReducedMoraleDetermined
from apps.month.messages.events.month import MonthPrepared, RivalFactionMonthPrepared
from apps.savegame.messages.events.savegame import NewSavegameCreated
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale


@message_registry.register_event(event=NewSavegameCreated)
def handle_create_player_faction_for_new_savegame(*, context: NewSavegameCreated) -> Command:
    # Naming the rival factions needs the cultures from the database, and strict mode blocks
    # database access in event handlers, so the command handler does the reading
    return CreateFactionsForNewSavegame(
        savegame=context.savegame,
        faction_name=context.faction_name,
        town_name=context.town_name,
        faction_culture_id=context.faction_culture_id,
    )


@message_registry.register_event(event=FactionWarriorsWithReducedMoraleDetermined)
def handle_warriors_with_reduced_morale_determined(
    *, context: FactionWarriorsWithReducedMoraleDetermined
) -> list[Command]:
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
def handle_earn_money_from_buildings_for_new_month(*, context: MonthPrepared) -> Command:
    return EarnMoneyFromBuildings(faction=context.faction, month=context.current_month)


# Rivals recover between months as well, otherwise a faction that survived one battle stays crippled
# for the rest of the game and can never be knocked out
@message_registry.register_event(event=RivalFactionMonthPrepared)
@message_registry.register_event(event=MonthPrepared)
def handle_determine_warriors_with_reduced_morale_for_new_month(
    *, context: MonthPrepared | RivalFactionMonthPrepared
) -> list[Command]:
    return [DetermineWarriorsWithReducedMorale(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=RivalFactionMonthPrepared)
@message_registry.register_event(event=MonthPrepared)
def handle_determine_injured_warriors_for_new_month(
    *, context: MonthPrepared | RivalFactionMonthPrepared
) -> list[Command]:
    return [DetermineInjuredWarriors(faction=context.faction, month=context.current_month)]
