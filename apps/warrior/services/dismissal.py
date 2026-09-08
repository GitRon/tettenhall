from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior

LEADER_REFUSAL = "Your leader stays. Losing him is losing the war band."
BUSY_REFUSAL = "He is spoken for this month. You can send him away once it is over."
UNAFFORDABLE_REFUSAL = "You don't have the silver to pay him off."


def get_dismissal_refusals(
    *, faction: Faction, warrior_list: list[Warrior], month: int, balance: int
) -> dict[int, str]:
    """
    Why each of these men may not be sent away, keyed by warrior id and holding only the ones who
    may not go.

    Asked about a roster at a time rather than a man at a time, because the page offering the control
    renders a card per warrior and one query per card is one query per card - the same reason
    "RivalFactionListView" answers its per-row questions out of sets. The view dispatching the
    command asks this with a single-man list, so the card and the click go through one function and
    cannot come to different conclusions about the same warrior.

    The order of the guards is a rule rather than the order they were written in, the way
    "get_building_upgrade_refusal" orders its own: the thing the player can do least about is named
    first. Nothing will ever make his leader dismissible, the month will end on its own, and the
    price is the one he can go and raise silver for - so a man who is both busy and unaffordable is
    told about the month, and sent off to sell something only once that is no longer the reason.
    """
    warrior_id_list = [warrior.id for warrior in warrior_list]

    # One query for the whole roster. "exclude_currently_busy" is the game's existing definition of
    # busy - signed on to a quest this month, or standing on the roster of a fight - and a man
    # dismissed out of one of those leaves a skirmish pointing at a warrior with no faction.
    free_warrior_ids = set(
        Warrior.objects.filter(id__in=warrior_id_list).exclude_currently_busy(month=month).values_list("id", flat=True)
    )

    refusals = {}

    for warrior in warrior_list:
        if warrior.id == faction.leader_id:
            refusals[warrior.id] = LEADER_REFUSAL
        elif warrior.id not in free_warrior_ids:
            refusals[warrior.id] = BUSY_REFUSAL
        elif balance < warrior.severance_pay:
            refusals[warrior.id] = UNAFFORDABLE_REFUSAL

    return refusals
