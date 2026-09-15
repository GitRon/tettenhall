import random

from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.models.injury_type import InjuryType


class InjuryRollService:
    """
    Whether a beating left a mark, and which one.

    The chance is scaled by how far past nothing the blow carried the man, which is what turns the
    death threshold from a cliff into a gradient: today a fight resolves as *nothing happened* or *he
    is gone*, and a warrior carried to the edge of it should not walk away as clean as one who was
    tapped over.

    Which injury he takes is drawn flat. The depth scales the chance and nothing else - a second axis
    on one roll would be two balance levers to tune where there is one thing to say.
    """

    # What a man who was tipped only just over carries out of the fight...
    CHANCE_AT_ZERO = 0.10
    # ...and what a man one point short of a corpse does. Between the two it is linear, so roughly one
    # man in three who goes down keeps something.
    CHANCE_AT_DEATHS_DOOR = 0.50

    warrior: Warrior
    overkill_health: int

    def __init__(self, *, warrior: Warrior, overkill_health: int) -> None:
        self.warrior = warrior
        self.overkill_health = overkill_health

    @property
    def _overkill_share(self) -> float:
        """
        How near death the blow took him, as nothing at the lip and one at the threshold.

        Measured against the very same depth that decided unconscious from dead, so the two can never
        disagree about where the band ends. It cannot exceed one: a blow that went further raised
        "WarriorWasKilled" instead and never reaches this.
        """
        return self.overkill_health / (self.warrior.max_health * Warrior.DEATH_OVERKILL_SHARE)

    @property
    def chance(self) -> float:
        return self.CHANCE_AT_ZERO + (self.CHANCE_AT_DEATHS_DOOR - self.CHANCE_AT_ZERO) * self._overkill_share

    def process(self) -> InjuryType | None:
        """
        The injury this beating left, or nothing.
        """
        if random.random() >= self.chance:
            return None

        injury_type = InjuryType.objects.order_by("?").first()

        if injury_type is None:
            raise RuntimeError(
                "No injury types exist. Load the reference data with 'loaddata culture itemtype questname injurytype'."
            )

        return injury_type
