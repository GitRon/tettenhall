import random

from apps.core.domain.random import DiceNotation
from apps.skirmish.models.battle_log import BattleLog
from apps.skirmish.models.item import Item
from apps.skirmish.models.warrior import Warrior


class DuelService:
    """
    Determines one single hit in the fight between "warrior_1" and "warrior_2"
    """

    attacker: Warrior
    defender: Warrior

    def __init__(self, warrior_1: Warrior, warrior_2: Warrior):
        self.attacker, self.defender = self._determine_roles_by_dexterity(
            warrior_1, warrior_2
        )

    def _determine_roles_by_dexterity(self, warrior_1, warrior_2):
        random_value = random.random()

        if (
            warrior_1.dexterity / (warrior_1.dexterity + warrior_2.dexterity)
            > random_value
        ):
            attacker: Warrior = warrior_1
            defender: Warrior = warrior_2
        else:
            attacker: Warrior = warrior_2
            defender: Warrior = warrior_1

        BattleLog.objects.create(
            message=f"Warrior {attacker} is the attacker and warrior {defender} the defender."
        )

        return attacker, defender

    def _handle_damage(self):
        attack = DiceNotation(dice_string=self.attacker.weapon.value).result
        defense = DiceNotation(dice_string=self.defender.armor.value).result

        damage = max(attack - defense, 0)

        BattleLog.objects.create(
            message=f"{self.attacker} hits for {attack} damage and {self.defender} defends for {defense} resulting in "
                    f"{damage} damage."
        )

        defender = Warrior.objects.reduce_current_health(
            obj=self.defender, damage=damage
        )

        return defender, damage

    def _handle_condition(self, warrior):
        # Update condition
        condition = Warrior.ConditionChoices.CONDITION_HEALTHY
        if warrior.current_health < 0:
            if warrior.current_health < warrior.max_health * -0.15:
                condition = Warrior.ConditionChoices.CONDITION_DEAD
            else:
                condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS

            warrior = Warrior.objects.set_condition(obj=warrior, condition=condition)
            BattleLog.objects.create(
                message=f"{warrior} is out of the game being {warrior.get_condition_display()}."
            )

        return warrior, condition

    def _handle_loot(self, warrior):
        spoils_of_war: list[Item] = []
        if bool(random.getrandbits(1)):
            spoils_of_war.append(warrior.weapon)
        if bool(random.getrandbits(1)):
            spoils_of_war.append(warrior.armor)

        if spoils_of_war:
            BattleLog.objects.create(
                message=f"{warrior} dropped the following items: {', '.join([str(item) for item in spoils_of_war])}."
            )

        return spoils_of_war

    def process(self):
        self.defender, damage = self._handle_damage()
        self.defender, condition = self._handle_condition(self.defender)

        loot_list = []
        if condition != Warrior.ConditionChoices.CONDITION_HEALTHY:
            loot_list = self._handle_loot(self.defender)

        return self.attacker, self.defender, loot_list
