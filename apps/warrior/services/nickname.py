# How far from his own kind's mean a warrior has to fall before he is named for it, in spreads of
# that same distribution. At 1.5 roughly one man in fifteen is extreme in a given attribute, so an
# epithet stays a remark about someone unusual rather than a label everybody wears.
NICKNAME_SPREAD_THRESHOLD = 1.5

STRENGTH_HIGH_NICKNAME = "the Strong"
STRENGTH_LOW_NICKNAME = "the Weak"
DEXTERITY_HIGH_NICKNAME = "the Quick"
DEXTERITY_LOW_NICKNAME = "the Clumsy"


def get_nickname(*, strength: int, dexterity: int, baseline: int, spread: int) -> str | None:
    """
    The epithet a warrior has earned for an extreme attribute, or None if he is an ordinary man.

    Extreme is measured against the distribution he was drawn from rather than against a fixed
    number, because the archetypes do not share a spread: a fyrd man rolling nine strength is a
    monster among his own kind and a mercenary rolling nine is unremarkable. Absolute cut-offs would
    not merely leave the fyrd plain - "STATS_MIN" is 3 for a mercenary and 4 for a leader, so a low
    cut-off worth having sits underneath both floors and an unflattering epithet would become a
    fyrd-only affair. Judged in spreads, every archetype earns them at the same rate.

    One baseline and one spread serve both attributes: strength and dexterity are drawn from the same
    "STATS_MU"/"STATS_SIGMA" pair, so the mean the generator stamped on the warrior for his strength
    describes his dexterity just as well.

    Only the further-out of the two is named. Comparing the magnitudes before the cut-off is safe
    because the loser cannot be the extreme one - it is the smaller deviation of the two, so
    whichever cut-off it would clear, the winner clears as well. A dead heat goes to strength.
    """
    if abs(strength - baseline) >= abs(dexterity - baseline):
        deviation = strength - baseline
        high_nickname, low_nickname = STRENGTH_HIGH_NICKNAME, STRENGTH_LOW_NICKNAME
    else:
        deviation = dexterity - baseline
        high_nickname, low_nickname = DEXTERITY_HIGH_NICKNAME, DEXTERITY_LOW_NICKNAME

    cutoff = NICKNAME_SPREAD_THRESHOLD * spread

    if deviation >= cutoff:
        return high_nickname
    if -deviation >= cutoff:
        return low_nickname

    return None
