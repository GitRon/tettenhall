from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    DetermineInjuredWarriors,
    DetermineWarriorsWithReducedMorale,
    EarnMoneyFromBuildings,
    EarnMonthlyFactionIncome,
    PayMonthlyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.messages.commands.warrior import ConsiderFyrdDraft
from apps.faction.messages.events.faction import FactionWarriorsWithReducedMoraleDetermined
from apps.month.messages.events.month import FactionMonthPrepared, PlayerMonthPrepared
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


# Everything a faction does when a month turns hangs off FactionMonthPrepared, so it applies to the
# player and to his rivals alike, and the declaration order below is the order it happens in: queuebie
# drains the commands one event raises in the order its handlers returned them.
#
# That order is load-bearing for exactly one thing: the recovery sweeps come after the wages, so the
# morale one sees the "unpaid_months" the salary run wrote. That write is synchronous, inside the
# salary command handler, which is why the order decides it - and there is a flow test on
# FinishMonthView pinning it.
#
# It decides nothing about the money. A salary run and an income each return an event, and the
# "CreateTransaction" it becomes is queued behind this whole batch, so no ledger row for the month
# lands until every command below has run. That is what makes the wage bill fall on the silver the
# month opened with, which is what the cost card and the navbar promise the player - and it holds
# however these are ordered.
@message_registry.register_event(event=FactionMonthPrepared)
def handle_replenish_fyrd_reserve_for_new_month(*, context: FactionMonthPrepared) -> list[Command]:
    return [ReplenishFyrdReserve(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=FactionMonthPrepared)
def handle_pay_monthly_warrior_salaries_for_new_month(*, context: FactionMonthPrepared) -> Command:
    return PayMonthlyWarriorSalaries(faction=context.faction, month=context.current_month)


# A rival has no buildings, so it earns off its war band instead - and its town sits at every default,
# which would pay it 50 silver against a leader's salary of around 150. The player's half of this is
# the one handler here that stays on PlayerMonthPrepared, further down.
@message_registry.register_event(event=FactionMonthPrepared)
def handle_earn_monthly_faction_income_for_new_month(*, context: FactionMonthPrepared) -> Command:
    return EarnMonthlyFactionIncome(faction=context.faction, month=context.current_month)


# Every faction recovers, not just the player's: otherwise one that survived a battle stays crippled
# for the rest of the game and can never be knocked out again
@message_registry.register_event(event=FactionMonthPrepared)
def handle_determine_warriors_with_reduced_morale_for_new_month(*, context: FactionMonthPrepared) -> list[Command]:
    return [DetermineWarriorsWithReducedMorale(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=FactionMonthPrepared)
def handle_determine_injured_warriors_for_new_month(*, context: FactionMonthPrepared) -> list[Command]:
    return [DetermineInjuredWarriors(faction=context.faction, month=context.current_month)]


@message_registry.register_event(event=FactionMonthPrepared)
def handle_consider_fyrd_draft_for_new_month(*, context: FactionMonthPrepared) -> Command:
    return ConsiderFyrdDraft(faction=context.faction, month=context.current_month)


# The town economy is the thing a rival genuinely has no equivalent of, which is what
# PlayerMonthPrepared is for - so being registered here is the whole of what keeps a rival off the
# hall's revenue, with no guard needed in the command handler.
@message_registry.register_event(event=PlayerMonthPrepared)
def handle_earn_money_from_buildings_for_new_month(*, context: PlayerMonthPrepared) -> Command:
    return EarnMoneyFromBuildings(faction=context.faction, month=context.current_month)
