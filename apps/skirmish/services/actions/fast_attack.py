from queuebie.messages import Command

from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
)
from apps.skirmish.services.actions.base import AttackService


class FastAttackService(AttackService):
    command: Command = WarriorAttacksWarrior

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # Fast attack will double the base points for being the attacker instead of the defender
        return AttackService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 2

    def get_attack_value(self) -> ActionRoll:
        # Attack will cause only 50% damage since it's a fast one
        roll = self.warrior.roll_attack()

        return ActionRoll(roll=roll, value=self._scaled_by_strength(roll=roll.result, action_multiplier=0.5))
