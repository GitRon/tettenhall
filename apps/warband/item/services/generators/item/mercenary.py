from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.base import BaseItemGenerator


class MercenaryItemGenerator(BaseItemGenerator):
    MODIFIER_ROLLS_MU = 2
    MODIFIER_ROLLS_SIGMA = 2
    ARMOR_MODIFIER_ROLLS_MU = 1
    ARMOR_MODIFIER_ROLLS_SIGMA = 2

    # A man for hire has been up and down the ladder, so both bands are open to him. Spelled out rather
    # than left unset: a pool that happens to be the whole table is a decision about mercenaries, and the
    # town shop borrows this class for its wares - see "handle_restock_shop_items".
    item_tiers = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
