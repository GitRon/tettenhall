import random
from dataclasses import dataclass

from apps.warband.faction.models.faction import Faction
from apps.warband.item.services.generators.item.base import BaseItemGenerator
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(frozen=True, kw_only=True)
class QuestOutcome:
    """
    One way an errand can come home, and what it brings with it.

    "title" and "body" are the chronicle line, in the register of the month incidents: a sentence of
    report and one that quietly undercuts it. The levers are constants, the way an incident's are -
    the variety is which outcome is drawn, never how much one of them pays.

    "is_success" decides which side of the draw the sent men's stat moves: good men make the
    successes likelier, and leave every failure exactly as likely as it was written. A lever left at
    its default is a lever this outcome does not pull.
    """

    key: str
    weight: int
    is_success: bool
    title: str
    body: str
    # Paid once per man who came home, so a larger band earns more for the same job
    silver_per_man: int = 0
    # Given to every man who came home
    renown_per_man: int = 0
    # A piece of gear for the stores: the function ("ItemType.FunctionChoices") and how far above the
    # generator's own quality it is drawn. None for an outcome that finds nothing
    item_function: int | None = None
    item_generator_class: type[BaseItemGenerator] | None = None
    item_quality_bonus: int = 0
    # A man who comes home with the band and joins it, drawn by this generator
    warrior_generator_class: type[BaseWarriorGenerator] | None = None


class Quest:
    """
    One errand the world can ask a war band to send men on.

    An entry of the catalogue is a class, in the shape of "apps/warband/incident/incidents/": a
    weight, the two sentences it is offered with, how many men it wants, the attribute it leans on and
    the outcomes it can come home with. Adding one to "apps/warband/quest/quests/__init__.py" is the
    whole of adding a quest.

    **An odd job is the errand that is always on offer.** Every month offers one of them beside the
    rest of the catalogue - harvest work, a merchant's road - so a war band that cannot pay its men
    always has something to send them on. It pays silver, little and reliably, and is never anything
    but safe; the pool's tests hold every odd job to that.
    """

    # How likely this entry is against the other entries on its side of the offer
    WEIGHT = 0

    # Shown on the board while the quest waits for men
    TITLE = ""
    BODY = ""

    # How many men it takes, both inclusive
    MIN_MEN = 1
    MAX_MEN = 1

    # The warrior attribute the sent men are weighed on, summed over the band
    LEANS_ON = "strength"
    # What the band's summed attribute is when the outcomes are as likely as they are written. A band
    # this good draws the written weights; twice as good draws its successes twice as often
    STAT_YARDSTICK = 1
    # The most a band's attribute can multiply the successes by. A cap rather than a curve, so no band
    # is good enough to make failure impossible
    MAX_SUCCESS_FACTOR = 3.0

    IS_ODD_JOB = False

    OUTCOMES: tuple[QuestOutcome, ...] = ()

    # What the chronicle says when the men a quest was sent with are no longer on the roster to come
    # home - every one of them dead, taken or gone
    LAPSED_TITLE = "Nobody came home from the errand."
    LAPSED_BODY = "It is not known whether it was done."

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        """
        Whether this quest can be offered to this faction at all: only when it has the men.

        Counted over the living roster rather than over the men free this month, because the quest is
        offered as the month opens, before anyone has been sent anywhere.
        """
        return Warrior.objects.filter_faction(faction_id=faction.id).exclude_dead().count() >= cls.MIN_MEN

    @classmethod
    def get_success_factor(cls, *, warriors: list[Warrior]) -> float:
        """
        How much likelier the band makes every success, against the weights as written.
        """
        band_stat = sum(getattr(warrior, cls.LEANS_ON) for warrior in warriors)

        return min(cls.MAX_SUCCESS_FACTOR, band_stat / cls.STAT_YARDSTICK)

    @classmethod
    def get_outcome_weights(cls, *, warriors: list[Warrior]) -> list[float]:
        success_factor = cls.get_success_factor(warriors=warriors)

        return [outcome.weight * success_factor if outcome.is_success else outcome.weight for outcome in cls.OUTCOMES]

    @classmethod
    def draw_outcome(cls, *, warriors: list[Warrior]) -> QuestOutcome:
        return random.choices(cls.OUTCOMES, weights=cls.get_outcome_weights(warriors=warriors))[0]
