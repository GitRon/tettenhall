from apps.core.event_loop.messages import Event
from apps.skirmish.messages.commands.skirmish import WarriorAttacksWarrior
from apps.skirmish.messages.events.warrior import (
    WarriorAttackedWithDamage,
    WarriorDefendedDamage,
)
from apps.skirmish.models import Skirmish, Warrior


# TODO: attack service is misleading, maybe skirmish action again?
class AttackService:
    message_list: list[Event]

    command: WarriorAttacksWarrior

    skirmish: Skirmish
    warrior: Warrior

    BASE_COMPARE_STRENGTH = 10

    def __init__(self, *, skirmish: Skirmish, warrior: Warrior) -> None:
        super().__init__()

        self.message_list = []

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
        # Attack will be at 100% for strength 10, otherwise less or greater
        attack = int(round(self.warrior.roll_attack() * self.warrior.strength / self.BASE_COMPARE_STRENGTH))
        self.message_list.append(
            WarriorAttackedWithDamage(
                WarriorAttackedWithDamage.Context(
                    skirmish=self.skirmish,
                    warrior=self.warrior,
                    damage=attack,
                )
            )
        )

        return attack

    def get_defense_value(self) -> int:
        defense = self.warrior.roll_defense()
        self.message_list.append(
            WarriorDefendedDamage(
                WarriorDefendedDamage.Context(
                    skirmish=self.skirmish,
                    warrior=self.warrior,
                    damage=defense,
                )
            )
        )

        return defense
