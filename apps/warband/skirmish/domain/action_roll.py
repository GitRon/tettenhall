from dataclasses import dataclass

from apps.common.domain.dice import DiceRoll
from apps.warband.item.models.item_type import ItemType


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
    # Which kind of gear threw that die. The type rather than the item, because these rows outlive the
    # sword: an item is deleted when it is destroyed and would take the record of every blow struck
    # with it along. The type is reference data and never goes anywhere, and it is what a question
    # like "has this man ever felled someone with an axe" is actually asking. None whenever the roll
    # is - nothing was swung, so no gear was used
    item_type: ItemType | None = None
    # What the fight actually compares, strength and the action's own multiplier included
    value: int
    # Why no blow was thrown, for the two actions that can decline to throw one. Left None whenever
    # one was: whether it got through is the damage service's answer, not the action's
    outcome: int | None = None
