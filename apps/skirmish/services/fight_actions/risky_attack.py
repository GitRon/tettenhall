import random

from apps.core.domain.random import DiceNotation
from apps.core.event_loop.messages import Command, Event
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarriorWithRiskyAttack
from apps.skirmish.services.fight_actions.simple_attack import SimpleAttackService


class RiskyAttackService(SimpleAttackService):
    context: WarriorAttacksWarriorWithRiskyAttack.Context

    def __init__(self, context: [Command.Context, Event.Context]) -> None:
        super().__init__(context)

        self.message_list = []

    def _get_attack_value(self):
        if bool(random.getrandbits(1)):
            attack = DiceNotation(dice_string=self.context.attacker.weapon.value).result * 2
        else:
            attack = 0

        return attack
