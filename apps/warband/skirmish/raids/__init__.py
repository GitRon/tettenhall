from apps.warband.skirmish.raids.base import RaidKind
from apps.warband.skirmish.raids.kinds import BurnTheVillage, LiftTheHerds, StormTheBurh

# In the order the attack page offers them: smallest stake first, the town last
RAID_KINDS: tuple[type[RaidKind], ...] = (
    LiftTheHerds,
    BurnTheVillage,
    StormTheBurh,
)


def get_raid_kind(*, value: int) -> type[RaidKind]:
    """The raid kind stored as "value" on a march or a skirmish."""
    for raid_kind in RAID_KINDS:
        if value == raid_kind.VALUE:
            return raid_kind

    raise RuntimeError(f"No raid kind is stored as {value}.")
