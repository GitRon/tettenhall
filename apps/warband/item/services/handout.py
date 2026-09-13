from apps.warband.item.models.item import Item
from apps.warband.skirmish.models.warrior import Warrior

# What a slot is called in a sentence. The field is spelled the American way and the game is not, so
# the two names have to be kept apart rather than the field name being printed.
SLOT_NAMES = {
    "weapon": "weapon",
    "armor": "armour",
}


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
