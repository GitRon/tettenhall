from django import template

from apps.warband.skirmish.models.battle_history import BattleHistory

register = template.Library()


@register.filter
def casualty_side(log: BattleHistory, player_faction_id: int | None) -> str:  # noqa: PBR001 - a filter is called positionally
    """
    Whose loss a casualty line reports, as the player reads it: "own" when one of his men went down,
    "theirs" when he felled one of the enemy's, and "watched" in a fight between two rivals.

    Losing a man and felling one are both worth reading and are not the same news. In a fight he is
    only watching neither is his, and colouring a stranger's death as a gain would be a lie - which is
    what "player_faction_id" being None says: the view answers it only when he is one of the two sides.
    """
    if player_faction_id is None:
        return "watched"

    return "own" if log.faction_id == player_faction_id else "theirs"
