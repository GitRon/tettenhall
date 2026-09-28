import dataclasses

from queuebie.messages import Command

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
)
from apps.warband.skirmish.services.actions.base import SkirmishActionService


class DefensiveStanceService(SkirmishActionService):
    command: Command = WarriorAttacksWarrior

    DEFENSE_MULTIPLIER = 2

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # Being in defensive stance will never lead to being the attacker
        return SkirmishActionService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 0

    def get_attack_value(self) -> ActionRoll:
        # Being in defensive stance will never lead to being the attacker, so no weapon is swung and
        # no die is thrown
        return ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)

    def get_defense_value(self) -> ActionRoll:
        # Defense value is multiplied, and the die it was multiplied from is kept as it fell
        defense = super().get_defense_value()

        return dataclasses.replace(defense, value=defense.value * self.DEFENSE_MULTIPLIER)
