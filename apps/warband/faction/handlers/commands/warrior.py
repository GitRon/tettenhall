from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.faction.messages.commands.warrior import (
    AddWarriorToPub,
    DraftWarriorFromFyrd,
    PayMonthlyWarriorSalaries,
    RecruitPubMercenary,
    RestockTownMercenaries,
)
from apps.warband.faction.messages.events.faction import (
    MonthlyWarriorSalariesPaid,
    MonthlyWarriorSalariesUnpaid,
)
from apps.warband.faction.messages.events.warrior import (
    PubMercenarySlotOpened,
    TownMercenariesRestocked,
    WarriorRecruited,
    WarriorWasAddedToPub,
)
from apps.warband.faction.models.culture import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models import Transaction
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.projections.payroll import Payroll
from apps.warband.town.buildings.hall import Hall
from apps.warband.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator
from apps.warband.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_command(command=RestockTownMercenaries)
def handle_restock_pub_mercenaries(*, context: RestockTownMercenaries) -> list[Event] | Event:
    # Every faction's town has a pub, sized by its own hall. Clean up previous stock, and only the
    # stock. This is a warrior queryset, so it deletes the rows themselves - right for a mercenary
    # nobody hired, and fatal for a man sent away, who waits on the same shelf and would be destroyed
    # at the start of the next month.
    context.faction.available_mercenaries.filter(is_pub_stock=True).delete()

    events = []

    # Get hall building
    hall_type = context.faction.town.hall
    hall_building = Hall.get_building_by_type(building_type=hall_type)

    for _ in range(hall_building.AVAILABLE_MERCENARIES):
        events.append(
            PubMercenarySlotOpened(
                savegame=context.faction.savegame,
                # He belongs to nobody while he stands for hire, but he stands in this town
                faction=None,
                pub_owner=context.faction,
                culture=Culture.objects.all().order_by("?").first(),
                generator_class=MercenaryWarriorGenerator,
                month=context.month,
            )
        )

    # After the loop, and counting the whole pub rather than each man: the player wants to know
    # whether it is worth walking over, not that a stool was filled
    events.append(
        TownMercenariesRestocked(
            faction=context.faction,
            new_mercenaries=hall_building.AVAILABLE_MERCENARIES,
            month=context.month,
        )
    )

    return events


@message_registry.register_command(command=AddWarriorToPub)
def handle_add_warrior_to_pub(*, context: AddWarriorToPub) -> list[Event] | Event:
    # The pub named on the message, never one read off the warrior: a generated mercenary arrives
    # without a faction of his own, and a man who left a roster has just lost his.
    context.pub_owner.available_mercenaries.add(context.warrior)
    # Written here rather than by whoever generated or released the man, because this is the one
    # place a warrior ever ends up on the shelf: a mercenary hired out of the pub and later sent away
    # comes back through this same command and is marked afresh, so the flag cannot go stale on him.
    Warrior.objects.set_pub_stock(obj=context.warrior, is_pub_stock=context.is_pub_stock)
    # Stamped here for the same reason, and it is the same one place: all three routes onto the shelf
    # - the mercenary the restock rolled, the man the player sent away and the man who walked out
    # over unpaid wages - arrive through this command. A man who comes back a second time starts his
    # wait again rather than inheriting the date of the first.
    Warrior.objects.set_pub_arrival(obj=context.warrior, month=context.month)

    return WarriorWasAddedToPub(pub_owner=context.pub_owner, warrior=context.warrior, month=context.month)


@message_registry.register_command(command=DraftWarriorFromFyrd)
def handle_draft_warrior_from_fyrd(*, context: DraftWarriorFromFyrd) -> list[Event] | Event | None:
    # Asked of the row rather than of the instance the view read: a double click sends two drafts
    # that both saw a reserve of 1, and only one of them may raise a warrior
    if not Faction.objects.draw_from_fyrd_reserve(faction=context.faction):
        return None

    # Create warrior
    warrior_generator = FyrdWarriorGenerator(
        culture=context.faction.culture, faction=context.faction, savegame_id=context.faction.savegame_id
    )
    warrior = warrior_generator.process()

    return WarriorRecruited(
        faction=context.faction,
        warrior=warrior,
        recruitment_price=0,
        month=context.month,
    )


