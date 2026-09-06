import dataclasses

from queuebie.messages import Command

from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
)
from apps.skirmish.services.actions.base import AttackService


class DefensiveStanceService(AttackService):
    command: Command = WarriorAttacksWarrior

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # Being in defensive stance will never lead to being the attacker
        return AttackService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 0

    def get_attack_value(self) -> ActionRoll:
        # Being in defensive stance will never lead to being the attacker, so no weapon is swung and
        # no die is thrown
        return ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)

    def get_defense_value(self) -> ActionRoll:
        # Defense value is doubled, and the die it was doubled from is kept as it fell
        defense = super().get_defense_value()

        return dataclasses.replace(defense, value=defense.value * 2)
