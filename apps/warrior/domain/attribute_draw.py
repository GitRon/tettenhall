from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class AttributeDraw:
    """
    One of a warrior's attributes beside the distribution it was drawn from.

    The three travel together because none of them means anything alone: a strength of nine is a
    monster among the fyrd and unremarkable among mercenaries, and which it is can only be read off
    the mean and the spread of the men it was drawn with. The generators stamp both on the warrior for
    exactly this reason - see "Warrior.strength_baseline".
    """

    value: int
    baseline: int
    spread: int

    @property
    def reach(self) -> float:
        """
        How far past his own kind's mean this attribute came out, counted in spreads.

        Negative for a man below it. Comparable across attributes and across archetypes, which is what
        lets one rule ask which of four attributes a warrior should be named for.
        """
        return (self.value - self.baseline) / self.spread
