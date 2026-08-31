from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.faction import AddWarriorToPub, PayMonthlyWarriorSalaries
from apps.faction.messages.commands.warrior import (
    ConsiderFyrdDraft,
    DraftWarriorFromFyrd,
    RecruitPubMercenary,
    RestockTownMercenaries,
)
from apps.faction.messages.events.faction import (
    MonthlyWarriorSalariesPaid,
    MonthlyWarriorSalariesUnpaid,
    WarriorWasAddedToPub,
)
from apps.faction.messages.events.warrior import FyrdDraftApproved, PubMercenarySlotOpened, WarriorRecruited
from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction
from apps.finance.models import Transaction
from apps.skirmish.models import Warrior
from apps.skirmish.projections.payroll import Payroll
from apps.town.buildings.hall import Hall
from apps.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@message_registry.register_command(command=RestockTownMercenaries)
def handle_restock_pub_mercenaries(*, context: RestockTownMercenaries) -> list[Event] | Event:
    # Only the player's town has a pub that can be visited, and the mercenaries this requests are
    # generated without a faction of their own, so handle_add_warrior_to_pub can only ever stock
    # that one. Restocking a rival - which NewFactionCreated does for each of them - would add its
    # mercenaries to the player's pub on top of the player's own restock.
    if context.faction.savegame.player_faction_id != context.faction.id:
        return []

    # Clean up previous stock
    context.faction.available_mercenaries.all().delete()

    events = []

    # Get hall building
    hall_type = context.faction.town.hall
    hall_building = Hall.get_building_by_type(building_type=hall_type)

    for _ in range(hall_building.AVAILABLE_MERCENARIES):
        events.append(
            PubMercenarySlotOpened(
                savegame=context.faction.savegame,
                faction=None,
                culture=Culture.objects.all().order_by("?").first(),
                generator_class=MercenaryWarriorGenerator,
                month=context.month,
            )
        )
        # TODO (#97): create event to show the user that we've finished and let user log listend to it

    return events


@message_registry.register_command(command=AddWarriorToPub)
def handle_add_warrior_to_pub(*, context: AddWarriorToPub) -> list[Event] | Event:
    # The pub belongs to the player, and there is only one player per savegame, so this is the right
    # target - the warrior arrives here without a faction of its own. handle_restock_pub_mercenaries
    # only requests these for the player faction, so nothing else ends up in this pub.
    context.savegame.player_faction.available_mercenaries.add(context.warrior)

    return WarriorWasAddedToPub(faction=context.faction, warrior=context.warrior, month=context.month)


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
    """
    Warrior.objects.set_faction(obj=context.warrior, faction=context.faction)
    Warrior.objects.transfer_equipment_ownership(obj=context.warrior, new_owner=context.faction)
    Faction.objects.remove_mercenary_from_pub(faction=context.faction, warrior=context.warrior)

    return WarriorRecruited(
        warrior=context.warrior,
        faction=context.faction,
        recruitment_price=context.warrior.recruitment_price,
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
