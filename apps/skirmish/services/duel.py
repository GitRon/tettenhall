from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.actions.action_1 import Action1Service
from apps.skirmish.services.helpers.fight import FightHelper


class DuelService:
    skirmish: Skirmish
    warrior_1: Warrior
    warrior_2: Warrior
    action_1: int
    action_2: int

    def __init__(self, skirmish, warrior_1, warrior_2, action_1, action_2) -> None:
        self.skirmish = skirmish
        self.warrior_1 = warrior_1
        self.warrior_2 = warrior_2
        self.action_1 = int(action_1)
        self.action_2 = int(action_2)

    def process(self):
        attacker, defender = FightHelper.determine_roles_by_dexterity(
            self.skirmish, self.warrior_1, self.warrior_2
        )

        if attacker == self.warrior_1:
            action = self.action_1
        else:
            action = self.action_2

        if action == 1:
            service = Action1Service(self.skirmish, attacker, defender)
            service.process()
