from apps.warband.finance.models import Transaction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.town.buildings.hall import Hall
from apps.warband.town.models import Town

NO_HALL_REFUSAL = "There is no hall to feast in. Build one first."
ALREADY_FEASTED_THIS_MONTH_REFUSAL = "Your war band has already feasted this month."
UNAFFORDABLE_FEAST_REFUSAL = "You don't have the silver to feed the whole war band."


def get_feast_refusal(*, town: Town, head_count: int, current_savegame: Savegame) -> str | None:
    """
    Why this town may not throw a feast for "head_count" men now, or None if it may.

    First refusal wins, in the order the building upgrade reports its own: the hall is the thing the
    player can do nothing about this month either, then the month, then the price - naming the price
    first would send him off to raise silver he may not spend yet. A feast is for the whole roster or
    nobody, so a purse short of the full table is refused rather than serving part of it.

    This is the first of two enforcement points for the month; "handle_throw_feast" re-checks it as a
    conditional UPDATE, the way "handle_upgrade_town_building" does.
    """
    hall = Hall.get_building_by_type(building_type=town.hall)
    if not hall.can_feast():
        return NO_HALL_REFUSAL

    if town.last_feast_at == current_savegame.current_month:
        return ALREADY_FEASTED_THIS_MONTH_REFUSAL

    current_silver_balance = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)
    if current_silver_balance < hall.get_feast_price(head_count=head_count):
        return UNAFFORDABLE_FEAST_REFUSAL

    return None


def has_feasted(*, town: Town, month: int) -> bool:
    """
    Whether this town's war band has feasted in "month", read off the row rather than the instance.

    What the feast view asks after it dispatches, so its line describes the table that was laid rather
    than the click: a request that lost its feast to another spend of the same purse is told so instead.
    """
    return Town.objects.filter(pk=town.pk, last_feast_at=month).exists()
