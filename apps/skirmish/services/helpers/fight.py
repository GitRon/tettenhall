import random

from apps.skirmish.models.battle_log import BattleLog
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class FightHelper:
    @staticmethod
    def determine_roles_by_dexterity(
        skirmish: Skirmish, warrior_1: Warrior, warrior_2: Warrior
    ):
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

        BattleLog.objects.create_record(
            skirmish=skirmish,
            message=f"Warrior {attacker} is the attacker and warrior {defender} the defender.",
        )

        return attacker, defender
