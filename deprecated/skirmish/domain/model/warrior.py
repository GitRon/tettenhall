import random
from dataclasses import dataclass

from faker import Faker

from apps.skirmish.domain.model.faction import Faction
from apps.skirmish.domain.model.item import Item


@dataclass
class Warrior:
    name: str
    faction: Faction

    max_health: int
    current_health: int
    dexterity: int

    weapon: Item
    armor: Item

    def __init__(self, faction: Faction) -> None:
        self.faction = faction
        self.name = self.generate_name()

        health = random.randint(10, 20)
        self.max_health = health
        self.current_health = health
        self.dexterity = int(round(abs(random.gauss(mu=20, sigma=20)), 0))

        self.weapon = Item(item_type=Item.TYPE_WEAPON)
        self.armor = Item(item_type=Item.TYPE_ARMOR)

    def __str__(self):
        return f"{self.name} ({self.faction})"

    def generate_name(self):
        faker = Faker(locale=self.faction.locale)
        return faker.first_name_male()
