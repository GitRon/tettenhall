from dataclasses import dataclass

from apps.warband.calendar.months import YEAR, CalendarMonth
from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models.transaction import Transaction
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.item.models.item import Item
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.projections.payroll import Payroll


@dataclass(kw_only=True)
class IncidentOutcome:
    """
    What one incident actually does, with everything it needed to look up already resolved.

    Two sentences and a set of levers. The levers are named rather than applied: an incident is
    resolved in a command handler, where the database may be read, and applied by the apps that own
    the rows - so what travels between the two has to be plain data.

    A lever left at its default is a lever this incident does not pull. "warrior" carries the man
    "max_morale_share" moves, which is also the man the title names: outside a skirmish nobody
    watches morale, so an unnamed change is invisible.
    """

    title: str
    body: str
    silver_change: int = 0
    fyrd_change: int = 0
    max_morale_share: float = 0.0
    warrior: Warrior | None = None
    lost_item: Item | None = None


@dataclass(frozen=True, kw_only=True)
class IncidentOption:
    """
    One answer a question-shaped entry accepts, and what it does when it is given.

    "label" is the button, "title" and "body" are the chronicle line the answer leaves behind. The
    levers are the same ones an ordinary entry sets as class constants, so an answer lands through
    the four handlers every incident already has - and through "IncidentOutcome.warrior", once an
    entry is about a man rather than the faction.

    "sells_item" hands over the piece of gear the question was asked about, which is the gear lever
    with the item chosen when the question was asked rather than when it is answered.
    """

    key: str
    label: str
    title: str
    body: str
    silver_change: int = 0
    fyrd_change: int = 0
    sells_item: bool = False


@dataclass(kw_only=True)
class IncidentQuestion:
    """
    What a question-shaped entry asks, with what it is about already chosen.

    "rival" and "item" are held on the pending row until the answer lands, because the answer has to
    be about the same rival and the same piece of gear the question named.
    """

    title: str
    body: str
    rival: Faction | None = None
    item: Item | None = None


