from apps.warband.faction.models import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.town.models import Town

# What the village pays, and what it pays with. Flat, and once a month: the same trade the thegn offers
# unasked in ThegnBuysOutHisSons, here asked for by the player when he needs it
GELD_SILVER = 80
GELD_FYRD_NAMES = 1

ALREADY_GELDED_THIS_MONTH_REFUSAL = "The village has already paid a geld this month."
EMPTY_FYRD_REFUSAL = "There is nobody left on the fyrd roll to strike off for a geld."


def get_geld_refusal(*, town: Town, faction: Faction, current_savegame: Savegame) -> str | None:
    """
    Why this town may not call a geld on its village now, or None if it may.

    First refusal wins, the month before the roll, in the order the feast reports its own: the month is
    over when it is over, while the roll may be refilled by the month turning or an incident.

    This is the first of two enforcement points; "handle_call_geld" re-checks both, the month as a
    conditional UPDATE and the roll as a read under the request's write lock.
    """
    if town.last_geld_at == current_savegame.current_month:
        return ALREADY_GELDED_THIS_MONTH_REFUSAL

    if faction.fyrd_reserve < GELD_FYRD_NAMES:
        return EMPTY_FYRD_REFUSAL

    return None
