import random

from apps.core.domain.random import DiceNotation
from apps.skirmish.models.battle_log import BattleLog
from apps.skirmish.models.warrior import Warrior


class DuelService:
    """
    Determines one single hit in the fight between "warrior_1" and "warrior_2"
    """

    warrior_1: Warrior
    warrior_2: Warrior

    def __init__(self, warrior_1: Warrior, warrior_2: Warrior):
        self.warrior_1 = warrior_1
        self.warrior_2 = warrior_2

    def _determine_roles_by_dexterity(self):
        random_value = random.random()

        if (
            self.warrior_1.dexterity
            / (self.warrior_1.dexterity + self.warrior_2.dexterity)
            > random_value
        ):
            attacker: Warrior = self.warrior_1
            defender: Warrior = self.warrior_2
        else:
            attacker: Warrior = self.warrior_2
            defender: Warrior = self.warrior_1

        BattleLog.objects.create(
            message=f"Warrior {attacker} is the attacker and warrior {defender} the defender."
        )

        return attacker, defender

    def _calculate_damage(self, attacker, defender):
        attack = DiceNotation(dice_string=attacker.weapon.value).result
        defense = DiceNotation(dice_string=defender.armor.value).result

        damage = max(attack - defense, 0)

        BattleLog.objects.create(
            message=f"{attacker} hits for {attack} damage and {defender} defends for {defense} resulting in {damage} "
            f"damage."
        )

        return damage

    def process(self):
        attacker, defender = self._determine_roles_by_dexterity()

        damage = self._calculate_damage(attacker, defender)

        defender = Warrior.objects.handle_damage_taken(obj=defender, changed_by=damage)

        if defender.condition != Warrior.ConditionChoices.CONDITION_HEALTHY:
            BattleLog.objects.create(
                message=f"{defender} is out of the game being {defender.get_condition_display()}."
            )

    # def determine_loser(self, warrior_1: Warrior, warrior_2: Warrior) -> Warrior:
    #     while 1:
    #         random_value = random.random()
    #
    #         if (
    #             warrior_1.dexterity / (warrior_1.dexterity + warrior_2.dexterity)
    #             > random_value
    #         ):
    #             attacker: Warrior = warrior_1
    #             defender: Warrior = warrior_2
    #         else:
    #             attacker: Warrior = warrior_2
    #             defender: Warrior = warrior_1
    #
    #         attack = DiceNotation(dice_string=attacker.weapon.value).result
    #         defense = DiceNotation(dice_string=defender.armor.value).result
    #
    #         damage = max(attack - defense, 0)
    #         defender.current_health -= damage
    #
    #         print(
    #             f" {attacker} hits for {attack} damage and {defender} defends for {defense} resulting in {damage} "
    #             f"damage."
    #         )
    #
    #         if defender.current_health <= 0:
    #             break
    #
    #     print(f"Warrior {defender} lost against warrior {attacker}.")
    #     return defender
