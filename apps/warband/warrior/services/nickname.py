from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.domain.attribute_draw import AttributeDraw

# How far past his own kind's mean a warrior has to reach before he is named for it, and how far
# before the epithet gets stronger, both counted in spreads. The far threshold sits at 2.5 rather than
# 2.75 because 2.75 puts the stronger wording under half a percent per archetype - a state a player
# would never meet.
NICKNAME_SPREAD_THRESHOLD = 2.0
NICKNAME_FAR_SPREAD_THRESHOLD = 2.5

# And how far below it he has to fall. Further out than the flattering threshold is near, because the
# downward end is compressed: see [draw_nickname_state]. Measured across the three generators, 1.75 is
# the value that keeps every unflattering state between one and six percent for every archetype - at
# 1.5 a leader's nerve fails him a tenth of the time, and at 2.0 a mercenary's health reaches the
# state once in two hundred.
NICKNAME_DESCENT_THRESHOLD = 1.75

# Several wordings per state, so a war band does not read as one man repeated. They are synonyms and
# carry no information the state does not: which of them a warrior gets is his stored
# "nickname_variant", so he is called the same thing on every page and for the rest of the savegame.
STRENGTH_NICKNAMES = ("the Strong", "the Stout")
STRENGTH_FAR_NICKNAMES = ("the Mighty", "the Bear", "the Ox")
DEXTERITY_NICKNAMES = ("the Quick", "the Deft")
DEXTERITY_FAR_NICKNAMES = ("the Lightning", "the Hare")
HEALTH_NICKNAMES = ("the Tough", "the Hale")
HEALTH_FAR_NICKNAMES = ("the Ironhide", "the Boar")
MORALE_NICKNAMES = ("the Brave", "the Bold")
MORALE_FAR_NICKNAMES = ("the Fearless", "the Wolfheart")

STATS_FLOOR_NICKNAMES = ("the Weak", "the Feeble", "the Reed")
HEALTH_LOW_NICKNAMES = ("the Frail", "the Sickly", "the Wisp")
MORALE_LOW_NICKNAMES = ("the Craven", "the Timid", "the Meek")

# The wording a stored state is read back through. The state is what a warrior carries, so editing a
# list here reaches every man already made - which is the whole reason the column holds the state and
# not the string.
NICKNAME_WORDINGS: dict[int, tuple[str, ...]] = {
    NicknameStateChoices.STRENGTH: STRENGTH_NICKNAMES,
    NicknameStateChoices.STRENGTH_FAR: STRENGTH_FAR_NICKNAMES,
    NicknameStateChoices.DEXTERITY: DEXTERITY_NICKNAMES,
    NicknameStateChoices.DEXTERITY_FAR: DEXTERITY_FAR_NICKNAMES,
    NicknameStateChoices.HEALTH: HEALTH_NICKNAMES,
    NicknameStateChoices.HEALTH_FAR: HEALTH_FAR_NICKNAMES,
    NicknameStateChoices.MORALE: MORALE_NICKNAMES,
    NicknameStateChoices.MORALE_FAR: MORALE_FAR_NICKNAMES,
    NicknameStateChoices.STATS_AT_FLOOR: STATS_FLOOR_NICKNAMES,
    NicknameStateChoices.HEALTH_AT_BOTTOM: HEALTH_LOW_NICKNAMES,
    NicknameStateChoices.MORALE_AT_BOTTOM: MORALE_LOW_NICKNAMES,
}

# The stored variant is reduced modulo whichever wording list it lands in, so the bound has to be a
# common multiple of the list lengths for every wording to be equally likely. Two and three both
# divide six.
NICKNAME_VARIANT_BOUND = 6


def _has_fallen_to_the_bottom(*, draw: AttributeDraw) -> bool:
    """
    Whether this attribute came out at the bottom of what its archetype can roll.

    The cut is a distance below the mean like the flattering ones, but clamped to what the generator
    can actually produce, because for half the archetype-attribute pairs in the game the honest
    distance lands underneath the floor. A fyrd man's health is drawn at a mean of ten with a spread of
    ten, so 1.75 spreads below it is a negative figure and the clamp puts the cut on the floor itself,
    where 3% of them sit. A leader's is a mean of twenty against a spread of five, the tail is intact,
    and the cut lands at 11.
    """
    return draw.value <= max(draw.minimum, round(draw.baseline - NICKNAME_DESCENT_THRESHOLD * draw.spread))


