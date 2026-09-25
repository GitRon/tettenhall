from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.faction.messages.commands.warrior import (
    AddWarriorToPub,
    ConsiderFyrdDraft,
    ConsiderPubHire,
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
    FyrdDraftApproved,
    PubHiringConsidered,
    PubMercenaryHireApproved,
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


@message_registry.register_command(command=ConsiderFyrdDraft)
def handle_consider_fyrd_draft(*, context: ConsiderFyrdDraft) -> list[Event] | Event | None:
    """
    Whether this faction calls somebody up out of its fyrd this month.

    A rival's only decision, and it is taken greedily: it drafts whenever the reserve and the purse
    allow, because there is nothing else for it to spend on yet and anything cleverer would be faction
    AI. The player is refused here - his draft is a button on the fyrd card, and choosing when to press
    it is the point of having one.

    "Can afford it" is a month of breathing room rather than the price of the man, because a draft is
    free and what it commits the faction to is his keep. So the purse has to still cover the roster's
    wage bill once over, read off the same [Payroll] the salary run bills from.

    The purse being read is the one the month opened with, and that is not a matter of where this sits
    among the monthly handlers. Nothing the month earns or spends reaches the ledger until every
    command those handlers raised has run: a salary run and an income both return an *event*, and the
    "CreateTransaction" it turns into is queued behind the whole batch. So every faction weighs the
    same balance it started the month on, whichever order the handlers run in - which also means the
    wage bill this compares against has been committed but not yet debited.

    A faction with no roster passes trivially, which is how one that has been emptied out starts
    rebuilding.

    All three questions are queries, which is why this is a command handler at all: the event handler
    on the monthly event may only raise this and let it decide.
    """
    if context.faction.savegame.player_faction_id == context.faction.id:
        return None

    if context.faction.fyrd_reserve <= 0:
        return None

    # budget=0 on purpose: "total_amount" is the whole roster's wages either way, and handing it the
    # balance would read as though the comparison were self-satisfying. It also means a future
    # "total_amount" that did respect the budget could not quietly turn this into "balance < balance",
    # which is false for every faction and would draft on every reserve there is.
    balance = Transaction.objects.current_balance(faction_id=context.faction.id)
    if balance < Payroll.for_faction(faction=context.faction, budget=0).total_amount:
        return None

    return FyrdDraftApproved(faction=context.faction, month=context.month)


@message_registry.register_command(command=ConsiderPubHire)
def handle_consider_pub_hire(*, context: ConsiderPubHire) -> list[Event]:
    """
    Which of the men standing in this faction's pub it takes on this month.

    Shaped like [handle_consider_fyrd_draft], and for the same reasons. The player is refused -
    hiring is a button in his pub. A rival buys greedily, because anything cleverer is faction AI:
    cheapest first, which fits the most men into the purse, for as long as the purse still covers the
    wage bill once over after paying for him. Unlike a draft a hire has a price, so the price comes
    out of the purse before the wages are weighed against it.

    The purse is tracked here across the men it takes rather than re-read per man. The price of a
    hire rides on "WarriorRecruited" and reaches the ledger only after the whole batch, so a second
    read would still see the silver the first man was bought with.

    The shelf is the one that stood in the pub all month, and "PubHiringConsidered" comes last on
    purpose: the restock hangs off it and clears the shelf with a row delete, and a man approved here
    is only taken off it once his "RecruitPubMercenary" drains. The approvals are queued first, so
    their commands drain first, whatever order anything else runs in.
    """
    considered = PubHiringConsidered(faction=context.faction, month=context.month)

    if context.faction.savegame.player_faction_id == context.faction.id:
        return [considered]

    purse = Transaction.objects.current_balance(faction_id=context.faction.id)
    # budget=0 for the same reason handle_consider_fyrd_draft gives: "total_amount" is the whole
    # roster's wages either way
    wage_bill = Payroll.for_faction(faction=context.faction, budget=0).total_amount

    # Priced once per man, and before anything moves him - the price is partly made of his wait
    priced_mercenary_list = sorted(
        ((mercenary.hiring_price, mercenary) for mercenary in context.faction.available_mercenaries.all()),
        key=lambda priced: (priced[0], priced[1].id),
    )

    events = []
    for hiring_price, mercenary in priced_mercenary_list:
        if purse - hiring_price < wage_bill + mercenary.monthly_salary:
            continue

        purse -= hiring_price
        wage_bill += mercenary.monthly_salary
        events.append(PubMercenaryHireApproved(faction=context.faction, warrior=mercenary, month=context.month))

    events.append(considered)

    return events


@message_registry.register_command(command=DraftWarriorFromFyrd)
def handle_draft_warrior_from_fyrd(*, context: DraftWarriorFromFyrd) -> list[Event] | Event | None:
    if context.faction.fyrd_reserve <= 0:
        return None

    # Create warrior
    warrior_generator = FyrdWarriorGenerator(
        culture=context.faction.culture, faction=context.faction, savegame_id=context.faction.savegame_id
    )
    warrior = warrior_generator.process()

    # Update reserve
    Faction.objects.reduce_fyrd_reserve(faction=context.faction, drafted_warriors=1)

    return WarriorRecruited(
        faction=context.faction,
        warrior=warrior,
        recruitment_price=0,
        month=context.month,
    )


@message_registry.register_command(command=RecruitPubMercenary)
def handle_recruit_pub_mercenary(*, context: RecruitPubMercenary) -> list[Event] | Event:
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

    Warrior.objects.set_faction(obj=context.warrior, faction=context.faction)
    Warrior.objects.forgive_unpaid_months(obj=context.warrior)
    Warrior.objects.transfer_equipment_ownership(obj=context.warrior, new_owner=context.faction)
    Faction.objects.remove_mercenary_from_pub(faction=context.faction, warrior=context.warrior)
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
