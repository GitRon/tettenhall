from collections.abc import Iterable

from apps.warband.faction.domain.rival_policy import ShopOffer
from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.item.services.handout import SLOT_NAMES, get_handout_roster


def get_shop_offers(*, item_list: Iterable[Item]) -> list[ShopOffer]:
    """
    The shelf as [RivalPolicy] weighs it: each item's price, the slot it fills and what it is worth there.

    Handed the items rather than the faction, because the caller keeps them by id to turn the policy's
    decision back into the item it names. The items want their "type" loaded - the value is read off it.
    """
    return [
        ShopOffer(item_id=item.id, price=item.price, slot=item.gear_slot, value=item.expectancy_value)
        for item in item_list
    ]


def get_held_gear_values(*, faction: Faction) -> dict[str, list[float]]:
    """
    What each man the hand-out may arm carries in each slot, one figure per man - what a purchase is weighed
    against. An empty slot counts as the fallback's dice, as in "annotate_held_gear_values".
    """
    handout_roster = get_handout_roster(faction=faction)

    return {slot: [warrior.held_gear_values[slot] for warrior in handout_roster] for slot in SLOT_NAMES}
