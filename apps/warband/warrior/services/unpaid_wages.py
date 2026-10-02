from apps.warband.skirmish.models.warrior import Warrior


def get_unpaid_wages_note(*, warrior: Warrior) -> str | None:
    """
    What this man's wage arrears say about him, or None when there is nothing to say.

    The monthly morale sweep skips anybody carrying unpaid months on purpose, so an unpaid man sits
    below his ceiling while every other warrior refills for free. That makes this the one state which
    stops a warrior recovering, and the roster showed no trace of it: the player read a low morale
    figure and no cause.

    Phrased here rather than in the card, because the card is the one place the branches could not be
    tested - view tests assert context, never rendered markup. Which also means the man's standing is
    decided once for the roster grid and the detail page alike.

    The count is said against "UNPAID_MONTHS_UNTIL_WALKOUT" rather than on its own, read off the model
    so the limit stays in one place; the wage-bill warning phrases its own countdown the same way, and
    the player meets one wording in both places. Unlike that warning, this is the clock as it stands
    rather than a projection: it counts the months he has already gone without, not the one the next
    payroll would add.
    """
    # A prisoner and a mercenary on the pub's shelf carry whatever count they had when they left a
    # roster, and nobody owes either of them wages - so the faction is asked before the column is.
    # The leader needs no case of his own: he draws no wage, so he is never owed any.
    if warrior.faction_id is None or warrior.unpaid_months == 0:
        return None

    return f"{warrior.unpaid_months} of {Warrior.UNPAID_MONTHS_UNTIL_WALKOUT} unpaid months"
