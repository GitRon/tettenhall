from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    EarnMoneyFromBuildings,
    PlanFactionMonth,
    PrepareFactionWarriorsForMonth,
    ReplenishFyrdReserve,
)
from apps.warband.faction.messages.commands.warrior import PayMonthlyWarriorSalaries
from apps.warband.faction.messages.events.faction import TownBuildingUpgradeApproved
from apps.warband.month.messages.events.month import FactionMonthPrepared
from apps.warband.savegame.messages.events.savegame import NewSavegameCreated
from apps.warband.town.messages.commands.town import UpgradeTownBuilding


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


# Everything a faction does when a month turns hangs off FactionMonthPrepared, so it applies to the
# player and to his rivals alike, and the declaration order below is the order it happens in: queuebie
# drains the commands one event raises in the order its handlers returned them.
#
# That order is load-bearing for exactly one thing: the warriors' own month comes after the wages, so
# the morale reaction sees the "unpaid_months" the salary run wrote. That write is synchronous, inside
# the salary command handler, which is why the order decides it - and there is a flow test on
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


# Every faction lives on its town, the player and his rivals alike: the hall pays for the men on the
# payroll, and a rival builds its hall the way the player does - see [RivalPolicy]
@message_registry.register_event(event=FactionMonthPrepared)
def handle_earn_money_from_buildings_for_new_month(*, context: FactionMonthPrepared) -> Command:
    return EarnMoneyFromBuildings(faction=context.faction, month=context.current_month)


# Every faction's men get their month, not just the player's: otherwise a faction that survived a
# battle stays crippled for the rest of the game and can never be knocked out again
@message_registry.register_event(event=FactionMonthPrepared)
def handle_prepare_faction_warriors_for_new_month(*, context: FactionMonthPrepared) -> Command:
    return PrepareFactionWarriorsForMonth(faction=context.faction, month=context.current_month)


# Every faction, because every faction's pub restocks behind it - see [handle_plan_faction_month]
@message_registry.register_event(event=FactionMonthPrepared)
def handle_plan_faction_month_for_new_month(*, context: FactionMonthPrepared) -> Command:
    return PlanFactionMonth(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=TownBuildingUpgradeApproved)
def handle_upgrade_town_building_for_approved_upgrade(*, context: TownBuildingUpgradeApproved) -> Command:
    # Pure mapping, because handle_plan_faction_month already weighed the whole decision. That is what
    # lets a rival build through the same command the player's town page dispatches.
    return UpgradeTownBuilding(
        town=context.town,
        faction=context.faction,
        building_type=context.building_type,
        new_level=context.new_level,
        costs=context.costs,
        month=context.month,
    )
