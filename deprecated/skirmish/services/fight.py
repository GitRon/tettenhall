import random

from apps.skirmish.domain.model.item import Item
from apps.skirmish.domain.model.warrior import Warrior


class FightService:
    party_1: list[Warrior]
    party_2: list[Warrior]

    casualty_list: list[Warrior] = []
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
        random.shuffle(self.party_1)
        random.shuffle(self.party_2)

    def determine_loser(self, warrior_1: Warrior, warrior_2: Warrior) -> Warrior:
        while 1:
            random_value = random.random()

            if warrior_1.dexterity / (warrior_1.dexterity + warrior_2.dexterity) > random_value:
                attacker: Warrior = warrior_1
                defender: Warrior = warrior_2
            else:
                attacker: Warrior = warrior_2
                defender: Warrior = warrior_1

            attack = attacker.weapon.value.result
            defense = defender.armor.value.result

            damage = max(attack - defense, 0)
            defender.current_health -= damage

            print(
                f" {attacker} hits for {attack} damage and {defender} defends for {defense} resulting in {damage} "
                f"damage."
            )

            if defender.current_health <= 0:
                break

        print(f"Warrior {defender} lost against warrior {attacker}.")
        return defender

    def handle_casualty(self, warrior: Warrior):
        if warrior.current_health < warrior.max_health * -0.15:
            print(f"Warrior {warrior} died.\n")
        else:
            print(f"Warrior {warrior} is unconscious.\n")

        self.casualty_list.append(warrior)

        if bool(random.getrandbits(1)):
            self.spoils_of_war.append(warrior.weapon)
        if bool(random.getrandbits(1)):
            self.spoils_of_war.append(warrior.armor)

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

            loser = self.determine_loser(warrior_party_1, warrior_party_2)
            self.handle_casualty(loser)

        print("Skirmish over. Casualties:")
        for casualty in self.casualty_list:
            print(f"* {casualty}")

        print("\nSpoils of war:")
        for item in self.spoils_of_war:
            print(f"* {item}")
