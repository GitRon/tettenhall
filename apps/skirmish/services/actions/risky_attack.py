import random

from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.services.actions.base import AttackService


class RiskyAttackService(AttackService):
    command: Command = WarriorAttacksWarrior

    def get_attack_value(self) -> int:
        # Attack has 50% chance to miss
        if bool(random.getrandbits(1)):
            # Full weapon damage for a warrior at his own kind's mean strength, otherwise less or greater
            return round(self.warrior.roll_attack() * 2 * self.warrior.strength / self.warrior.strength_baseline)

        return 0
