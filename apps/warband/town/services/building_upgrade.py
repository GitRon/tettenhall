from apps.warband.finance.models import Transaction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.town.buildings import BUILDINGS
from apps.warband.town.models import Town

MAXIMUM_LEVEL_REFUSAL = "You already have the maximum building level."
ALREADY_BUILT_THIS_MONTH_REFUSAL = "You've already commissioned a building this month."
UNAFFORDABLE_REFUSAL = "You don't have the silver to pay for the building."


def get_building_upgrade_refusal(*, town: Town, building_type: str, current_savegame: Savegame) -> str | None:
    """
    Why this town may not raise the next level of "building_type", or None if it may.

    The order of the guards is a rule, not the order the conditions happened to be written in: the
    month is the one the player cannot do anything about until it is over, so a click that trips both
    the month and the price is told about the month. Naming the price instead sends him off to raise
    silver he may not spend yet.

    This is the first of two enforcement points for the month, and the one the player hears from.
    "handle_upgrade_town_building" re-checks it as a conditional UPDATE, which is what keeps two
    overlapping requests from both being charged - see docs/patterns/town-buildings.md.
    """
    building_class = BUILDINGS[building_type]
    current_building_level = getattr(town, building_type)

    # The top level is the last one there is, so this has to stop there - asking for the next one up
    # would leave "get_building_by_type" without a match
    if current_building_level >= building_class.get_max_level():
        return MAXIMUM_LEVEL_REFUSAL

    if town.last_constructed_building_at == current_savegame.current_month:
        return ALREADY_BUILT_THIS_MONTH_REFUSAL

    desired_building = building_class.get_building_by_type(building_type=current_building_level + 1)
    current_silver_balance = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)
    if current_silver_balance < desired_building.BUILDING_COSTS:
        return UNAFFORDABLE_REFUSAL

    return None
