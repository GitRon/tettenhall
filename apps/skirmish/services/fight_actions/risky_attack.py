import random

from apps.core.domain.random import DiceNotation
from apps.skirmish.messages.commands.duel import WarriorAttacksWarriorWithRiskyAttack
from apps.skirmish.services.fight_actions.simple_attack import SimpleAttackService


class RiskyAttackService(SimpleAttackService):
    message_list = []
    context: WarriorAttacksWarriorWithRiskyAttack.Context

    def _get_attack_value(self):
        if bool(random.getrandbits(1)):
            attack = DiceNotation(dice_string=self.context.attacker.weapon.value).result * 2
        else:
            attack = 0

        return attack
