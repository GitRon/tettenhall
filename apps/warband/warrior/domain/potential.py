from apps.warband.warrior.domain.knowledge import WarriorKnowledge

# What the player is told about how far a man can still rise - always a word, never the number, since a
# ceiling is something nobody has earned the right to read off a man. The word follows the levels he has
# left rather than the ceiling itself, so it needs no mean to be judged against: "has become what he will
# be" says the same of a champion and of a levy - see docs/patterns/warrior-knowledge.md.
POTENTIAL_SPENT = "Has become what he will be"
POTENTIAL_LEFT = "Has more in him"
POTENTIAL_A_LITTLE_LEFT = "Has a little more in him"
POTENTIAL_MUCH_LEFT = "Has much more in him"


def describe_potential(*, levels_left: int | None, knowledge: WarriorKnowledge) -> str | None:
    """
    The word for how far a man can still rise, at what the viewer has earned, or None where nothing is
    said: a rival's man, and a man generated before the ceiling existed, who has none.
    """
    if levels_left is None or not knowledge.potential_is_visible:
        return None

    if levels_left == 0:
        return POTENTIAL_SPENT

    if not knowledge.potential_is_sharp:
        return POTENTIAL_LEFT

    if levels_left == 1:
        return POTENTIAL_A_LITTLE_LEFT

    return POTENTIAL_MUCH_LEFT
