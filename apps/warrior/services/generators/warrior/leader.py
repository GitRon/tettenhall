from apps.item.services.generators.item.leader import LeaderItemGenerator
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


class LeaderWarriorGenerator(BaseWarriorGenerator):
    XP_MU = 100
    XP_SIGMA = 10
    HEALTH_MU = 20
    HEALTH_SIGMA = 5
    MORALE_MU = 10
    MORALE_SIGMA = 3
    STATS_MU = 8
    STATS_SIGMA = 3
    STATS_MIN = 4
    PROGRESS_MU = 50
    PROGRESS_SIGMA = 50

    item_generator_class = LeaderItemGenerator
    chance_for_weapon = 1
    chance_for_armor = 1
