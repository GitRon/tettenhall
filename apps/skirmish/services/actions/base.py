import dataclasses

from apps.core.event_loop.messages import Command, Event
from apps.skirmish.messages.events.warrior import (
    WarriorAttackedWithDamage,
    WarriorDefendedAllDamage,
    WarriorDefendedDamage,
    WarriorTookDamage,
)


class AttackService:
    message_list: list[Event]

    command: Command
    context: dataclasses.dataclass

    BASE_COMPARE_STRENGTH = 10

    def __init__(self, *, context: [Command.Context, Event.Context]) -> None:
        super().__init__()

        self.message_list = []
        self.context = context

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        """
        Determine the points the given warrior has based on this base dexterity and his attack action.
        This value will be used to match warrior attacker/defender pairs in a skirmish.
        """
        return warrior_dexterity

    def _get_attack_value(self) -> int:
        # Attack will be at 100% for strength 10, otherwise less or greater
        attack = int(
            round(self.context.attacker.roll_attack() * self.context.attacker.strength / self.BASE_COMPARE_STRENGTH)
        )
        self.message_list.append(
            WarriorAttackedWithDamage(
                WarriorAttackedWithDamage.Context(
                    skirmish=self.context.skirmish, warrior=self.context.attacker, damage=attack
                )
            )
        )

        return attack

    def _get_defense_value(self) -> int:
        defense = self.context.defender.roll_defense()
        self.message_list.append(
            WarriorDefendedDamage(
                WarriorDefendedDamage.Context(
                    skirmish=self.context.skirmish, warrior=self.context.defender, damage=defense
                )
            )
        )

        return defense

    def _deal_damage(self, *, attack: int, defense: int) -> int:
        damage = max(attack - defense, 0)

        if damage > 0:
            self.message_list.append(
                WarriorTookDamage(
                    WarriorTookDamage.Context(
                        skirmish=self.context.skirmish,
                        attacker=self.context.attacker,
                        attacker_damage=attack,
                        defender=self.context.defender,
                        defender_damage=defense,
                        damage=damage,
                    )
                )
            )
        else:
            self.message_list.append(
                WarriorDefendedAllDamage(
                    WarriorDefendedAllDamage.Context(
                        skirmish=self.context.skirmish,
                        attacker=self.context.attacker,
                        defender=self.context.defender,
                        attacker_damage=attack,
                        defender_damage=defense,
                    )
                )
            )

        return damage

    def process(self) -> list[Event]:
        attack = self._get_attack_value()
        defense = self._get_defense_value()
        self._deal_damage(attack=attack, defense=defense)

        return self.message_list