@message_registry.register_command(command=RecruitPubMercenary)
def handle_recruit_pub_mercenary(*, context: RecruitPubMercenary) -> list[Event] | Event | None:
    """
    Hire the man standing in the pub.

    No morale malus, unlike recruiting a captive: a mercenary who took the silver is not fighting
    under duress. What he is instead is a man with no village of his own to defend, and the generator
    is where that shows - his morale rolls low to begin with.

    The price rides on the event rather than being spent here, so the ledger row is the finance app's
    to write the way every other payment in the game is.

    What he costs is "hiring_price" and not "recruitment_price": the pub also holds the men the player
    sent away, whose rolled price describes the levy they were rather than the veteran standing there
    now. One number for both, so a man costs the same whether he was generated for the shelf or
    walked onto it.

    What he owes is cleared, because the shelf also holds the man who walked out over the full term
    of unpaid wages - see [forgive_unpaid_months].
    """
    # Read before anything below moves him, because taking him off the shelf ends the wait his price
    # is partly made of - see [Warrior.idle_surcharge]. Reading it at the bottom would bill a veteran
    # the price of a man who had never been parked, which is the loophole the surcharge closes.
    hiring_price = context.warrior.hiring_price

    # Only while the purse still covers him: a hire and a purchase elsewhere can each pass their view's
    # check on the same balance, and only the one that gets the write lock first may spend it
    if Transaction.objects.current_balance(faction_id=context.faction.id) < hiring_price:
        return None

    # Off the shelf first, and only if he is still on it: the second of two overlapping hires finds
    # him gone, and would otherwise be charged for a man already in the war band
    if not Faction.objects.remove_mercenary_from_pub(faction=context.faction, warrior=context.warrior):
        return None

    Warrior.objects.set_faction(obj=context.warrior, faction=context.faction)
    Warrior.objects.forgive_unpaid_months(obj=context.warrior)
    Warrior.objects.transfer_equipment_ownership(obj=context.warrior, new_owner=context.faction)
    Warrior.objects.set_pub_arrival(obj=context.warrior, month=None)

    return WarriorRecruited(
        warrior=context.warrior,
        faction=context.faction,
        recruitment_price=hiring_price,
        month=context.month,
    )


@message_registry.register_command(command=PayMonthlyWarriorSalaries)
def handle_warrior_monthly_salaries(*, context: PayMonthlyWarriorSalaries) -> list[Event] | Event:
    """
    Pay this month's wages, as far as the purse reaches.

    The one bill in the game that arrives whether or not it can be met - every other check in the
    codebase guards a purchase somebody chose to make - so it is also the only one that has to
    decide what happens when it cannot. It pays the roster cheapest man first and stops when the
    silver does, which fits the most men into what there is and leaves the shortfall on the dearest.

    Both events can come out of one month: a faction that covered three of its five warriors paid
    something and failed to pay something. The paid event stays silent at zero, though, because it
    writes a transaction and a log line, and "salaries of 0 silver paid" directly above "you were
    150 short" reads as a contradiction.

    Who ends up on which side is [Payroll]'s answer rather than this handler's, so the card that
    warns the player beforehand can ask the same question and get the same men.
    """
    payroll = Payroll.for_faction(
        faction=context.faction,
        budget=Transaction.objects.current_balance(faction_id=context.faction.id),
    )

    # Two writes for the whole roster rather than two per man: this runs on the synchronous month
    # advance, and #3 is about to multiply it by every rival faction in the savegame
    Warrior.objects.record_salaries_paid(warrior_list=payroll.paid_warrior_list)
    Warrior.objects.record_salaries_unpaid(warrior_list=payroll.unpaid_warrior_list)

    message_list = []

    if payroll.paid_amount > 0:
        message_list.append(
            MonthlyWarriorSalariesPaid(
                faction=context.faction,
                amount=payroll.paid_amount,
                month=context.month,
            )
        )

    if payroll.is_short:
        message_list.append(
            MonthlyWarriorSalariesUnpaid(
                faction=context.faction,
                warrior_list=payroll.unpaid_warrior_list,
                missing_amount=payroll.missing_amount,
                month=context.month,
            )
        )

    return message_list
