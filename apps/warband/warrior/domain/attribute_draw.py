from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class AttributeDraw:
    """
    One of a warrior's attributes beside the distribution it was drawn from.

    The four travel together because none of them means anything alone: a strength of nine is a
    monster among the fyrd and unremarkable among mercenaries, and which it is can only be read off
    the mean and the spread of the men it was drawn with. The generators stamp them on the warrior for
    exactly this reason - see "Warrior.strength_baseline".
    """

    value: int
    baseline: int
    spread: int
    # The lowest this attribute can come out of its generator. One by default, which is what health
    # and morale are worth: they are re-rolled while zero, so nothing below one survives generation.
    # Strength and dexterity are re-rolled below their own "STATS_MIN" and pass it.
    minimum: int = 1

    @property
    def reach(self) -> float:
        """
        How far past his own kind's mean this attribute came out, counted in spreads.

        Negative for a man below it. Comparable across attributes and across archetypes, which is what
        lets one rule ask which of four attributes a warrior should be named for.
        """
        return (self.value - self.baseline) / self.spread
