from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.base import BaseItemGenerator


class FyrdItemGenerator(BaseItemGenerator):
    MODIFIER_ROLLS_MU = 0
    MODIFIER_ROLLS_SIGMA = 2
    # Half of nothing is nothing, spelled out rather than left to inheritance: the base class carries a
    # mean of its own, and a levy who inherited it would come off the fields better armoured than armed
    ARMOR_MODIFIER_ROLLS_MU = 0
    ARMOR_MODIFIER_ROLLS_SIGMA = 2

    # A man called off the fields, in what the fields could give him
    item_tiers = frozenset({ItemType.TierChoices.TIER_RUSTIC})
