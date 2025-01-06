import random

from apps.core.event_loop.messages import Command
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarriorWithRiskyAttack
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.base import AttackService


class RiskyAttackService(AttackService):
    command: Command = WarriorAttacksWarriorWithRiskyAttack
    context: WarriorAttacksWarriorWithRiskyAttack.Context

    def _get_attack_value(self) -> int:
        # Attack has 50% chance to miss
        if bool(random.getrandbits(1)):
            # Attack will be at 100% for strength 10, otherwise less or greater
            attack = int(
                round(
                    self.context.attacker.roll_attack()
                    * 2
                    * self.context.attacker.strength
                    / self.BASE_COMPARE_STRENGTH
                )
            )
        else:
            attack = 0

        self.message_list.append(
            WarriorAttackedWithDamage(
                WarriorAttackedWithDamage.Context(
                    skirmish=self.context.skirmish, warrior=self.context.attacker, damage=attack
                )
            )
        )

        return attack