def draw_nickname_state(
    *,
    strength: AttributeDraw,
    dexterity: AttributeDraw,
    health: AttributeDraw,
    morale: AttributeDraw,
) -> int | None:
    """
    What a warrior has earned an epithet for from how his attributes stand, or None if he is an
    ordinary man.

    Drawn rather than answered: what comes back is stamped on the warrior and read off him from then
    on, so this runs when a man is generated and when one first crosses a threshold, and never when a
    page renders his name.

    Measured against the distributions he was drawn from rather than against fixed numbers, because
    the archetypes share neither their means nor their spreads: a fyrd man reaching nine strength is a
    monster among his own kind and a mercenary reaching nine is unremarkable. Counted in spreads, all
    three archetypes earn epithets at comparable rates - between 19% and 25% of the men they make.

    **A good roll outranks a bad one.** A man two spreads above his kind in nerve and on the floor in
    both arms is named for the nerve: what he is exceptional at is the more interesting fact, and the
    unflattering states are otherwise the commoner ones and would swallow him.

    Upwards, only the attribute that reached furthest is named, and a dead heat goes to the earlier of
    the four - the order they are declared in, which is the order they sit on the warrior.

    **Downwards the four do not divide the same way, because the distributions do not.** Two of them
    are floored at "STATS_MIN" and the mass that would have been a left tail sits on the floor itself:
    a quarter of every fyrd man's and every mercenary's strength rolls land exactly there, so no
    unflattering epithet taken off strength alone could ever be a remark about somebody unusual. Those
    two are therefore read together - a man at the floor in both arms is not clumsy in particular, he
    is the worst his kind produces, and that is 1.4% of leaders and about 6% of everyone else. Health
    and morale are floored only by the generator's refusal of zero, which leaves them a bottom of
    their own to fall to, so each carries its own epithet - see [_has_fallen_to_the_bottom].

    A man can be in two of the three at once, and the arms are named first - not because they are the
    rarest, which they are not, but because they are the completest failing: two attributes gone at the
    same time rather than one. Rarest-first is not available to any fixed order, because the ranking
    flips between archetypes - the arms are the rarest failing a leader has at 1.5% against health's
    4.4%, and the commonest a mercenary has at 6.7% against health's 1.5%.
    """
    candidates = (
        (strength, NicknameStateChoices.STRENGTH, NicknameStateChoices.STRENGTH_FAR),
        (dexterity, NicknameStateChoices.DEXTERITY, NicknameStateChoices.DEXTERITY_FAR),
        (health, NicknameStateChoices.HEALTH, NicknameStateChoices.HEALTH_FAR),
        (morale, NicknameStateChoices.MORALE, NicknameStateChoices.MORALE_FAR),
    )
    # "max" hands back the first of equal candidates, so declaration order is the tie-break
    furthest, near_state, far_state = max(candidates, key=lambda candidate: candidate[0].reach)

    if furthest.reach >= NICKNAME_FAR_SPREAD_THRESHOLD:
        return far_state

    if furthest.reach >= NICKNAME_SPREAD_THRESHOLD:
        return near_state

    if strength.is_at_floor and dexterity.is_at_floor:
        return NicknameStateChoices.STATS_AT_FLOOR

    if _has_fallen_to_the_bottom(draw=health):
        return NicknameStateChoices.HEALTH_AT_BOTTOM

    if _has_fallen_to_the_bottom(draw=morale):
        return NicknameStateChoices.MORALE_AT_BOTTOM

    return None


def resolve_nickname(*, state: int, variant: int) -> str:
    """
    How this warrior's epithet is phrased for him.

    The variant is reduced modulo the list it lands in, so one stored number picks a wording out of a
    list of two and a list of three alike - see [NICKNAME_VARIANT_BOUND].
    """
    wordings = NICKNAME_WORDINGS[state]

    return wordings[variant % len(wordings)]
