import dataclasses

from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.warband.skirmish.models import Skirmish, Warrior


# TODO (#95): attack service is misleading, maybe skirmish action again?
class AttackService:
    # How much harder a man is to hurt while he stands behind his own faction's wall. A constant of the
    # mechanic rather than of any wall: a town building levers how much wall there is, never this
    FORTIFICATION_DEFENSE_MULTIPLIER = 1.5

    command: WarriorAttacksWarrior

    skirmish: Skirmish
    warrior: Warrior

    def __init__(self, *, skirmish: Skirmish, warrior: Warrior) -> None:
        super().__init__()

        self.warrior = warrior
        self.skirmish = skirmish

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        """
        Determine the points the given warrior has based on this base dexterity and his attack action.
        This value will be used to match warrior attacker/defender pairs in a skirmish.
        """
        return warrior_dexterity

    def _scaled_by_strength(self, *, attack: ActionRoll, action_multiplier: float = 1) -> ActionRoll:
        """
        What the fight compares, put in place of the bare roll and leaving the die and the gear alone.

        Full weapon damage for a warrior at his own kind's mean strength, otherwise less or greater.

        The effective strength rather than the stored column, so a lasting injury is felt in every
        swing the fight has - the three attack services all reach this one method with a multiplier
        rather than a formula of their own, which is what makes it the single seam.
        """
        return dataclasses.replace(
            attack,
            value=round(
                attack.roll.result
                * action_multiplier
                * self.warrior.effective_strength
                / self.warrior.strength_baseline
            ),
        )

    def get_attack_value(self) -> ActionRoll:
        return self._scaled_by_strength(attack=self.warrior.roll_attack())

    def get_defense_value(self) -> ActionRoll:
        # Defence is the armour's own roll - no strength, and so no baseline either - and the wall
        defense = self.warrior.roll_defense()

        # Every defence in the game comes through here, which is what makes the wall stack with a
        # stance without either knowing about the other: the stance doubles what this returns.
        # Scoped to the defending *side* rather than to the defender of the exchange, who is only
        # whoever lost the initiative roll - an attacker is that in half his exchanges and has no wall
        # at his back in any of them.
        if self.skirmish.is_fortified and self.skirmish.is_defended_by(warrior=self.warrior):
            return dataclasses.replace(defense, value=round(defense.value * self.FORTIFICATION_DEFENSE_MULTIPLIER))

        return defense
