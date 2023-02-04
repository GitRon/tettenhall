import random

from faker import Faker

from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction
from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.base import BaseItemGenerator
from apps.skirmish.models.warrior import Warrior


class BaseWarriorGenerator:
    XP_MU: int
    XP_SIGMA: int
    HEALTH_MU: int
    HEALTH_SIGMA: int
    MORALE_MU: int
    MORALE_SIGMA: int
    STATS_MU: int
    STATS_SIGMA: int

    item_generator_class: type(BaseItemGenerator)
    chance_for_weapon = 1
    chance_for_armor = 1

    culture: Culture
    faction: Faction

    def __init__(self, culture: Culture, faction: Faction | None) -> None:
        self.culture = culture
        self.faction = faction

    def process(self):
        faker = Faker([self.culture.locale])

        experience = 0
        while experience == 0:
            experience = max(random.gauss(self.XP_MU, self.XP_SIGMA), 0)

        max_health = 0
        while max_health == 0:
            max_health = max(random.gauss(self.HEALTH_MU, self.HEALTH_SIGMA), 0)

        max_morale = 0
        while max_morale == 0:
            max_morale = max(random.gauss(self.MORALE_MU, self.MORALE_SIGMA), 0)

        strength = 0
        while strength == 0:
            strength = max(random.gauss(self.STATS_MU, self.STATS_SIGMA), 0)

        dexterity = 0
        while dexterity == 0:
            dexterity = max(random.gauss(self.STATS_MU, self.STATS_SIGMA), 0)

        base_recruitment_price = 0
        while base_recruitment_price == 0:
            base_recruitment_price = max(random.gauss(100, 50), 0)
        recruitment_price = int(
            (((strength + dexterity) / self.STATS_MU) + (max_health / self.HEALTH_MU)) * base_recruitment_price
        )

        if random.uniform(0, 1) <= self.chance_for_weapon:
            weapon_generator = self.item_generator_class(
                faction=self.faction, item_function=ItemType.FunctionChoices.FUNCTION_WEAPON
            )
            weapon = weapon_generator.process()
        else:
            weapon = None

        if random.uniform(0, 1) <= self.chance_for_armor:
            armor_generator = self.item_generator_class(
                faction=self.faction, item_function=ItemType.FunctionChoices.FUNCTION_ARMOR
            )
            armor = armor_generator.process()
        else:
            armor = None

        warrior = Warrior.objects.create(
            name=faker.first_name_male(),
            culture=self.culture,
            faction=self.faction,
            experience=experience,
            current_health=max_health,
            max_health=max_health,
            current_morale=max_morale,
            max_morale=max_morale,
            strength=strength,
            dexterity=dexterity,
            recruitment_price=recruitment_price,
            weekly_salary=int(recruitment_price * 0.15),
            weapon=weapon,
            armor=armor,
        )

        return warrior
