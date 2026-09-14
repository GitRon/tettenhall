from apps.warband.item.models.item import Item
from apps.warband.skirmish.models.warrior import Warrior

WEARER_REFUSAL = "He is in a fight nobody has settled. He fights on with what he marched out with."
HOLDER_REFUSAL = "{name} is in a fight nobody has settled. What he marched out with stays on him."


def get_warriors_in_an_open_fight(*, warrior_list: list[Warrior]) -> set[int]:
    """
    Which of these men are standing on the roster of a fight nobody has played out, by id.

    One query for however many warriors are asked about, because both callers below hold a pair and
    the picker holds a whole roster - the same reason "get_dismissal_refusals" takes a list.

    "filter_standing_in_an_open_fight" and not "exclude_currently_busy", which is the broader rule
    dismissal answers from. The two now disagree about who is unavailable, and that is the decision
    rather than an oversight: a pending quest contract points at a warrior who must not vanish out of
    it, so dismissal has to refuse a man the day he signs on. A slot is only read while a blow is
    being thrown, so arming before the rosters are fixed is the decision the gear economy is built on
    and a settled fight has no roll left to exploit.
    """
    return set(
        Warrior.objects.filter(id__in=[warrior.id for warrior in warrior_list])
        .filter_standing_in_an_open_fight()
        .values_list("id", flat=True)
    )


def get_equip_refusal(*, warrior: Warrior, item: Item | None) -> str | None:
    """
    Why this item may not fill this man's slot, or None if it may.

    Asked about both ends, because since the slot started offering what other warriors carry a save
    writes two rows: picking an item somebody holds takes it off him. A guard that only measured the
    man being edited would leave the whole exploit reachable from the other end - the receiver
    sitting safely at home while the sword is on somebody standing in the line.

    The wearer is named first for the reason "get_building_upgrade_refusal" orders its own guards:
    the sentence the player can do least about goes first. Nothing he picks will make his own man
    editable, while a different item is one click away.

    An empty slot is a handout with no far end, and so is an item nobody is carrying - both answer
    the wearer's own verdict and nothing more.
    """
    holder = item.worn_by if item else None
    fighting_ids = get_warriors_in_an_open_fight(warrior_list=[warrior, *([holder] if holder else [])])

    if warrior.id in fighting_ids:
        return WEARER_REFUSAL

    if holder is not None and holder.id in fighting_ids:
        return HOLDER_REFUSAL.format(name=holder.display_name)

    return None


def get_unequip_refusal(*, item: Item) -> str | None:
    """
    Why this item may not be taken out of the game, or None if it may.

    Selling is the third way a slot empties, and it empties it without naming a warrior at all:
    "update_ownership" clears whoever is wearing the item. No page offers it for a worn item - the
    column is built from "get_all_unoccupied_items" - so this guards the hand-made request, which is
    exactly the request the exploit would be made from once the two above are closed.
    """
    holder = item.worn_by

    if holder is None:
        return None

    if holder.id in get_warriors_in_an_open_fight(warrior_list=[holder]):
        return HOLDER_REFUSAL.format(name=holder.display_name)

    return None
