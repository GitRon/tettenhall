from queuebie.messages import Command

from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
)
from apps.warband.skirmish.services.actions.base import SkirmishActionService


class FastAttackService(SkirmishActionService):
    command: Command = WarriorAttacksWarrior

    # Quick enough to be the attacker more often, too quick to put weight behind the blow
    PAIR_MATCHING_MULTIPLIER = 2
    ATTACK_MULTIPLIER = 0.5
    # What the man he beat to the blow has left for his counter: caught off-balance, he swings back
    # at this share before armour. Applied by "SkirmishDamageService", which is the one place that sees
    # both men of the exchange - see there
    OFF_BALANCE_COUNTER_MULTIPLIER = 0.5

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # A fast attack weighs more towards being the attacker instead of the defender
        return (
            SkirmishActionService.get_pair_matching_points(warrior_dexterity=warrior_dexterity)
            * FastAttackService.PAIR_MATCHING_MULTIPLIER
        )

    def get_attack_value(self) -> ActionRoll:
        # A fast attack lands lighter than a plain one
        return self._scaled_by_strength(attack=self.warrior.roll_attack(), action_multiplier=self.ATTACK_MULTIPLIER)
