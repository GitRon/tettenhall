from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.raids.base import RaidKind


def get_raid_defenders(*, raid_kind: type[RaidKind], muster: list[Warrior]) -> list[Warrior]:
    """
    Who of "muster" - every man able to defend - stands in the way of a raid of "raid_kind".

    The assault on the burh meets all of them: men fall back behind the wall. A raid out in the shire
    meets only the men posted where it lands (see "Warrior.posting"). Where nobody of the war band is
    posted, the place's own people still turn out (see "RaidKind.LOCALS_TURNOUT"), so this may come
    back empty; only a place nobody turns out for has the first man of the muster put there, so every
    raid is a fight and no side is ever empty.
    """
    if raid_kind.IS_FORTIFIED or not muster:
        return list(muster)

    ordered_muster = sorted(muster, key=lambda warrior: warrior.id)
    defenders = [warrior for warrior in ordered_muster if warrior.posting == raid_kind.POSTING]
    if not defenders and not raid_kind.LOCALS_TURNOUT:
        defenders = ordered_muster[:1]

    return defenders
