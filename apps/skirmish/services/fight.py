import random

from apps.skirmish.models.item import Item
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.duel import DuelService


class FightService:
    party_1: list[Warrior]
    party_2: list[Warrior]

    spoils_of_war: list[Item] = []

    def __init__(self, party_1: list[Warrior], party_2: list[Warrior]):
        # Party 1 is always the larger one
        if len(party_1) >= len(party_2):
            self.party_1 = party_1
            self.party_2 = party_2
        else:
            self.party_1 = party_2
            self.party_2 = party_1

        # Create random list
        random.shuffle(list(self.party_1))
        random.shuffle(list(self.party_2))

    def process(self):
        print(f"\nSkirmish! {self.party_1[0].faction} vs. {self.party_2[0].faction}.\n")

        for _index, warrior_party_1 in enumerate(self.party_1):
            # We can do this because list one is always larger/equal than two
            try:
                warrior_party_2 = self.party_2[_index]
                print(
                    f"Fight! {warrior_party_1} ({warrior_party_1.current_health} HP, {warrior_party_1.dexterity} dex, "
                    f"{warrior_party_1.weapon.value}/{warrior_party_1.armor.value}) "
                    f"challenges {warrior_party_2} ({warrior_party_2.current_health} HP, "
                    f"{warrior_party_2.dexterity} dex, "
                    f"{warrior_party_2.weapon.value}/{warrior_party_2.armor.value})!"
                )
            except IndexError:
                break

            # Fight
            service = DuelService(warrior_party_1, warrior_party_2)
            attacker, defender, loot_list = service.process()

        print("\nSpoils of war:")
        for item in self.spoils_of_war:
            print(f"* {item}")
