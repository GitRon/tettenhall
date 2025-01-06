from apps.core.event_loop.messages import Command
from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarriorWithFastAttack,
)
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.base import AttackService


class FastAttackService(AttackService):
    command: Command = WarriorAttacksWarriorWithFastAttack
    context: WarriorAttacksWarriorWithFastAttack.Context

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # Fast attack will double the base points for being the attacker instead of the defender
        return AttackService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 2

    def _get_attack_value(self) -> int:
        # Attack will cause only 50% damage since it's a fast one
        # Attack will be at 100% for strength 10, otherwise less or greater
        attack = int(
            round(
                self.context.attacker.roll_attack() * 0.5 * self.context.attacker.strength / self.BASE_COMPARE_STRENGTH
            )
        )

        self.message_list.append(
            WarriorAttackedWithDamage(
                WarriorAttackedWithDamage.Context(
                    skirmish=self.context.skirmish, warrior=self.context.attacker, damage=attack
                )
            )
        )

        return attack
