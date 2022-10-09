import logging
import random
from dataclasses import dataclass
from typing import Literal, List

from faker import Faker

from apps.skirmish.domain.helpers import DiceNotation

logger = logging.getLogger(__name__)


@dataclass
class Faction:
    name: str


@dataclass
class Weapon:
    name: str
    damage = DiceNotation


@dataclass
class Armor:
    name: str
    defense = DiceNotation


@dataclass
class Warrior:
    name: str
    attack: DiceNotation
    defense: DiceNotation
    max_health: int
    current_health: int

    @classmethod
    def generate_random(cls):
        health = random.randint(10, 20)
        return cls(
            name=cls.generate_name(),
            attack=DiceNotation(rolls=2, sides=random.randint(1, 3)),
            defense=DiceNotation(rolls=1, sides=random.randint(1, 3)),
            max_health=health,
            current_health=health,
        )

    def __str__(self):
        return self.name

    @staticmethod
    def generate_name():
        faker = Faker()
        return faker.first_name_male()

    def defends_attack(self, attack: DiceNotation) -> int:
        defense_roll = self.defense.result
        attack_roll = attack.result

        damage = max(0, attack_roll - defense_roll)
        self.current_health -= damage

        # logger.info(f'{str(self)} taken {damage} and has {self.health} remaining.')
        print(f'{str(self)} takes {damage} damage and has {self.current_health}/{self.max_health} health.')

        return damage
