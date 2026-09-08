from apps.warrior.domain.attribute_draw import AttributeDraw

# How far past his own kind's mean a warrior has to reach before he is named for it, and how far
# before the epithet gets stronger, both counted in spreads. Measured over the three generators,
# 13-17% of the men they make earn something and each of the nine states falls between 0.6% and 6.5%,
# so an epithet stays a remark about somebody unusual and the stronger one stays worth reading. Moving
# the far threshold out to 2.75 drops it under half a percent, which is a state a player would never
# meet.
NICKNAME_SPREAD_THRESHOLD = 2.0
NICKNAME_FAR_SPREAD_THRESHOLD = 2.5

# Several wordings per state, so a war band of strong men does not read as one man repeated. They are
# synonyms and carry no information the state does not: which of them a warrior gets is his stored
# "nickname_variant", so he is called the same thing on every page and for the rest of the savegame.
STRENGTH_NICKNAMES = ("the Strong", "the Stout")
STRENGTH_FAR_NICKNAMES = ("the Mighty", "the Bear", "the Ox")
DEXTERITY_NICKNAMES = ("the Quick", "the Deft")
DEXTERITY_FAR_NICKNAMES = ("the Lightning", "the Hare")
HEALTH_NICKNAMES = ("the Tough", "the Hale")
HEALTH_FAR_NICKNAMES = ("the Ironhide", "the Boar")
MORALE_NICKNAMES = ("the Brave", "the Bold")
MORALE_FAR_NICKNAMES = ("the Fearless", "the Wolfheart")
FLOOR_NICKNAMES = ("the Weak", "the Frail", "the Reed")

# The stored variant is reduced modulo whichever wording list it lands in, so the bound has to be a
# common multiple of the list lengths for every wording to be equally likely. Two and three both
# divide six.
NICKNAME_VARIANT_BOUND = 6


def get_nickname(
    *,
    strength: AttributeDraw,
    dexterity: AttributeDraw,
    health: AttributeDraw,
    morale: AttributeDraw,
    stats_minimum: int,
    variant: int,
) -> str | None:
    """
    The epithet a warrior has earned for how his attributes came out, or None if he is an ordinary
    man.

    Measured against the distributions he was drawn from rather than against fixed numbers, because
    the archetypes share neither their means nor their spreads: a fyrd man reaching nine strength is a
    monster among his own kind and a mercenary reaching nine is unremarkable. Counted in spreads, all
    three archetypes earn epithets at comparable rates.

    Only the attribute that reached furthest is named, and a dead heat goes to the earlier of the four
    - the order they are declared in, which is the order they sit on the warrior.

    **The two directions are not mirror images, because the distributions are not.** Upwards every
    tail runs free and two spreads past the mean is a genuine rarity. Downwards there is no tail to
    measure. "STATS_MIN" floors strength and dexterity, and the mass that would have been the left
    tail sits on the floor itself - a quarter of every fyrd man's and every mercenary's rolls land
    exactly there. Health and morale are not floored but re-rolled while zero, which truncates them
    just as hard: two spreads below the mean is a negative figure for a fyrd man's health and zero for
    a mercenary's, and zero is the one value the generator refuses. So a threshold below the mean is
    either unreachable or it collects the whole heap at once.

    Being feeble is therefore not a distance but a position: the man rolled as badly as his kind can
    roll, in both of the two attributes that have a floor at all. That is 1.4% of leaders and about 6%
    of everyone else, which is the rate the upward direction has. It reads correctly too - a war
    band's leader is seldom a weakling.

    Which is also why there is no unflattering epithet per attribute. A man at the floor in both is
    not clumsy in particular; he is simply the worst his kind produces.
    """
    candidates = (
        (strength, STRENGTH_NICKNAMES, STRENGTH_FAR_NICKNAMES),
        (dexterity, DEXTERITY_NICKNAMES, DEXTERITY_FAR_NICKNAMES),
        (health, HEALTH_NICKNAMES, HEALTH_FAR_NICKNAMES),
        (morale, MORALE_NICKNAMES, MORALE_FAR_NICKNAMES),
    )
    # "max" hands back the first of equal candidates, so declaration order is the tie-break
    furthest, nicknames, far_nicknames = max(candidates, key=lambda candidate: candidate[0].reach)

    if furthest.reach >= NICKNAME_FAR_SPREAD_THRESHOLD:
        chosen = far_nicknames
    elif furthest.reach >= NICKNAME_SPREAD_THRESHOLD:
        chosen = nicknames
    # At or below the floor rather than on it: training only ever raises an attribute, so nothing
    # generated sits underneath its own minimum, but the epithet should not hinge on that staying true
    elif strength.value <= stats_minimum and dexterity.value <= stats_minimum:
        chosen = FLOOR_NICKNAMES
    else:
        return None

    return chosen[variant % len(chosen)]
