import dataclasses

from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.models import Skirmish, Warrior


# TODO (#95): attack service is misleading, maybe skirmish action again?
class AttackService:
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
        """
        return dataclasses.replace(
            attack,
            value=round(
                attack.roll.result * action_multiplier * self.warrior.strength / self.warrior.strength_baseline
            ),
        )

    def get_attack_value(self) -> ActionRoll:
        return self._scaled_by_strength(attack=self.warrior.roll_attack())

    def get_defense_value(self) -> ActionRoll:
        # Defence is the armour's own roll and nothing else - no strength, and so no baseline either
        return self.warrior.roll_defense()
