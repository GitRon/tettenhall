from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.events.faction import MonthlyWarriorSalariesUnpaid, NewFactionCreated
from apps.warband.faction.messages.events.warrior import PubMercenarySlotOpened, WarriorMonthPrepared
from apps.warband.warrior.messages.commands.warrior import (
    CreateNewLeaderWarrior,
    CreateWarrior,
    HealInjuredWarrior,
    PunishUnpaidWarrior,
    ReplenishWarriorMorale,
)


@message_registry.register_event(event=NewFactionCreated)
def handle_create_leader_for_new_faction(*, context: NewFactionCreated) -> Command:
    return CreateNewLeaderWarrior(faction=context.faction)


@message_registry.register_event(event=WarriorMonthPrepared)
def handle_heal_a_wounded_warrior_for_new_month(*, context: WarriorMonthPrepared) -> Command | None:
    """
    A man who is carrying a wound mends a little at the sanctuary of the faction holding him.

    Everybody the faction is responsible for arrives here, captives included, and this decides for
    itself whom that covers: health is what a captor can mend, so a prisoner heals from his captor's
    month and no comparison against the faction on the event is wanted. The faction is passed on
    rather than read off the warrior because a captive has none - it is his captor's sanctuary doing
    the mending and his captor's month log the line belongs in.

    The two columns are read off the instance the command handler loaded, which touches no database -
    strict mode's blocker forbids an event handler one. A man already at his maximum has nothing to
    mend, and asking the healing handler anyway would have it draw a random number and discard it.
    """
    if context.warrior.current_health >= context.warrior.max_health:
        return None

    return HealInjuredWarrior(faction=context.faction, warrior=context.warrior, month=context.month)


@message_registry.register_event(event=WarriorMonthPrepared)
def handle_replenish_a_warriors_morale_for_new_month(*, context: WarriorMonthPrepared) -> Command | None:
    """
    A man on the roster gets his nerve back, unless he is a prisoner or went unpaid.

    Three guards, all of them reading columns the event already carries.

    A captive is excluded by comparing his own faction against the one holding him, which is the one
    rule this handler cannot take from the event alone. Spirit is not something a captor can mend, and
    "handle_replenish_warrior_morale" refills to the maximum unconditionally, so a month in an enemy
    cell would otherwise restore a man completely. He keeps whatever the fight left him for as long as
    he is held and gets it back the moment "handle_recruit_captured_warrior" puts him under a banner -
    that handler fills him up itself rather than leaving him to wait a month and march out empty.

    A man who was not paid does not cheer up either, and the "unpaid_months" guard is what makes that
    stick: the refill is to the maximum, so without it every point insolvency had just taken would
    come straight back in the same month it was taken.

    And only a man below his ceiling has anything to recover - the rest would be a no-op further down
    the chain.
    """
    if context.warrior.faction_id != context.faction.id:
        return None

    if context.warrior.unpaid_months > 0:
        return None

    if context.warrior.current_morale >= context.warrior.max_morale:
        return None

    return ReplenishWarriorMorale(warrior=context.warrior, month=context.month)


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
        pub_owner=context.pub_owner,
        culture=context.culture,
        generator_class=context.generator_class,
        month=context.month,
    )
