from apps.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


class MercenaryWarriorGenerator(BaseWarriorGenerator):
    XP_MU = 100
    XP_SIGMA = 75
    HEALTH_MU = 20
    HEALTH_SIGMA = 10
    MORALE_MU = 10
    MORALE_SIGMA = 5
    STATS_MU = 10
    STATS_SIGMA = 10

    item_generator_class = MercenaryItemGenerator
    chance_for_weapon = 0
    chance_for_armor = 0
