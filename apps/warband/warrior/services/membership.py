from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.models.warrior import Warrior


def is_on_roster(*, warrior: Warrior, faction: Faction) -> bool:
    """
    Whether this man stands on "faction"'s roster now, read off the row rather than the instance.

    What a view hiring or recruiting a man asks after it dispatches, so its line describes where he
    ended up rather than the click: a mercenary whose price another spend took first, or a captive
    sold by an overlapping request, is not announced as joining.
    """
    return Warrior.objects.filter(id=warrior.id, faction=faction).exists()


def was_sold_from_cells(*, warrior: Warrior, faction: Faction) -> bool:
    """
    Whether this man is gone from "faction"'s cells without joining any roster - which is what selling
    him leaves behind.

    The enslave view's read-back: a captive recruited by an overlapping request is on the roster, and
    one still in the cells was not sold at all.
    """
    return (
        Warrior.objects.filter(id=warrior.id, faction__isnull=True)
        .exclude(id__in=faction.captured_warriors.values("id"))
        .exists()
    )
