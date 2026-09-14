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


def annotate_held_gear_values(*, roster: Iterable[Warrior]) -> list[Warrior]:
    """
    What each man on the roster has in each slot, as the figure the picker has to beat.

    Hung on the man rather than worked out per option, because a picker asks the question once per
    item per man and only the man's half can be shared: there is a card per unused item and they all
    offer the same roster.

    An empty slot is worth what the fight says it is worth. A bare-handed man still throws the
    fallback's dice ("Warrior.get_weapon_or_fallback"), so comparing against nothing would call every
    empty slot the same and rank none of them. That method fetches its type on every call, which is a
    query per option here - so the two fallbacks are read once for the whole column instead, and the
    slots they fill are the slots this answers for.

    The filled case costs nothing: "Faction.get_all_living_warriors" already carries "weapon__type"
    and "armor__type", and "type" is where the dice live.
    """
    fallback_values = {
        fallback.gear_slot: fallback.expectancy_value
        for fallback in (Item(type=item_type) for item_type in ItemType.objects.filter(is_fallback=True))
    }

    warriors = list(roster)
    for warrior in warriors:
        warrior.held_gear_values = {}
        for slot, fallback_value in fallback_values.items():
            held_item = getattr(warrior, slot)
            warrior.held_gear_values[slot] = held_item.expectancy_value if held_item else fallback_value

    return warriors


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
