import random

from queuebie.messages import Command

from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.services.actions.base import AttackService


class RiskyAttackService(AttackService):
    command: Command = WarriorAttacksWarrior

    def get_attack_value(self) -> ActionRoll:
        # Attack has 50% chance to miss
        if bool(random.getrandbits(1)):
            return self._scaled_by_strength(attack=self.warrior.roll_attack(), action_multiplier=2)

        # No die and no weapon at all, and it says so: a swing that went wide is not a blow the armour
        # stopped, and a zero on its own cannot tell the two apart
        return ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_MISSED)
