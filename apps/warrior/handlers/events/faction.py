from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import MonthlyWarriorSalariesUnpaid, NewFactionCreated
from apps.faction.messages.events.warrior import PubMercenarySlotOpened
from apps.warrior.messages.commands.warrior import CreateNewLeaderWarrior, CreateWarrior, PunishUnpaidWarrior


@message_registry.register_event(event=NewFactionCreated)
def handle_create_leader_for_new_faction(*, context: NewFactionCreated) -> Command:
    return CreateNewLeaderWarrior(faction=context.faction)


@message_registry.register_event(event=MonthlyWarriorSalariesUnpaid)
def handle_unpaid_warriors(*, context: MonthlyWarriorSalariesUnpaid) -> list[Command]:
    # One command per man rather than one for the list, because what happens to him depends on how
    # long he has gone without - and that decision reads the roster, which an event handler may not
    # do under strict mode
    return [
        PunishUnpaidWarrior(warrior=warrior, faction=context.faction, month=context.month)
        for warrior in context.warrior_list
    ]


@message_registry.register_event(event=PubMercenarySlotOpened)
def handle_pub_mercenary_slot_opened(*, context: PubMercenarySlotOpened) -> Command:
    return CreateWarrior(
        savegame=context.savegame,
        faction=context.faction,
        culture=context.culture,
        generator_class=context.generator_class,
        month=context.month,
    )
