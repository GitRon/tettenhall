import random

from apps.core.event_loop.messages import Command, Event
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarriorWithRiskyAttack
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.fight_actions.simple_attack import SimpleAttackService


class RiskyAttackService(SimpleAttackService):
    context: WarriorAttacksWarriorWithRiskyAttack.Context

    def __init__(self, context: [Command.Context, Event.Context]) -> None:
        super().__init__(context)

        self.message_list = []

    def _get_attack_value(self):
        if bool(random.getrandbits(1)):
            attack = self.context.attacker.roll_attack() * 2
        else:
            attack = 0

        self.message_list.append(
            WarriorAttackedWithDamage.generator(
                {"skirmish": self.context.skirmish, "warrior": self.context.attacker, "damage": attack}
            )
        )

        return attack
