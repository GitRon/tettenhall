from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddWarriorToPub, SetNewLeaderWarrior
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RestockTownMercenaries
from apps.faction.messages.events.faction import NewFactionCreated
from apps.faction.messages.events.warrior import FyrdDraftApproved
from apps.month.messages.events.month import PlayerMonthPrepared
from apps.warrior.messages.events.warrior import NewLeaderWarriorCreated, WarriorCreated


@message_registry.register_event(event=NewLeaderWarriorCreated)
def handle_set_new_leader_for_faction(*, context: NewLeaderWarriorCreated) -> Command:
    return SetNewLeaderWarrior(faction=context.faction, warrior=context.warrior)


@message_registry.register_event(event=WarriorCreated)
def handle_add_new_warrior_to_faction_pub(*, context: WarriorCreated) -> Command:
    return AddWarriorToPub(
        savegame=context.savegame, faction=context.faction, warrior=context.warrior, month=context.month
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