class Incident:
    """
    One thing the world does to the player between his own decisions.

    An entry of the catalogue is a class: a weight, two sentences and the levers it moves as class
    constants, the way "apps/town/buildings/" holds a building's numbers. Most entries need nothing
    else - [resolve] below turns the constants into an outcome, so adding one to
    "apps/incident/incidents/__init__.py" is the whole of adding an incident.

    Override [resolve] only where the outcome depends on the faction: which warrior the title names,
    which item goes missing, how much of a reserve is actually left to lose. Not abstract, and not an
    ABC: an entry with no code of its own is the normal case here, so there is nothing a subclass
    must implement.

    **Preconditions read the state the month opened with.** Selection hangs off
    "PlayerMonthPrepared", which the bus reaches before a single warrior has been paid, healed or
    rallied - so [is_possible] sees last month's board. Every entry here asks about something a month
    boundary does not change, which is what makes that harmless; an entry that needs this month's
    state does not belong on this hook.

    **Silver is the one exception, and the base check owns it.** The wages come out of the same purse
    later in the same month, so a cost is weighed against what is left once they are paid - see
    [is_possible].

    **A magnitude is a constant, never a roll.** The variety is the pool's job. A rolled magnitude
    would put a branch behind a dice throw - which the coverage gate rightly refuses - and hands a
    float to a positive integer column, where anything under one truncates to nothing.
    """

    # How likely this entry is against its siblings and against QUIET_MONTH_WEIGHT. Priced per entry
    # rather than uniformly: a windfall and a bereavement do not want the same odds
    WEIGHT = 0

    # The months of the year this entry can be drawn in. Empty is every month, which is most of the
    # catalogue. An entry tied to fewer months carries a weight raised to match, so it is drawn as
    # often across a year as it would be across all twelve - see [get_yearly_weight]
    MONTHS: tuple[type[CalendarMonth], ...] = ()

    # The report, and the sentence that undercuts it. "{warrior}" and "{item}" are filled in by an
    # overriding [resolve]
    TITLE = ""
    BODY = ""

    SILVER_CHANGE = 0
    FYRD_CHANGE = 0
    MAX_MORALE_SHARE = 0.0

    # What the player may answer, for an entry that asks rather than tells. Empty for a notice, which
    # is most of the catalogue: a month that asks something every time is a form
    OPTIONS: tuple[IncidentOption, ...] = ()
    # The key of the option an unanswered question takes when the month ends. Not answering is an
    # answer, so ignoring a question never pays better than deciding it
    DEFAULT_OPTION = ""

    @classmethod
    def is_drawn_in(cls, *, calendar_month: type[CalendarMonth]) -> bool:
        """Whether this entry belongs to the pool in "calendar_month" at all."""
        return not cls.MONTHS or calendar_month in cls.MONTHS

    @classmethod
    def get_yearly_weight(cls) -> float:
        """
        The weight this entry carries averaged over a whole year.

        What the pool's balance is measured in: an entry drawn in two months at 18 is drawn as often
        across a year as one drawn in twelve at 3, and the silver, the fyrd and the morale ceiling net
        out over the year rather than inside any one month.
        """
        return cls.WEIGHT * sum(cls.is_drawn_in(calendar_month=calendar_month) for calendar_month in YEAR) / len(YEAR)

    @classmethod
    def is_question(cls) -> bool:
        return bool(cls.OPTIONS)

    @classmethod
    def get_option(cls, *, key: str) -> IncidentOption | None:
        """
        The option this entry declares under "key", or None when it declares nothing by that name.

        The one place a posted key meets the catalogue, so a key naming nothing real is turned away
        here rather than reaching a handler.
        """
        return next((option for option in cls.OPTIONS if option.key == key), None)

    @classmethod
    def get_default_option(cls) -> IncidentOption | None:
        return cls.get_option(key=cls.DEFAULT_OPTION)

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        """
        Whether this entry can happen to this faction at all.

        A cost is only possible when it can be paid, which every entry with a negative
        SILVER_CHANGE inherits from here: #45 made being broke bite, and an incident opening a hole
        the player did not dig takes a decision away from him rather than handing him one.

        **Paid out of what the wages leave.** The salary run bills this same month from the balance
        the month opened with, because no ledger row of the month lands before it - the incident's
        own included. Checked against the raw balance, both bills would pass on their own and
        overdraw together. So the wages are reserved first, through the same [Payroll] the salary run
        bills from, and a cost only asks for silver that is actually free. A month already short on
        wages leaves nothing free, and costly incidents fire less often in lean months. This month's
        building income is not counted: it lands after the wages and funds the month after.

        Everything else can always happen, unless it has something else to take - a reserve to thin,
        a man to name, a piece of gear to lose - and says so by overriding this.
        """
        # A question is priced by its dearest answer, so it is only asked of a player who could give
        # every one of them. Its default never costs silver, which the pool holds it to
        dearest_change = min([cls.SILVER_CHANGE, *[option.silver_change for option in cls.OPTIONS]])
        if dearest_change < 0:
            payroll = Payroll.for_faction(
                faction=faction,
                budget=Transaction.objects.current_balance(faction_id=faction.id),
            )
            return payroll.remaining_amount >= -dearest_change

        return True

    @classmethod
    def resolve(cls, *, faction: Faction) -> IncidentOutcome:
        """
        Turn this entry's constants into the outcome the levers are applied from.
        """
        return IncidentOutcome(
            title=cls.TITLE,
            body=cls.BODY,
            silver_change=cls.SILVER_CHANGE,
            fyrd_change=cls.FYRD_CHANGE,
        )

    @classmethod
    def ask(cls, *, faction: Faction) -> IncidentQuestion:
        """
        Turn a question-shaped entry's constants into what it asks. Override where the question names
        something the faction has - a rival, a piece of gear.
        """
        return IncidentQuestion(title=cls.TITLE, body=cls.BODY)

    @classmethod
    def answer(cls, *, option: IncidentOption, pending_incident: PendingIncident) -> IncidentOutcome:
        """
        Turn the option given into the outcome the levers are applied from.

        Resolved when the answer lands rather than when the question was asked, so a levy is clamped
        to what the reserve holds by then - the same reason FeverInTheVillages clamps its own.
        """
        fyrd_change = option.fyrd_change
        if fyrd_change < 0:
            fyrd_change = -min(-fyrd_change, pending_incident.faction.fyrd_reserve)

        return IncidentOutcome(
            title=option.title,
            body=option.body,
            silver_change=option.silver_change,
            fyrd_change=fyrd_change,
            lost_item=pending_incident.item if option.sells_item else None,
        )


def roster(*, faction: Faction) -> list[Warrior]:
    """
    The men an incident can happen to: the faction's roster, minus the dead.

    The dead stay on it - "Warrior.faction" is not cleared by dying - so they have to be excluded
    here, or a relic is handed to a corpse.
    """
    return list(Warrior.objects.filter_faction(faction_id=faction.id).exclude_dead())


def losable_items(*, faction: Faction) -> list[Item]:
    """
    The gear a moor may swallow: everything the faction has in the field except the finest of each
    function.

    The finest blade and the finest mail are never what goes missing. Losing a rusty spear is an
    anecdote; losing the sword the player saved three months for is arbitrary, and no weight low
    enough makes that read as anything but the game cheating. So a faction needs two weapons or two
    suits of armour in use before anything is losable at all.

    Only worn items, because an item nobody carries is in a chest at home. Priced rather than
    measured by [Item.expectancy_value]: the value of a die roll is a Python property and cannot be
    ordered on, while the price the item was drawn at tracks it closely enough to say which piece is
    the good one.
    """
    worn_items = list(
        Item.objects.filter(owner=faction)
        .exclude(warrior_weapon__isnull=True, warrior_armor__isnull=True)
        .select_related("type")
        .order_by("-price", "id")
    )

    # Dearest first, so the first item of each function is that function's finest and everything
    # behind it is fair game. Ordered by id as well, or two items at one price take turns being
    # the untouchable one
    losable = []
    finest_functions = set()
    for item in worn_items:
        if item.type.function in finest_functions:
            losable.append(item)
        else:
            finest_functions.add(item.type.function)

    return losable
