import random

from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.base import AttackService


class RiskyAttackService(AttackService):
    command: Command = WarriorAttacksWarrior

    def get_attack_value(self) -> int:
        # Attack has 50% chance to miss
        if bool(random.getrandbits(1)):
            # Full weapon damage for a warrior at his own kind's mean strength, otherwise less or greater
            attack = round(self.warrior.roll_attack() * 2 * self.warrior.strength / self.warrior.strength_baseline)
        else:
            attack = 0

        # TODO (#99): can we put this in "AttackService"?
        self.message_list.append(WarriorAttackedWithDamage(skirmish=self.skirmish, warrior=self.warrior, damage=attack))

        return attack
