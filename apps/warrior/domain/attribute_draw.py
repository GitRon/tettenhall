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
    # The lowest this attribute can come out of its generator. One by default, which is what the
    # guarded attributes are worth: health and morale are re-rolled while zero rather than floored, so
    # nothing below one survives generation. Strength and dexterity are floored properly and pass
    # their own "STATS_MIN".
    minimum: int = 1

    @property
    def reach(self) -> float:
        """
        How far past his own kind's mean this attribute came out, counted in spreads.

        Negative for a man below it. Comparable across attributes and across archetypes, which is what
        lets one rule ask which of four attributes a warrior should be named for.
        """
        return (self.value - self.baseline) / self.spread

    @property
    def is_at_floor(self) -> bool:
        """
        Whether this came out as low as the generator can put it.

        At or below rather than on it: training only ever raises an attribute, so nothing generated
        sits underneath its own minimum, but nothing reading this should depend on that staying true.
        """
        return self.value <= self.minimum
