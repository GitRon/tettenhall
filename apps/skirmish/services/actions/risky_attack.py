import random

from apps.core.event_loop.messages import Command, Event
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarriorWithRiskyAttack
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.simple_attack import SimpleAttackService


class RiskyAttackService(SimpleAttackService):
    context: WarriorAttacksWarriorWithRiskyAttack.Context

    def __init__(self, *, context: [Command.Context, Event.Context]) -> None:
        super().__init__(context=context)

        self.message_list = []

    def _get_attack_value(self):
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
