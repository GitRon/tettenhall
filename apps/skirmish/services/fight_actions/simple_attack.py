from apps.core.domain.random import DiceNotation
from apps.core.event_loop.messages import Command, Event
from apps.skirmish.messages.commands.duel import WarriorAttacksWarriorWithSimpleAttack
from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage, WarriorDefendedDamage, WarriorTookDamage


class SimpleAttackService:
    message_list = []
    context: WarriorAttacksWarriorWithSimpleAttack.Context

    def __init__(self, context: [Command.Context, Event.Context]) -> None:
        super().__init__()

        self.context = context

    def _get_attack_value(self):
        attack = DiceNotation(dice_string=self.context.attacker.weapon.value).result
        self.message_list.append(
            WarriorAttackedWithDamage.generator(
                {"skirmish": self.context.skirmish, "warrior": self.context.attacker, "damage": attack}
            )
        )

        return attack

    def _get_defense_value(self):
        defense = DiceNotation(dice_string=self.context.defender.armor.value).result
        self.message_list.append(
            WarriorDefendedDamage.generator(
                {"skirmish": self.context.skirmish, "warrior": self.context.defender, "damage": defense}
            )
        )

        return defense

    def _deal_damage(self, attack: int, defense: int):
        damage = max(attack - defense, 0)

        self.message_list.append(
            WarriorTookDamage.generator(
                {
                    "skirmish": self.context.skirmish,
                    "attacker": self.context.attacker,
                    "attacker_damage": attack,
                    "defender": self.context.defender,
                    "defender_damage": defense,
                    "damage": damage,
                }
            )
        )

        return damage

    def process(self):
        attack = self._get_attack_value()
        defense = self._get_defense_value()
        self._deal_damage(attack=attack, defense=defense)

        return self.message_list
