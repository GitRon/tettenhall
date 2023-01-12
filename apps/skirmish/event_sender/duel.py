import random

from apps.core.domain.events import EventSender
from apps.skirmish.event_broadcaster.actions.simple_attack import SimpleAttackService
from apps.skirmish.event_consumers.battle_history import BattleHistoryService
from apps.skirmish.events.duel import DuelAttackerDefenderDecided
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class DuelService(EventSender):
    skirmish: Skirmish
    warrior_1: Warrior
    warrior_2: Warrior
    action_1: int
    action_2: int

    def __init__(self, skirmish, warrior_1, warrior_2, action_1, action_2, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.skirmish = skirmish
        self.warrior_1 = warrior_1
        self.warrior_2 = warrior_2
        self.action_1 = int(action_1)
        self.action_2 = int(action_2)

    def determine_roles_by_dexterity(self, warrior_1: Warrior, warrior_2: Warrior):
        # todo move to simpleattackservice -> henne/ei problem, ich muss wissen, wer anfängt um zu sagen,
        #  welche action es wird. Vll doch global, dass der geschicktere wahrscheinlicher anfängt?
        random_value = random.random()

        if warrior_1.dexterity / (warrior_1.dexterity + warrior_2.dexterity) > random_value:
            attacker: Warrior = warrior_1
            defender: Warrior = warrior_2
        else:
            attacker: Warrior = warrior_2
            defender: Warrior = warrior_1

        self.event_list.append(DuelAttackerDefenderDecided(context_data={"attacker": attacker, "defender": defender}))

        return attacker, defender

    def process(self):
        attacker, defender = self.determine_roles_by_dexterity(
            self.warrior_1,
            self.warrior_2,
        )

        if attacker == self.warrior_1:
            action = self.action_1
        else:
            action = self.action_2

        # todo change to model object
        if action == 1:
            service = SimpleAttackService(attacker, defender)
        else:
            raise RuntimeError("No valid action selected.")

        self.event_list += service.process()

        # Create battle history records
        # todo https://www.cosmicpython.com/book/chapter_10_commands.html
        #  http://www.cosmicpython.com/book/chapter_10_commands.html#events_vs_commands_table
        #  handle_command() und handle_event()
        # todo mache ich das in einem with transaction.atomic() block?
        # event und command list -> dynamische imports aus jeder django app?
        battle_history_service = BattleHistoryService(skirmish=self.skirmish)
        battle_history_service.process(event_list=self.event_list)

        """
        - command muss ein direkter aufruf sein
        - beim command muss sichergestellt sein, dass es ankommt, das system wartet auf den rückgabewert
        - event handler rufen nur commads auf, die haben keine eigene logik
        
        - ProduktInWarenkorbGelegt -> Handler ruft Methode "versandkostenaktualisieren" auf, das berechnet und 
        speichert die neuen VK und löst das Event "VersandkostenAktualisiert" aus. Die Command-Logik löst am Ende 
        alle relevanten Events aus, dem ersten Event-Handler ist das latte, das will nur sicherstellen, DASS das 
        Command ausgeführt wurde
        """
