from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.models import Skirmish, Warrior


# TODO (#95): attack service is misleading, maybe skirmish action again?
class AttackService:
    command: WarriorAttacksWarrior

    skirmish: Skirmish
    warrior: Warrior

    def __init__(self, *, skirmish: Skirmish, warrior: Warrior) -> None:
        super().__init__()

        self.warrior = warrior
        self.skirmish = skirmish

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        """
        Determine the points the given warrior has based on this base dexterity and his attack action.
        This value will be used to match warrior attacker/defender pairs in a skirmish.
        """
        return warrior_dexterity

    def get_attack_value(self) -> int:
        # Full weapon damage for a warrior at his own kind's mean strength, otherwise less or greater
        return round(self.warrior.roll_attack() * self.warrior.strength / self.warrior.strength_baseline)

    def get_defense_value(self) -> int:
        return self.warrior.roll_defense()
