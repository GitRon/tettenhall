from enum import Enum


class WarriorKnowledge(Enum):
    """
    What the player may know about one warrior, decided by what that warrior is to him.

    The rule every screen showing a man derives from, rather than deciding again: **a number the
    player has not earned is fuzzed, and a thing he has not seen is absent.** Four screens answered
    that question in three different ways and three defects came out of the seams between them - see
    docs/patterns/warrior-knowledge.md, which is normative for this.

    The two properties below are the whole rule. A screen asks them; it does not ask which relation
    this is, because that is how a fifth screen starts deciding for itself.
    """

    # One of the player's own men. He has fought beside him and pays him every month.
    COMMANDED = "commanded"
    # In the player's hands without being his: a prisoner in his cells, a mercenary standing in his
    # pub. He can see what the man carries - the town square is already charging him for it - but he
    # has not fought beside him.
    HELD = "held"
    # Somebody else's man, and anybody held by somebody else. Everything privileged about him is
    # knowledge the player has not earned.
    RIVAL = "rival"

    @classmethod
    def for_relation(cls, *, is_commanded: bool, is_held: bool) -> WarriorKnowledge:
        """
        The relation, from the two memberships a caller can establish.

        Commanded outranks held, which outranks neither: a man cannot be in the war band and in the
        cells at once, but a caller that asks two separate questions can get two yeses out of a stale
        row, and the more generous answer is the wrong one to take.
        """
        if is_commanded:
            return cls.COMMANDED
        if is_held:
            return cls.HELD
        return cls.RIVAL

    @property
    def numbers_are_exact(self) -> bool:
        """
        Whether strength, dexterity, health and morale are shown as figures or as a bucket.

        Only for the men he commands. A mercenary for hire is a gamble the pub is selling him, and
        exact numbers would price it for him.
        """
        return self is WarriorKnowledge.COMMANDED

    @property
    def gear_is_visible(self) -> bool:
        """
        Whether the weapon and the armor are named.

        Named or absent, with no bucket in between: the fuzz compares a value against the mean of
        what it was drawn with, a warrior's row carries its own means, and an item does not. So gear
        is the one omission in the rule, and this is where that is written down.
        """
        return self is not WarriorKnowledge.RIVAL
