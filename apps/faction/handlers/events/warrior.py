from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddWarriorToPub, SetNewLeaderWarrior
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RestockTownMercenaries
from apps.faction.messages.events.faction import NewFactionCreated
from apps.faction.messages.events.warrior import FyrdDraftApproved
from apps.month.messages.events.month import PlayerMonthPrepared
from apps.warrior.messages.events.warrior import (
    NewLeaderWarriorCreated,
    WarriorCreated,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


@message_registry.register_event(event=NewLeaderWarriorCreated)
def handle_set_new_leader_for_faction(*, context: NewLeaderWarriorCreated) -> Command:
    return SetNewLeaderWarrior(faction=context.faction, warrior=context.warrior)


@message_registry.register_event(event=WarriorCreated)
def handle_add_new_warrior_to_faction_pub(*, context: WarriorCreated) -> Command:
    # Stock, because the only thing raising WarriorCreated is the monthly restock asking for a man to
    # fill a stool: his row exists to be hired or swept away with the next one
    return AddWarriorToPub(
        savegame=context.savegame,
        faction=context.faction,
        warrior=context.warrior,
        is_pub_stock=True,
        month=context.month,
    )


@message_registry.register_event(event=WarriorWasDismissed)
def handle_add_dismissed_warrior_to_pub(*, context: WarriorWasDismissed) -> Command:
    """
    The man the player sent away waits in the pub to be taken back.

    Not stock, which is the whole point of the flag: the restock empties its shelf with a row delete,
    and a veteran destroyed at the start of the next month would be a dismissal the player cannot
    undo and a warrior gone from the savegame for good.
    """
    return AddWarriorToPub(
        savegame=context.savegame,
        faction=context.faction,
        warrior=context.warrior,
        is_pub_stock=False,
        month=context.month,
    )


@message_registry.register_event(event=WarriorWalkedOutOverUnpaidSalary)
def handle_add_warrior_who_walked_out_to_pub(*, context: WarriorWalkedOutOverUnpaidSalary) -> Command | None:
    """
    The man who walked out over unpaid wages waits in the pub to be taken back.

    Not stock, for the reason the dismissed man is not: the restock empties its shelf with a row
    delete, and a veteran destroyed at the start of the next month would be gone from the savegame
    for good.

    Nothing else has to hold him back. He costs two months of the wage that drove him off
    ([Warrior.hiring_price]), so the purse decides when the second chance becomes real, and nobody on
    the shelf is mended by the monthly sweep - a man who left wounded is still wounded when the
    silver returns.

    Rivals go unpaid on the same rule, and their men must not turn up here: there is one pub in a
    savegame and it is the player's, so every rival that missed its payroll would be stocking his
    shelf with trained veterans. A rival's man stays where he has always been - no faction, no pub,
    out of reach - until #157 gives him a market. The comparison reads two loaded rows and touches no
    database, which is what keeps it legal in an event handler.
    """
    if context.savegame.player_faction_id != context.faction.id:
        return None

    return AddWarriorToPub(
        savegame=context.savegame,
        faction=context.faction,
        warrior=context.warrior,
        is_pub_stock=False,
        month=context.month,
    )


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=PlayerMonthPrepared)
def handle_restock_mercenaries_in_pub_for_new_month(*, context: PlayerMonthPrepared | NewFactionCreated) -> Command:
    return RestockTownMercenaries(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=FyrdDraftApproved)
def handle_draft_warrior_for_approved_fyrd_draft(*, context: FyrdDraftApproved) -> Command:
    # Pure mapping, because handle_consider_fyrd_draft already weighed the whole decision. That is
    # what lets a rival's monthly draft run through the same command the player's fyrd card
    # dispatches instead of a second flow beside it.
    return DraftWarriorFromFyrd(faction=context.faction, month=context.month)
