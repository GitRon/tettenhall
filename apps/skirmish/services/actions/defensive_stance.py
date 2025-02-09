from queuebie.messages import Command

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

    def get_attack_value(self) -> int:
        # Being in defensive stance will never lead to being the attacker
        return 0

    def get_defense_value(self) -> int:
        # Defense value is doubled
        return super().get_defense_value() * 2
