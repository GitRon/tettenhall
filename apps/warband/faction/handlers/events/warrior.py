from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.faction import SetNewLeaderWarrior
from apps.warband.faction.messages.commands.warrior import (
    AddWarriorToPub,
    ConsiderPubHire,
    DraftWarriorFromFyrd,
    RecruitPubMercenary,
    RestockTownMercenaries,
)
from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.faction.messages.events.warrior import (
    FyrdDraftApproved,
    PubHiringConsidered,
    PubMercenaryHireApproved,
)
from apps.warband.month.messages.events.month import FactionMonthPrepared
from apps.warband.warrior.messages.events.warrior import (
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
        pub_owner=context.pub_owner,
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
        pub_owner=context.faction,
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

    Rivals go unpaid on the same rule, and their men do not go on a shelf yet. Every faction has a pub
    of its own, but whose shelf a veteran who left a rival stands on - that rival's, or a market every
    faction can reach - is #157's decision, and parking him in his old faction's pub would take it.
    A rival's man stays where he has always been - no faction, no pub, out of reach - until then. The
    comparison reads two loaded rows and touches no database, which is what keeps it legal in an
    event handler.
    """
    if context.savegame.player_faction_id != context.faction.id:
        return None

    return AddWarriorToPub(
        savegame=context.savegame,
        pub_owner=context.faction,
        warrior=context.warrior,
        is_pub_stock=False,
        month=context.month,
    )


@message_registry.register_event(event=NewFactionCreated)
def handle_restock_mercenaries_in_pub_for_new_faction(*, context: NewFactionCreated) -> Command:
    return RestockTownMercenaries(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=FactionMonthPrepared)
def handle_consider_pub_hire_for_new_month(*, context: FactionMonthPrepared) -> Command:
    # Every faction, because every faction's pub restocks behind this - see [handle_consider_pub_hire]
    return ConsiderPubHire(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=PubMercenaryHireApproved)
def handle_recruit_mercenary_for_approved_pub_hire(*, context: PubMercenaryHireApproved) -> Command:
    # Pure mapping, because handle_consider_pub_hire already weighed the whole decision. That is what
    # lets a rival hire through the same command the player's pub dispatches.
    return RecruitPubMercenary(warrior=context.warrior, faction=context.faction, month=context.month)


@message_registry.register_event(event=PubHiringConsidered)
def handle_restock_mercenaries_in_pub_once_hiring_is_considered(*, context: PubHiringConsidered) -> Command:
    return RestockTownMercenaries(faction=context.faction, month=context.month)


@message_registry.register_event(event=FyrdDraftApproved)
def handle_draft_warrior_for_approved_fyrd_draft(*, context: FyrdDraftApproved) -> Command:
    # Pure mapping, because handle_consider_fyrd_draft already weighed the whole decision. That is
    # what lets a rival's monthly draft run through the same command the player's fyrd card
    # dispatches instead of a second flow beside it.
    return DraftWarriorFromFyrd(faction=context.faction, month=context.month)
