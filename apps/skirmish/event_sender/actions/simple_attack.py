from apps.core.domain.events import EventSender
from apps.core.domain.random import DiceNotation
from apps.skirmish.events.warrior import WarriorAttacksWithDamage, WarriorDefendsDamage, WarriorTakesDamage
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class SimpleAttackService(EventSender):
    """
    Handles attacker attacking defender with action 1. # fixme needs to be dynamic at some point
    Determines one single hit in the fight between "warrior_1" and "warrior_2"
    """

    skirmish: Skirmish
    attacker: Warrior
    defender: Warrior

    def __init__(self, attacker: Warrior, defender: Warrior, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.attacker = attacker
        self.defender = defender

    def _handle_damage(self):
        attack = DiceNotation(dice_string=self.attacker.weapon.value).result
        self.event_list.append(WarriorAttacksWithDamage.generator({"warrior": self.attacker, "damage": attack}))

        defense = DiceNotation(dice_string=self.defender.armor.value).result
        self.event_list.append(WarriorDefendsDamage.generator({"warrior": self.defender, "damage": defense}))

        damage = max(attack - defense, 0)

        self.event_list.append(
            WarriorTakesDamage.generator(
                {
                    "attacker": self.attacker,
                    "attacker_damage": attack,
                    "defender": self.defender,
                    "defender_damage": defense,
                    "damage": damage,
                }
            )
        )

    def process(self) -> list:
        self._handle_damage()

        return self.event_list
