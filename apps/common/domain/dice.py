import itertools
import random
import re
from dataclasses import dataclass


@dataclass(kw_only=True)
class DiceNotation:
    """
    Dice notation format: "2d4+7"
    Rolls 2 times a die with 4 sides and add 7.
    "2d4" is part of the item type, the modifier comes from the item itself.
    """

    rolls: int
    sides: int
    modifier: int

    def __init__(self, *, dice_string: str, modifier: int = 0):
        match = re.search(r"^(\d+)d(\d+)$", dice_string)
        self.rolls = int(match[1])
        self.sides = int(match[2])
        self.modifier = modifier

    def __str__(self) -> str:
        return f"{self.rolls}d{self.sides}"

    @property
    def result(self) -> int:
        result = 0
        for _ in itertools.repeat(None, self.rolls):
            result += random.randint(1, self.sides)
        return max(result + self.modifier, 0)

    @property
    def expectancy_value(self) -> float:
        return (self.rolls * (self.sides + 1) / 2) + self.modifier

    @property
    def expected_result(self) -> float:
        """
        What "result" hands back on average, floor included.

        The figure a player reads as a weapon's average. "expectancy_value" lets a deep modifier pull it
        below zero - "1d4-3" averages -0.5 there - but no blow ever lands for less than nothing, so the
        three faces that fall short count as 0 and the one that clears counts as 1: 0.25. The two only
        differ when the floor can be reached; prices and the gear hand-out rank by "expectancy_value".

        Counted exactly over every total the dice can show rather than estimated, which costs one pass
        per die over at most "best_possible_roll" totals.
        """
        ways_to_reach = {0: 1}
        for _ in range(self.rolls):
            next_ways = {}
            for total, ways in ways_to_reach.items():
                for face in range(1, self.sides + 1):
                    next_ways[total + face] = next_ways.get(total + face, 0) + ways
            ways_to_reach = next_ways

        outcomes = self.sides**self.rolls
        return sum(max(total + self.modifier, 0) * ways for total, ways in ways_to_reach.items()) / outcomes

    @property
    def best_possible_roll(self) -> int:
        """
        Every die showing its highest face, before the modifier.

        What an item generator floors a negative modifier against: a modifier deeper than this makes
        the item unable to deal damage at all, however it is rolled.
        """
        return self.rolls * self.sides

    @property
    def best_possible_result(self) -> int:
        """
        The highest number "result" can hand back, modifier included.

        Floored at zero the way "result" is, so a notation whose modifier is deeper than its dice has
        a ceiling of nothing rather than a negative one. This is what a recorded roll is measured
        against - the roll carries the modifier, so the bare "best_possible_roll" would call an
        ordinary throw with a good weapon a maximum one.
        """
        return max(self.best_possible_roll + self.modifier, 0)

    def roll(self) -> DiceRoll:
        """
        One throw, kept next to the notation that made it.

        "result" rolls afresh on every read, so anything wanting both the number and what the number
        could have been has to take the two together: asking twice answers about two different throws.
        """
        return DiceRoll(notation=self, result=self.result)


@dataclass(frozen=True, kw_only=True)
class DiceRoll:
    """
    A throw that still knows what it was thrown against.

    The pair is the point. A bare 8 cannot be checked against the "2d6+1" it came from, so a record
    holding only totals can never answer whether a man rolled his weapon's maximum - and that
    question is why the roll is written down at all.
    """

    notation: DiceNotation
    result: int
