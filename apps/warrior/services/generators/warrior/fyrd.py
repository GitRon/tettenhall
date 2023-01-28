from apps.item.services.generators.item.fyrd import FyrdItemGenerator
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


class FyrdWarriorGenerator(BaseWarriorGenerator):
    XP_MU = 30
    XP_SIGMA = 10
    HEALTH_MU = 10
    HEALTH_SIGMA = 10
    MORALE_MU = 5
    MORALE_SIGMA = 3
    STATS_MU = 5
    STATS_SIGMA = 5

    item_generator_class = FyrdItemGenerator
