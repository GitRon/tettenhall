from dataclasses import dataclass

from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models.transaction import Transaction
from apps.warband.item.models.item import Item
from apps.warband.skirmish.models.warrior import Warrior


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

    **A magnitude is a constant, never a roll.** The variety is the pool's job. A rolled magnitude
    would put a branch behind a dice throw - which the coverage gate rightly refuses - and hands a
    float to a positive integer column, where anything under one truncates to nothing.
    """

    # How likely this entry is against its siblings and against QUIET_MONTH_WEIGHT. Priced per entry
    # rather than uniformly: a windfall and a bereavement do not want the same odds
    WEIGHT = 0

    # The report, and the sentence that undercuts it. "{warrior}" and "{item}" are filled in by an
    # overriding [resolve]
    TITLE = ""
    BODY = ""

    SILVER_CHANGE = 0
    FYRD_CHANGE = 0
    MAX_MORALE_SHARE = 0.0

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        """
        Whether this entry can happen to this faction at all.

        A cost is only possible when it can be paid, which every entry with a negative
        SILVER_CHANGE inherits from here: #45 made being broke bite, and an incident opening a hole
        the player did not dig takes a decision away from him rather than handing him one.

        Everything else can always happen, unless it has something else to take - a reserve to thin,
        a man to name, a piece of gear to lose - and says so by overriding this.
        """
        if cls.SILVER_CHANGE < 0:
            return Transaction.objects.current_balance(faction_id=faction.id) >= -cls.SILVER_CHANGE

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
