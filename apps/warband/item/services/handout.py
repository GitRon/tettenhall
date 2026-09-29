from collections.abc import Iterable

from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.models.warrior import Warrior

# What a slot is called in a sentence. The field is spelled the American way and the game is not, so
# the two names have to be kept apart rather than the field name being printed.
SLOT_NAMES = {
    "weapon": "weapon",
    "armor": "armour",
}


def get_fallback_values() -> dict[str, float]:
    """
    What an empty slot is worth, per slot: the dice a bare-handed man still throws.
    """
    return {
        fallback.gear_slot: fallback.expectancy_value
        for fallback in (Item(type=item_type) for item_type in ItemType.objects.filter(is_fallback=True))
    }


def annotate_held_gear_values(*, roster: Iterable[Warrior]) -> list[Warrior]:
    """
    What each man on the roster has in each slot, as the figure the picker has to beat.

    Hung on the man rather than worked out per option, because a picker asks the question once per
    item per man and only the man's half can be shared: there is a card per unused item and they all
    offer the same roster.

    An empty slot is worth what the fight says it is worth. A bare-handed man still throws the
    fallback's dice ("Warrior.get_weapon_or_fallback"), so comparing against nothing would call every
    empty slot the same and rank none of them. That method caches the fallbacks per man, which is still
    a query per option here - so the two are read once for the whole column instead, and the slots they
    fill are the slots this answers for.

    The filled case costs nothing: "Faction.get_all_living_warriors" already carries "weapon__type"
    and "armor__type", and "type" is where the dice live.
    """
    fallback_values = get_fallback_values()

    warriors = list(roster)
    for warrior in warriors:
        warrior.held_gear_values = {}
        for slot, fallback_value in fallback_values.items():
            held_item = getattr(warrior, slot)
            warrior.held_gear_values[slot] = held_item.expectancy_value if held_item else fallback_value

    return warriors


def get_handout_roster(*, faction) -> list[Warrior]:
    """
    The men an unused item may be handed to, each carrying what his slots are worth.

    A man standing in a fight nobody has settled fights on with what he marched out with, so handing
    him something would be a control that could only ever be refused - the refusal lives in
    "get_equip_refusal", which the assign view asks before it dispatches.
    """
    return annotate_held_gear_values(
        roster=faction.get_all_living_warriors().exclude(
            id__in=Warrior.objects.filter_standing_in_an_open_fight().values("id")
        )
    )


def rank_for_slot(*, roster: Iterable[Warrior], leader_id: int | None, slot: str) -> list[Warrior]:
    """
    The order a faction hands out one slot's gear in: the leader first, then by level.

    The leader goes first because losing him loses the faction. A tie on level goes to the man the slot
    does most for - strength for a weapon, which scales the blow, and maximum health for armour, the man
    with the most to lose to one. The id settles the rest, so the same roster always ranks the same way.
    """
    tie_breaker = "strength" if slot == "weapon" else "max_health"

    return sorted(
        roster,
        key=lambda warrior: (
            warrior.id != leader_id,
            -warrior.level,
            -getattr(warrior, tie_breaker),
            warrior.id,
        ),
    )


