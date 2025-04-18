from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
)
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.base import AttackService


class FastAttackService(AttackService):
    command: Command = WarriorAttacksWarrior

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # Fast attack will double the base points for being the attacker instead of the defender
        return AttackService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 2

    def get_attack_value(self) -> int:
        # Attack will cause only 50% damage since it's a fast one
        # Attack will be at 100% for strength 10, otherwise less or greater
        attack = round(self.warrior.roll_attack() * 0.5 * self.warrior.strength / self.BASE_COMPARE_STRENGTH)

        self.message_list.append(
            WarriorAttackedWithDamage(
                skirmish=self.skirmish,
                warrior=self.warrior,
                damage=attack,
            )
        )

        return attack
