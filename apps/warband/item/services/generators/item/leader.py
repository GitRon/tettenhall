from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.base import BaseItemGenerator


class LeaderItemGenerator(BaseItemGenerator):
    MODIFIER_ROLLS_MU = 4
    MODIFIER_ROLLS_SIGMA = 1
    ARMOR_MODIFIER_ROLLS_MU = 2
    ARMOR_MODIFIER_ROLLS_SIGMA = 1

    # A man with a war band behind him marches out in the best the game has
    item_tiers = frozenset({ItemType.TierChoices.TIER_FINE})
