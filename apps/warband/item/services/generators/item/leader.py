from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.base import BaseItemGenerator


class LeaderItemGenerator(BaseItemGenerator):
    # A mercenary's means at half his spread: a leader is reliably well armed, never badly, but he does
    # not march out at the top of the table. Every faction is founded with one, so the first leader
    # killed would otherwise hand over the best kit of the campaign in month two - and the forge would
    # have nothing left to sell for the rest of it.
    MODIFIER_ROLLS_MU = 2
    MODIFIER_ROLLS_SIGMA = 1
    ARMOR_MODIFIER_ROLLS_MU = 1
    ARMOR_MODIFIER_ROLLS_SIGMA = 1

    # A man with a war band behind him has been up and down the ladder, like a mercenary
    item_tiers = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
