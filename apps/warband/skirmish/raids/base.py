from apps.warband.skirmish.choices.raid_kind import RaidKindChoices


class RaidKind:
    """
    One thing a war band can set out to take when it marches on a rival.

    A kind decides three things about the march, and nothing about the fight itself: the wall the
    defenders stand behind, what a victory takes from the rival on top of the loot of the field, and
    whether a victory opens the town to be ridden into. Who stands in the way is asked of
    "get_raid_defenders", which reads [IS_FORTIFIED] to tell a raid out in the shire from an assault
    on the burh.

    Classes rather than instances, like the calendar months and the town's buildings, which is why
    "do_not_call_in_templates" is set: a template would otherwise call the class and render the
    instance it built. The handlers take their numbers from the constants and [get_effects] words them
    for the attack page, so what the page promises and what the raid takes cannot drift apart.
    """

    do_not_call_in_templates = True

    VALUE: int = 0

    # Whether the defenders fight behind the town's fortification. A raid out in the shire meets them in
    # the open, whatever the town has built
    IS_FORTIFIED = False
    # Whether a victory leaves the town to be ridden into. A raid that is not on the burh bleeds a rival
    # without ending it - see "FactionQuerySet.occupiable_by"
    OPENS_TOWN = False

    # The share of the rival's purse a won raid drives off with, and the most it ever takes. The cap is
    # what keeps a hoarding rival from paying out its whole treasury to one raid
    PURSE_SHARE = 0.0
    PURSE_CAP = 0
    # How many names a won raid strikes off the rival's fyrd reserve
    FYRD_NAMES_BURNED = 0

    @classmethod
    def get_label(cls) -> str:
        return RaidKindChoices(cls.VALUE).label

    @classmethod
    def get_fortification_strength(cls, *, town) -> int:
        """The wall the defenders stand behind on this raid."""
        if not cls.IS_FORTIFIED:
            return 0

        return town.get_fortification_strength()

    @classmethod
    def get_purse_taken(cls, *, balance: int) -> int:
        """What a won raid takes out of a purse holding "balance", never more than is in it."""
        if balance <= 0:
            return 0

        return min(int(balance * cls.PURSE_SHARE), cls.PURSE_CAP)

    @classmethod
    def get_fyrd_names_burned(cls, *, fyrd_reserve: int) -> int:
        """How many names a won raid strikes off a reserve of "fyrd_reserve", never more than there are."""
        return min(cls.FYRD_NAMES_BURNED, fyrd_reserve)

    @classmethod
    def get_skirmish_name(cls, *, target) -> str:
        return f"Attack on {target}"

    @classmethod
    def get_effects(cls) -> tuple[str, ...]:
        """
        One line per thing a won raid of this kind does beyond the loot of the field, in display order.

        Read off the constants, so a kind whose numbers change describes itself.
        """
        effects = []
        if cls.PURSE_SHARE:
            effects.append(f"Drives off {cls.PURSE_SHARE:.0%} of their silver, at most {cls.PURSE_CAP}")
        if cls.FYRD_NAMES_BURNED:
            effects.append(f"Strikes {cls.FYRD_NAMES_BURNED} names off their fyrd")
        if cls.OPENS_TOWN:
            effects.append("Opens the town to be ridden into")
        else:
            effects.append("Leaves the town standing")
        return tuple(effects)