def plan_gear_handout(*, faction) -> list[tuple[Warrior, Item, str]]:
    """
    Which of a faction's items go to which of its men: the best of each slot to the best man, and so on
    down the line. Answered as the equips that get there, in the order they have to run.

    The pool is everything the faction could put in a man's hand - the stores and what its men already
    carry. A man standing in an open fight is not on the roster, so he and what he holds are left out of
    both, for the reason "get_equip_refusal" gives.

    Each man takes the best item still free, but only if it beats what he holds now - an empty slot
    being worth the fallback's dice, as in "annotate_held_gear_values". Equal is not better, so a man is
    never handed a sidegrade.

    The walk replays "handle_equip_item" as it goes rather than planning against the state it started
    from: taking an item off another man hands him the receiver's old one, and a man further down may
    then want that. Every equip lands on a man before anybody below him is considered, and nobody below
    him can take what he ended up with, so running the equips in this order ends on the state the walk
    ends on.
    """
    roster = get_handout_roster(faction=faction)
    stored_item_list = list(faction.get_all_unoccupied_items().select_related("type"))
    fallback_values = get_fallback_values()

    equip_list = []
    for slot in SLOT_NAMES:
        holding = {warrior.id: getattr(warrior, slot) for warrior in roster}
        holder_ids = {item.id: warrior_id for warrior_id, item in holding.items() if item}
        pool = [item for item in stored_item_list if item.gear_slot == slot] + [
            item for item in holding.values() if item
        ]
        settled_item_ids = set()

        for warrior in rank_for_slot(roster=roster, leader_id=faction.leader_id, slot=slot):
            held_item = holding[warrior.id]
            held_value = held_item.expectancy_value if held_item else fallback_values[slot]
            best_item = max(
                (item for item in pool if item.id not in settled_item_ids),
                key=lambda item: (item.expectancy_value, -item.id),
                default=None,
            )

            if best_item is not None and best_item.expectancy_value > held_value:
                previous_holder_id = holder_ids.get(best_item.id)
                holding[warrior.id] = best_item
                holder_ids[best_item.id] = warrior.id
                if previous_holder_id is not None:
                    # The exchange "handle_equip_item" makes, or an empty hand when there is nothing to give back
                    holding[previous_holder_id] = held_item
                if held_item:
                    holder_ids[held_item.id] = previous_holder_id
                equip_list.append((warrior, best_item, slot))

            if holding[warrior.id]:
                settled_item_ids.add(holding[warrior.id].id)

    return equip_list


def count_stored_upgrades(*, faction) -> int:
    """
    How many unused items in the stores would improve at least one man who could be handed them.

    An upgrade rather than an empty slot, because an empty slot stops being the question after the
    first months: every man carries something, and the sword that beats half of it sits in the
    stores unmentioned. A spare kept on purpose - no better than what anybody already holds - is
    not counted, so a player who keeps one is not told about it every month.
    """
    roster = get_handout_roster(faction=faction)
    if not roster:
        return 0

    return sum(
        1
        for item in faction.get_all_unoccupied_items().select_related("type")
        if improves_anybody(item=item, roster=roster)
    )


def improves_anybody(*, item: Item, roster: Iterable[Warrior]) -> bool:
    """
    Whether the item beats what at least one man on the roster holds in its slot.

    Equal is not better: a swap that gains nothing is not an upgrade. The roster has to arrive through
    "annotate_held_gear_values", which is where the figures being compared are hung on each man.
    """
    return any(item.expectancy_value > warrior.held_gear_values[item.gear_slot] for warrior in roster)


def get_handout_note(*, warrior: Warrior, item: Item | None, slot: str) -> str | None:
    """
    What the player has to be told about a handout he cannot see the far side of.

    Read *before* the gear moves, because it describes the state the move changes and afterwards
    there is nothing left to read it off.

    Both entry points fill a slot the player is looking at, and the answer to "did it arrive" is on
    the screen in front of him. What is not on the screen is the other end - a man somewhere down the
    roster who has just been disarmed, or an item that has quietly gone back into the stash - so
    those are the cases with a sentence and the rest answer None rather than narrating the obvious.
    """
    previous_holder = item.worn_by if item else None
    displaced_item = getattr(warrior, slot)

    # The slot saved on what was already in it. Nothing leaves the man and nothing reaches him, so
    # both ends fall away and there is no sentence - without this he is told he took his own sword
    # off himself and put it down.
    if displaced_item == item:
        return None

    if previous_holder and displaced_item:
        return f"Taken off {previous_holder.display_name}, who takes the {displaced_item.display_name} in exchange."

    if previous_holder:
        return f"Taken off {previous_holder.display_name}, who now carries no {SLOT_NAMES[slot]}."

    if displaced_item:
        return f"{warrior.display_name} puts the {displaced_item.display_name} back in the stash."

    return None
