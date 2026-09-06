from dataclasses import dataclass

from apps.common.domain.dice import DiceRoll


@dataclass(frozen=True, kw_only=True)
class ActionRoll:
    """
    What one warrior's chosen action produced, before the other man's is set against it.

    Three things rather than the single number the fight compares, because that number is a blend and
    cannot be read back as any of its parts: the die is scaled by the warrior's strength against his
    kind's mean, and then again by whatever his action does to it.
    """

    # The weapon's or armour's own die as it fell, with the notation that produced it. None when
    # nothing was thrown at all: a stance that never attacks and a swing that went wide roll no die,
    # and a zero in its place would claim one was rolled and came up empty
    roll: DiceRoll | None
    # What the fight actually compares, strength and the action's own multiplier included
    value: int
    # Why no blow was thrown, for the two actions that can decline to throw one. Left None whenever
    # one was: whether it got through is the damage service's answer, not the action's
    outcome: int | None = None
