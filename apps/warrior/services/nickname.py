# How far above his own kind's mean a warrior has to reach before he is named for it, in spreads of
# that same distribution. At two spreads roughly one man in eighteen is exceptional in a given
# attribute, so a flattering epithet stays a remark about somebody unusual.
NICKNAME_SPREAD_THRESHOLD = 2.0

STRENGTH_HIGH_NICKNAME = "the Strong"
DEXTERITY_HIGH_NICKNAME = "the Quick"
BOTH_LOW_NICKNAME = "the Weak"


def get_nickname(*, strength: int, dexterity: int, baseline: int, spread: int, minimum: int) -> str | None:
    """
    The epithet a warrior has earned for how his attributes came out, or None if he is an ordinary
    man.

    Measured against the distribution he was drawn from rather than against fixed numbers, because
    the archetypes share neither a mean nor a spread: a fyrd man reaching nine strength is a monster
    among his own kind and a mercenary reaching nine is unremarkable. Judged in spreads, all three
    earn a flattering epithet at the same rate - between 5% and 7% of the men each generator makes.

    One baseline, spread and minimum serve both attributes: strength and dexterity are drawn from the
    same "STATS_MU"/"STATS_SIGMA"/"STATS_MIN" trio, so what the generator stamped on the warrior for
    his strength describes his dexterity just as well.

    **The two directions are not mirror images, because the distributions are not.** Upwards the tail
    runs free and two spreads above the mean is a genuine rarity. Downwards there is no tail to
    measure: "STATS_MIN" floors the roll, and the mass that would have been the left tail sits on the
    floor itself - a quarter of every fyrd man's and every mercenary's rolls land exactly there. So a
    threshold below the mean is either unreachable (two of the three archetypes have a spread equal to
    their mean, which puts any such cut-off at a negative strength) or it collects that whole heap at
    once. Being feeble is therefore not a distance but a position: the man rolled as badly as his kind
    can roll, in both attributes at once. That is 1.5% of leaders and about 6% of everyone else, which
    is the rate the upward direction has, and it reads correctly - a war band's leader is seldom a
    weakling.

    Which is also why there is no unflattering epithet per attribute. A man at the floor in both is
    not clumsy in particular; he is simply the worst his kind produces.
    """
    cutoff = NICKNAME_SPREAD_THRESHOLD * spread

    # Only the further-out of the two is named, and a dead heat goes to strength
    if strength - baseline >= cutoff and strength >= dexterity:
        return STRENGTH_HIGH_NICKNAME
    if dexterity - baseline >= cutoff:
        return DEXTERITY_HIGH_NICKNAME

    # At or below the floor rather than on it: training only ever raises an attribute, so nothing
    # generated sits underneath its own minimum, but the epithet should not hinge on that staying true
    if strength <= minimum and dexterity <= minimum:
        return BOTH_LOW_NICKNAME

    return None
