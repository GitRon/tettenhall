from dataclasses import dataclass
from enum import StrEnum

from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame


class AttackRefusal(StrEnum):
    """
    Why a rival who is still standing may not be marched on, ranked.

    The order is the rule, the way "get_dismissal_refusals" orders its own: the first reason that
    applies is the one the player is told. A decided savegame is why nothing of his marches, whatever
    month it stopped in. A war band that has fought comes before the leader being unfit, because the
    spent month is the reason whoever leads it, and a leader who fell in that fight is not the reason
    the player should be given. And the rival's men being spoken for is only ever said
    once the player could otherwise have marched, or it blames the rival for a refusal that is nothing
    to do with them.
    """

    SAVEGAME_IS_OVER = "savegame_is_over"
    HAS_MARCHED_THIS_MONTH = "has_marched_this_month"
    LEADER_CANNOT_MARCH = "leader_cannot_march"
    WAR_BAND_IS_COMMITTED = "their_war_band_is_committed"


@dataclass(frozen=True, kw_only=True)
class AttackStanding:
    """
    Who the player may march on this month, and why not for everybody still standing whom he may not.

    "refusals" holds only rivals of [Faction.objects.rivals_still_standing] that are not attackable.
    Anything outside that queryset never offered a fight in the first place - the player's own faction,
    one already knocked out - and a sentence explaining a button that was never there would be a non
    sequitur.

    "war_band_refusal" is the reason that is about the player's own war band rather than any one rival,
    which the rivals list says once above its table instead of on every row. None while no standing
    rival is refused, so over a cleared board it explains nothing.
    """

    attackable_rival_ids: frozenset[int]
    refusals: dict[int, AttackRefusal]
    war_band_refusal: AttackRefusal | None


def get_attack_standing(*, savegame: Savegame) -> AttackStanding:
    """
    The one answer to "who may be attacked, and why not" for every page that offers or withholds an
    Attack control.

    Asked once for the whole savegame and answered out of sets, because the rivals list renders a row
    per rival and a lookup per row is a query per row. The faction page reads the same answer for its
    one rival, so the two pages cannot word the rule differently.

    The attackable set is "attackable_by", which is the queryset the attack view resolves its target
    with - a button offered here and the page it leads to cannot disagree.
    """
    player_faction = savegame.player_faction
    if player_faction is None:
        return AttackStanding(attackable_rival_ids=frozenset(), refusals={}, war_band_refusal=None)

    attackable_rival_ids = frozenset(Faction.objects.attackable_by(savegame=savegame).values_list("id", flat=True))
    refused_rival_ids = (
        set(Faction.objects.rivals_still_standing(player_faction=player_faction).values_list("id", flat=True))
        - attackable_rival_ids
    )
    if not refused_rival_ids:
        return AttackStanding(attackable_rival_ids=attackable_rival_ids, refusals={}, war_band_refusal=None)

    war_band_refusal = _get_war_band_refusal(savegame=savegame, player_faction=player_faction)

    return AttackStanding(
        attackable_rival_ids=attackable_rival_ids,
        # Fit, free and still refused leaves only the rival's own men in the way: "attackable_targets"
        # is narrower than "rivals_still_standing" by exactly the "already in a fight" rule
        refusals=dict.fromkeys(refused_rival_ids, war_band_refusal or AttackRefusal.WAR_BAND_IS_COMMITTED),
        war_band_refusal=war_band_refusal,
    )


def _get_war_band_refusal(*, savegame: Savegame, player_faction: Faction) -> AttackRefusal | None:
    """
    The reason the player's own war band cannot march on anybody, or None if it could.

    The spent month first, asked of the faction's fights rather than of the man leading it now - a
    successor seated after the march is free and fit, and still leads nobody out again this month.
    Only then the leader: unavailable without a march behind him means wounded or routed, and the
    sentence says what the player can do about it - mend him.
    """
    if savegame.is_over:
        return AttackRefusal.SAVEGAME_IS_OVER

    month = savegame.current_month
    if player_faction.has_marched_this_month(month=month):
        return AttackRefusal.HAS_MARCHED_THIS_MONTH

    if player_faction.get_available_leader(month=month) is None:
        return AttackRefusal.LEADER_CANNOT_MARCH

    return None
