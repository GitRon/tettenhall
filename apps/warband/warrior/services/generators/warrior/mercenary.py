from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator


class MercenaryWarriorGenerator(BaseWarriorGenerator):
    # On level 2's threshold with a wide spread, on purpose: the pub has green men and seasoned ones for
    # hire, about half of each, unlike the leader, whose narrow spread says he is always the one (#493)
    XP_MU = 100
    XP_SIGMA = 75
    HEALTH_MU = 40
    HEALTH_SIGMA = 16
    MORALE_MU = 10
    MORALE_SIGMA = 5
    STATS_MU = 10
    STATS_SIGMA = 4
    STATS_MIN = 3
    PROGRESS_MU = 50
    PROGRESS_SIGMA = 50

    item_generator_class = MercenaryItemGenerator
    chance_for_weapon = 0.75
    chance_for_armor = 0.25
