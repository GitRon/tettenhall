from collections import Counter
from collections.abc import Iterable

from apps.warband.item.models.item import Item


def annotate_stored_copy_counts(*, item_list: Iterable[Item], faction) -> tuple[list[Item], int]:
    """
    Each item on the shelf with how many of its kind already lie unused in the faction's stores, and
    how many unused items the stores hold in all.

    The shop and the stores are two pages in two sections, so a player buying a second seax has no
    way to see the first one waiting for a man unless the shelf tells him. Matched on the type rather
    than the item: a worn seax and a fine one are the same weapon in the hand, which is the question
    being asked.

    Once for the whole shelf rather than once per card - every card asks the same stores.
    """
    stored_type_counts = Counter(faction.get_all_unoccupied_items().values_list("type_id", flat=True))

    items = list(item_list)
    for item in items:
        item.stored_copy_count = stored_type_counts[item.type_id]

    return items, stored_type_counts.total()
