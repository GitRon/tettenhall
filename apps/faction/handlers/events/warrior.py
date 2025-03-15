from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddWarriorToPub, SetNewLeaderWarrior
from apps.faction.messages.commands.warrior import RestockTownMercenaries
from apps.faction.messages.events.faction import NewFactionCreated
from apps.month.messages.events.month import MonthPrepared
from apps.warrior.messages.events.warrior import NewLeaderWarriorCreated, WarriorCreated


@message_registry.register_event(event=NewLeaderWarriorCreated)
def handle_set_new_leader_for_faction(*, context: NewLeaderWarriorCreated) -> Command:
    return SetNewLeaderWarrior(faction=context.faction, warrior=context.warrior)


@message_registry.register_event(event=WarriorCreated)
def handle_add_new_warrior_to_faction_pub(*, context: WarriorCreated) -> Command:
    return AddWarriorToPub(faction=context.faction, warrior=context.warrior, month=context.month)


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=MonthPrepared)
def handle_restock_mercenaries_in_pub_for_new_month(*, context: MonthPrepared | NewFactionCreated) -> Command:
    return RestockTownMercenaries(faction=context.faction, month=context.current_month)
