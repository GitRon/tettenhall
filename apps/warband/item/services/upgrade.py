from dataclasses import dataclass

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.item.services.generators.item.base import BaseItemGenerator
from apps.warband.town.buildings.weaponsmith import Weaponsmith
from apps.warband.warrior.services.equipping import get_unequip_refusal

# What one step up the condition ladder adds to an item's modifier. A fixed step rather than the next
# band's threshold, because the thresholds belong to the generator that drew the item and the item
# does not remember which one that was: a "Traditional" levy spear and a "Traditional" mercenary spear
# can carry different modifiers. Two is the sigma most generators share, so a step is about one band.
UPGRADE_MODIFIER_STEP = 2
# A rework is never free, even where the floor on expected damage swallows the step's whole value
MINIMUM_UPGRADE_COSTS = 1

NOT_YOURS_REFUSAL = "Only the gear of your own war band is reworked at your forge."
UNWORKABLE_REFUSAL = "There is nothing here for a smith to work on."
SUPERIOR_REFUSAL = "Nothing better than this is made in the land."
NO_WEAPONSMITH_REFUSAL = "There is no weaponsmith to rework it. Build one first."
BEYOND_THE_FORGE_REFUSAL = "Your weaponsmith cannot make it any better. A larger forge could."
ALREADY_UPGRADED_THIS_MONTH_REFUSAL = "Your weaponsmith has already reworked a piece this month."
UNAFFORDABLE_REFUSAL = "You don't have the silver to have it reworked."

# Refusals that offer the player nothing to do about this item, so a page leaves the control out
# rather than showing it disabled on every card in the stores
_SILENT_REFUSALS = frozenset({NOT_YOURS_REFUSAL, UNWORKABLE_REFUSAL, SUPERIOR_REFUSAL, NO_WEAPONSMITH_REFUSAL})


@dataclass(frozen=True, kw_only=True)
class ItemUpgrade:
    """
    What one step up the condition ladder makes of an item, and what the step costs.
    """

    condition: int
    modifier: int
    price: int
    costs: int

    @property
    def condition_label(self) -> str:
        return Item.ConditionChoices(self.condition).label


def get_item_upgrade(*, item: Item) -> ItemUpgrade | None:
    """
    The item one step up the condition ladder, or None where there is no step to take.

    Priced by the rule the generators price by, so a reworked sword is worth what a drawn sword of the
    same dice and modifier is worth, and the step costs exactly what it adds to the item's value:
    reworking is never cheaper than buying, only certain.
    """
    if item.type.is_fallback or item.condition >= Item.ConditionChoices.CONDITION_SUPERIOR:
        return None

    modifier = item.modifier + UPGRADE_MODIFIER_STEP
    price = BaseItemGenerator.get_price(dice_string=item.type.base_value, modifier=modifier)

    return ItemUpgrade(
        condition=item.condition + 1,
        modifier=modifier,
        price=price,
        costs=max(price - item.price, MINIMUM_UPGRADE_COSTS),
    )


def get_item_upgrade_refusal(*, item: Item, faction: Faction, month: int, balance: int) -> str | None:
    """
    Why "faction"'s weaponsmith may not rework this item now, or None if he may.

    First refusal wins, in the order "get_tending_refusal" reports its own: what the player can do least
    about is named first. Another faction's item is not his to rework, nothing makes a fallback or a
    superior piece any better, a forge is built and raised rather than waited for, a fight ends once it
    is played out and the month once it is over - and the price is the one thing he can go and raise
    silver for.

    The page offering the control and the view dispatching the command both ask this, so the two
    cannot disagree about one item. "handle_upgrade_item" re-checks the purse, the item and the month
    under the write lock, so a double-click is charged once.
    """
    if item.owner_id != faction.id:
        return NOT_YOURS_REFUSAL

    if item.type.is_fallback:
        return UNWORKABLE_REFUSAL

    upgrade = get_item_upgrade(item=item)
    if upgrade is None:
        return SUPERIOR_REFUSAL

    weaponsmith = Weaponsmith.get_building_by_type(building_type=faction.town.weaponsmith)
    if not weaponsmith.can_upgrade_item():
        return NO_WEAPONSMITH_REFUSAL

    if upgrade.condition > weaponsmith.MAX_UPGRADE_CONDITION:
        return BEYOND_THE_FORGE_REFUSAL

    # A blow is rolled off a worn item while its fight is open, which is the lock that keeps the gear
    # from being handed out or sold from under him as well
    fight_refusal = get_unequip_refusal(item=item)
    if fight_refusal is not None:
        return fight_refusal

    if faction.town.last_item_upgraded_at == month:
        return ALREADY_UPGRADED_THIS_MONTH_REFUSAL

    if balance < upgrade.costs:
        return UNAFFORDABLE_REFUSAL

    return None


def get_item_upgrade_offer(*, item: Item, faction: Faction, month: int, balance: int) -> dict | None:
    """
    What a page offers for reworking this item: the step, why it may not be bought now, and whether the
    purse covers it - or None where there is nothing to offer at all.

    Off the refusal the upgrade view itself asks, so a button can never offer a rework the click would
    refuse. A purse that falls short is priced on the button rather than told it is short, the way the
    tending and the buildings are: the number is what the player has to go and raise.
    """
    refusal = get_item_upgrade_refusal(item=item, faction=faction, month=month, balance=balance)
    if refusal in _SILENT_REFUSALS:
        return None

    return {
        "upgrade": get_item_upgrade(item=item),
        "refusal": None if refusal == UNAFFORDABLE_REFUSAL else refusal,
        "can_afford": refusal != UNAFFORDABLE_REFUSAL,
    }
