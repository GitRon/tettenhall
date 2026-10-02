from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.raids.base import RaidKind


class LiftTheHerds(RaidKind):
    """Out to the pastures for the rival's cattle, which is silver on the hoof."""

    VALUE = RaidKindChoices.LIFT_THE_HERDS

    PURSE_SHARE = 0.2
    PURSE_CAP = 150

    @classmethod
    def get_skirmish_name(cls, *, target) -> str:
        return f"Raid on the herds of {target}"


class BurnTheVillage(RaidKind):
    """
    Fire in the rival's village. It takes no silver, and it costs the rival the men it would have
    drafted from there.
    """

    VALUE = RaidKindChoices.BURN_THE_VILLAGE

    FYRD_NAMES_BURNED = 2

    @classmethod
    def get_skirmish_name(cls, *, target) -> str:
        return f"Burning of the village of {target}"


class StormTheBurh(RaidKind):
    """The assault on the rival's town itself, behind its wall, and the one raid that can end it."""

    VALUE = RaidKindChoices.STORM_THE_BURH

    IS_FORTIFIED = True
    OPENS_TOWN = True
