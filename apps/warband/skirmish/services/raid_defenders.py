import random

from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.raids import RAID_KINDS
from apps.warband.skirmish.raids.base import RaidKind


def get_raid_defenders(*, raid_kind: type[RaidKind], muster: list[Warrior]) -> list[Warrior]:
    """
    Who of "muster" - every man able to defend - stands in the way of a raid of "raid_kind".

    The assault on the burh meets all of them: men fall back behind the wall. A raid out in the shire
    meets only the men who happen to be where it lands. Which place each man stands at is drawn when
    the raid is staged, one place per man out of every raid kind's, and at least one of them always
    stands where the raid falls, so every raid is a fight and no side is ever empty.

    The draw is a stand-in for a faction choosing where its men stand. It comes from the module-level
    "random", over the muster in id order, so a seeded game replays it.
    """
    if raid_kind.IS_FORTIFIED or not muster:
        return list(muster)

    ordered_muster = sorted(muster, key=lambda warrior: warrior.id)
    defenders = [warrior for warrior in ordered_muster if random.choice(RAID_KINDS) is raid_kind]
    if not defenders:
        defenders = [random.choice(ordered_muster)]

    return defenders
