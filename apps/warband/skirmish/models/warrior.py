import typing
from functools import cached_property
from math import isqrt

from django.db import models

from apps.common.domain.dice import DiceNotation
from apps.warband.faction.models.culture import Culture
from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.managers.warrior import WarriorManager
from apps.warband.skirmish.services.actions.requirements import get_offered_actions
from apps.warband.skirmish.services.skirmish.skirmish_action_decision import SkirmishActionDecisionService
from apps.warband.warrior.choices.modified_attribute import ModifiedAttributeChoices
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.choices.portrait_kind import PortraitKindChoices
from apps.warband.warrior.domain.attribute_draw import AttributeDraw
from apps.warband.warrior.services.nickname import resolve_nickname

if typing.TYPE_CHECKING:
    from apps.warband.skirmish.models.skirmish import Skirmish


# TODO (#95): move to warrior app?
class Warrior(models.Model):
    NO_WEAPON_ATTACK = "1d3"
    NO_ARMOR_DEFENSE = "1d3"

    # How far past zero a blow may carry a man and still leave him alive, as a share of what he can
    # hold. Named rather than written at the one comparison that decides dead from unconscious,
    # because the injury roll has to measure its own depth against the very same threshold - see
    # [InjuryRollService].
    DEATH_OVERKILL_SHARE = 0.5

    # No injury or trait may take an attribute to nothing. Strength scales a blow by
    # "strength / strength_baseline", so a zero is a man who can never hurt anybody again - a worse
    # outcome than the death he was one point away from, and reachable by no other route. The morale
    # ceiling is floored for the same kind of reason, see "WarriorManager.MINIMUM_MAX_MORALE".
    MINIMUM_EFFECTIVE_ATTRIBUTE = 1

    # What the man in a faction's seat is called, in front of his name and wherever a page speaks of
    # the seat itself. One word for every faction and every culture.
    LEADER_TITLE = "Ealdorman"

    # Reaching level N costs (N - 1) squared times XP_LEVEL_BASE - 100, 400, 900, 1600 - so every level takes
    # longer than the one before it and a veteran does not run away with it. Quadratic rather than
    # anything steeper because isqrt inverts it in one integer expression: no loop walking the
    # levels, and no float to round the wrong way at a threshold.
    XP_LEVEL_BASE = 100
    # What every level adds to the four attributes and to the salary alike
    LEVEL_UP_GROWTH = 0.1

    # Renown is what a man is known for rather than what he can do, so it is paid by who fell and it
    # fades when he stops fighting - the two things that keep it from being experience under another
    # name. Putting a man down is worth this much per level of the man who fell, and a faction's
    # leader three times that: a levy is 10, a level-3 veteran or a green leader 30.
    RENOWN_PER_LEVEL_OF_THE_FALLEN = 10
    RENOWN_FOR_A_LEADER_MULTIPLIER = 3
    # What a month spent in no fight costs, as a share of the renown he has, and never less than one
    # point, so a small name is forgotten outright rather than lingering at a fraction forever. A
    # quarter is gentle on purpose: a rival's men fight only when the player comes for them.
    RENOWN_IDLE_MONTH_SHARE = 0.25
    # What a man is known for on the day he is generated, as a share of the experience he arrives with.
    # Small on purpose: a veteran from the pub is known a little better than a farmer from the fyrd
    # (about 5 against 1 or 2), and still for less than putting down a single levy is worth.
    RENOWN_ON_ARRIVAL_SHARE_OF_EXPERIENCE = 0.05

    # What a month without wages costs, as a share of the warrior's maximum morale, and how many
    # such months in a row he puts up with before walking. Two drops and then he is gone, so the
    # player watches the war band sour for two months before it starts shrinking.
    UNPAID_MORALE_LOSS = 0.25
    UNPAID_MONTHS_UNTIL_WALKOUT = 3
    # What being taken in a fight costs a man's morale ceiling, as a share of it, once he is turned to
    # the captor's banner
    CAPTIVITY_MORALE_LOSS = 0.25
    # What a captive fetches sold into slavery, as a share of what he would cost to hire
    SLAVERY_PRICE_SHARE = 0.5

    # What a warrior's monthly wage is worth as a share of what it costs to hire him. One number for
    # both directions: the generators price a wage off a rolled recruitment price, and the pub prices
    # a hire off the wage the man draws today - see [hiring_price].
    SALARY_SHARE_OF_PRICE = 0.5
    # The least a man on the payroll draws - see [salary_for].
    MINIMUM_MONTHLY_SALARY = 1
    # Months of wages a warrior is owed for being sent away. The silver insolvency would have taken
    # off the player anyway, which is what makes letting a man go a decision with a price rather than
    # a way to walk out of a wage bill for nothing.
    SEVERANCE_SALARY_MONTHS = 1
    # How long a man may stand in the pub before his price starts climbing, and what every month
    # past it adds - see [hiring_price].
    #
    # The threshold is what the round trip already costs, counted in months of his wage: one month of
    # severance to send him away, and the inverse of SALARY_SHARE_OF_PRICE - two - to take him back.
    # So the wages saved by parking him catch up with the trip exactly on the third month, and every
    # month after that is the one the surcharge exists to price. Derived rather than written down as
    # a three, because a three would go on saying three after either of the numbers under it moved.
    IDLE_MONTHS_BEFORE_SURCHARGE = SEVERANCE_SALARY_MONTHS + round(1 / SALARY_SHARE_OF_PRICE)
    # A month of his wage per month over the threshold, which is what makes the surcharge cancel the
    # saving rather than merely blunt it. Anything less leaves parking profitable at a later month
    # instead of at the fourth, and anything more punishes a dismissal the player regretted.
    IDLE_SURCHARGE_SALARY_MONTHS = 1

    class ConditionChoices(models.IntegerChoices):
        CONDITION_HEALTHY = 1, "Healthy"
        CONDITION_UNCONSCIOUS = 2, "Unconscious"
        CONDITION_FLEEING = 3, "Fleeing"
        CONDITION_DEAD = 4, "Dead"

    name = models.CharField("Name", max_length=100)
    culture = models.ForeignKey(Culture, verbose_name="Culture", on_delete=models.CASCADE)
    faction = models.ForeignKey(
        "warband.Faction", verbose_name="Faction", null=True, blank=True, on_delete=models.CASCADE
    )
    savegame = models.ForeignKey("warband.Savegame", verbose_name="Savegame", on_delete=models.CASCADE)

    # What he looks like, drawn once by his generator and kept, for the reason "nickname_variant" is: a
    # man with one face on the roster and another in the pub is two men to the player. Hair and beard
    # are empty for a bald or clean-shaven man, the face only for a man generated before faces were
    # drawn, who keeps the silhouette - see docs/patterns/portraits.md.
    portrait_face = models.ForeignKey(
        "warband.PortraitPiece",
        verbose_name="Face",
        related_name="warriors_with_face",
        limit_choices_to={"kind": PortraitKindChoices.KIND_FACE},
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    portrait_hair = models.ForeignKey(
        "warband.PortraitPiece",
        verbose_name="Hair",
        related_name="warriors_with_hair",
        limit_choices_to={"kind": PortraitKindChoices.KIND_HAIR},
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    portrait_beard = models.ForeignKey(
        "warband.PortraitPiece",
        verbose_name="Beard",
        related_name="warriors_with_beard",
        limit_choices_to={"kind": PortraitKindChoices.KIND_BEARD},
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    hair_colour = models.ForeignKey(
        "warband.HairColour",
        verbose_name="Hair colour",
        related_name="warriors_with_hair_colour",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    beard_colour = models.ForeignKey(
        "warband.HairColour",
        verbose_name="Beard colour",
        related_name="warriors_with_beard_colour",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    strength = models.PositiveSmallIntegerField("Strength")
    strength_progress = models.PositiveSmallIntegerField("Strength progress", default=0)
    # The mean strength of the population this warrior was drawn from, stamped on him by his generator.
    # It is what his own strength is measured against when he swings: a man at his kind's mean deals his
    # weapon's full damage, one below it less and one above it more. Carried per warrior rather than held
    # as one number for the whole game, because the archetypes do not share a mean - a single pivot would
    # be a standing discount for whichever archetypes sit below it, which is most of them.
    strength_baseline = models.PositiveSmallIntegerField("Strength baseline")
    # The spread of that same population, and the lowest it can roll, stamped on him by the same
    # generator. Together they are what tells an exceptional roll from an ordinary one: the archetypes
    # differ in spread by a factor of two, so how far from the mean is far depends on which kind of man
    # was rolled, and the minimum is as low as a roll can come out. Both describe his dexterity as well
    # as his strength, drawn as it is from the same "STATS_SIGMA" and "STATS_MIN" - see "get_nickname".
    stats_spread = models.PositiveSmallIntegerField("Stats spread")
    stats_minimum = models.PositiveSmallIntegerField("Stats minimum")
    # What this man is named for, and which of the several wordings phrases it. Both are drawn once
    # and kept: an epithet is a fact about who he was, so nothing that moves an attribute afterwards -
    # a level, a training course, a prisoner's oath, a bad night at the ford - may rename him. Null
    # for an ordinary man, and null is the only state the ratchet may fill: see
    # [handle_award_earned_nickname].
    #
    # The state rather than the resolved string, so the wording lists stay editable and reach men
    # already made. The variant is on the row rather than derived from his id, because the wording has
    # to hold still as well: a man called "the Bear" on the roster and "the Ox" in the pub is two men
    # to the player.
    nickname_state = models.PositiveSmallIntegerField(
        "Nickname state", choices=NicknameStateChoices.choices, null=True, blank=True, default=None
    )
    nickname_variant = models.PositiveSmallIntegerField("Nickname variant", default=0)

    dexterity = models.PositiveSmallIntegerField("Dexterity")
    dexterity_progress = models.PositiveSmallIntegerField("Dexterity progress", default=0)

    current_health = models.SmallIntegerField("Current health")
    max_health = models.PositiveSmallIntegerField("Maximum health")
    health_progress = models.PositiveSmallIntegerField("Health progress", default=0)
    # The mean and the spread of the health this warrior's kind is rolled with, its own pair because
    # the archetypes' health means and spreads stand in no fixed ratio to their stats ones - see
    # "get_nickname"
    health_baseline = models.PositiveSmallIntegerField("Health baseline")
    health_spread = models.PositiveSmallIntegerField("Health spread")
    # The month the player last paid his sanctuary to tend this man. Months count from 1, so 0 is
    # "never tended" - the reading "Town.last_feast_at" gives its own zero. Once a month is enough:
    # he fights once a month, so a second treatment could buy nothing.
    last_tended_at = models.PositiveSmallIntegerField(
        "Last tended at", help_text="Month his wounds were last tended for silver, 0 if never", default=0
    )

    current_morale = models.SmallIntegerField("Current morale")
    max_morale = models.PositiveSmallIntegerField("Maximum morale")
    # The highest ceiling this man has ever held. Every raise that takes "max_morale" above it moves
    # it along - a level, a training course, a relic - while a cut leaves it standing, so the gap
    # between the two is exactly what he has lost. A feast mends toward it and never past it, which
    # is what keeps the feast a repair rather than a way to buy nerve.
    peak_max_morale = models.PositiveSmallIntegerField("Highest maximum morale")
    morale_progress = models.PositiveSmallIntegerField("Morale progress", default=0)
    morale_baseline = models.PositiveSmallIntegerField("Morale baseline")
    morale_spread = models.PositiveSmallIntegerField("Morale spread")

    experience = models.PositiveIntegerField("Experience", default=0)
    renown = models.PositiveIntegerField("Renown", default=0)
    monthly_salary = models.PositiveSmallIntegerField("Monthly salary", default=0)
    # Consecutive months this warrior went without his wages, reset the moment he is paid again.
    # Per warrior rather than per faction because the salary run pays the roster cheapest first and
    # stops when the silver does, so one month leaves some men paid and some not.
    unpaid_months = models.PositiveSmallIntegerField("Unpaid months", default=0)

    recruitment_price = models.PositiveSmallIntegerField("Recruitment price", default=0)

    # Whether this man is stock a pub generated and may sweep out again at the next restock.
    # "handle_restock_pub_mercenaries" clears the shelf with a row delete, and a warrior who left a
    # roster waits on that same shelf - so what may be destroyed has to be stated on the row rather
    # than read off an empty faction, which describes a dismissed veteran just as well as a mercenary
    # nobody hired. Written where the pub takes a man in, by "handle_add_warrior_to_pub" and nowhere
    # else, so a man hired out of the pub and later sent away is marked afresh on the way back in.
    is_pub_stock = models.BooleanField("Is pub stock", default=False)

    # The month this man went onto the pub's shelf, and null whenever he is not standing on it. What
    # reads it is [hiring_price]: a veteran parked there draws no wages, so without a date nothing
    # can tell a man sent away last month from one sent away last year, and the second is the one
    # who was being kept off the payroll. Written by "handle_add_warrior_to_pub" and cleared by
    # "handle_recruit_pub_mercenary", which are the one way in and the one way out.
    pub_arrival_month = models.PositiveSmallIntegerField("Pub arrival month", null=True, blank=True)

    last_used_skirmish_action = models.PositiveSmallIntegerField(
        choices=SkirmishActionChoices.choices, blank=True, null=True
    )

    condition = models.PositiveSmallIntegerField(
        "Condition",
        choices=ConditionChoices.choices,
        default=ConditionChoices.CONDITION_HEALTHY,
    )

    # A deleted item leaves the man empty-handed rather than taking him with it
    weapon = models.OneToOneField(
        Item,
        verbose_name="Weapon",
        related_name="warrior_weapon",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    armor = models.OneToOneField(
        Item,
        verbose_name="Armor",
        related_name="warrior_armor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = WarriorManager()

    class Meta:
        verbose_name = "Warrior"
        verbose_name_plural = "Warriors"
        default_related_name = "warriors"

    def __str__(self) -> str:
        """
        The bare name, deliberately without the epithet - see [display_name].
        """
        return self.name

    @property
    def attribute_draws(self) -> dict[str, AttributeDraw]:
        """
        The four attributes beside the distributions they were drawn from, which is the only form
        anything can ask whether one of them is exceptional in - see [AttributeDraw].

        Strength and dexterity share a baseline, a spread and a floor, all three being drawn from the
        one "STATS_MU"/"STATS_SIGMA"/"STATS_MIN" trio. Health and morale each have their own pair, and
        take the default minimum of one: their generator re-rolls a zero, so one is as low as they
        come.

        The stored columns, never [effective_strength] and [effective_dexterity]. This feeds the
        epithet, which is drawn once and kept - a man called "the Strong" who loses a shoulder is
        still called "the Strong", the way a level that raises his strength does not rename him
        either.
        """
        return {
            "strength": AttributeDraw(
                value=self.strength,
                baseline=self.strength_baseline,
                spread=self.stats_spread,
                minimum=self.stats_minimum,
            ),
            "dexterity": AttributeDraw(
                value=self.dexterity,
                baseline=self.strength_baseline,
                spread=self.stats_spread,
                minimum=self.stats_minimum,
            ),
            "health": AttributeDraw(value=self.max_health, baseline=self.health_baseline, spread=self.health_spread),
            "morale": AttributeDraw(value=self.max_morale, baseline=self.morale_baseline, spread=self.morale_spread),
        }

    @cached_property
    def injury_maluses(self) -> dict[str, int]:
        """
        What this man's lasting injuries take off each attribute, summed per attribute.

        One query for both, and cached on the instance: the fight asks for a warrior's strength once
        per blow he throws, and a roster page asks every man on it. An injury is inflicted on a man
        who is already out of the fight and is never healed away, so there is nothing that can change
        under a cached value while anything is still reading it.

        Zero is absent from the result rather than present as a zero, so a man with no injuries
        aggregates to an empty dict and the two readers below fall back through "get".
        """
        return {
            row["type__attribute"]: row["total"]
            for row in self.injuries.values("type__attribute").annotate(total=models.Sum("type__magnitude"))
        }

    @cached_property
    def trait_modifiers(self) -> dict[str, int]:
        """
        What this man's traits add to or take off each attribute, summed per attribute and signed.

        The same shape and the same caching as [injury_maluses], and for the same reason: a trait is
        granted after the fight that earned it is over, so nothing changes under a cached value while
        anything is still reading it. Signed where an injury is not, because a trait can be a virtue.

        A man whose traits cancel out on an attribute aggregates to a zero rather than an absent key,
        which reads the same through "get".
        """
        return {
            row["type__attribute"]: row["total"]
            for row in self.traits.values("type__attribute").annotate(total=models.Sum("type__magnitude"))
        }

    def _effective_attribute(self, *, stored: int, attribute: str) -> int:
        """
        A stored attribute as it reaches the field: the injuries taken off, the traits applied.

        The sources simply sum, and the floor sits on the result rather than on any one of them - a
        slight man with a ruined shoulder is floored once, not twice.
        """
        modifier = self.trait_modifiers.get(attribute, 0) - self.injury_maluses.get(attribute, 0)

        return max(stored + modifier, self.MINIMUM_EFFECTIVE_ATTRIBUTE)

    @property
    def effective_strength(self) -> int:
        """
        The strength he actually swings with, his injuries and his traits applied.

        The stored column is left alone on purpose: level-up growth and training both write it, so a
        crippled man who levels would silently un-cripple, and nothing could tell an injury or a trait
        from a roll at generation. Everything that turns strength into an outcome reads this instead -
        "AttackService._scaled_by_strength", [expected_damage] and the action decision. The epithet
        deliberately does not: see [attribute_draws].
        """
        return self._effective_attribute(stored=self.strength, attribute=ModifiedAttributeChoices.ATTRIBUTE_STRENGTH)

    @property
    def effective_dexterity(self) -> int:
        """
        The dexterity he actually moves with, his injuries and his traits applied.

        A bigger swing than it looks: dexterity decides who attacks whom and which action the AI
        picks, so a lame man is attacked more often as well as hitting less.
        """
        return self._effective_attribute(stored=self.dexterity, attribute=ModifiedAttributeChoices.ATTRIBUTE_DEXTERITY)

    @property
    def nickname(self) -> str | None:
        """
        The epithet this man carries, phrased his way.

        Read off the row rather than measured off the attributes, which is what makes it a name: the
        columns it was drawn from go on moving for the rest of his life and it does not.
        """
        if self.nickname_state is None:
            return None

        return resolve_nickname(state=self.nickname_state, variant=self.nickname_variant)

    @property
    def is_leader(self) -> bool:
        """
        Whether this man holds his faction's seat today.

        Asked of his own faction, so a captive - whose faction capture has cleared - holds no seat even
        while his old faction's "leader" still points at him. A defeated faction is the same: its row
        keeps naming the man it lost, and he leads nothing any more.

        Reads "faction", so a list that names its men by [display_name] brings the faction along with
        them rather than paying a query per man.
        """
        faction = self.faction
        # Asked of the seat rather than of the man, so an empty seat is nobody's - not the one of an
        # unsaved man whose id is just as empty
        if faction is None or faction.leader_id is None:
            return False

        return faction.leader_id == self.id and not faction.is_defeated

    @property
    def display_name(self) -> str:
        """
        The warrior as he is introduced to the player: the title of the seat he holds, his name, and
        the epithet he has earned - "Ealdorman Uthred the Strong", "Wulf the Strong".

        Kept out of "__str__", which every generated user-facing string flows through - the twelve
        battle-history templates, the monthly player log, the reasons on finance transactions. Those
        are all persisted as frozen strings, and a man who earns his epithet in month twenty, or takes
        the seat in month thirty, would otherwise be carrying it in rows written in month three.
        Whether the battle log adopts the full name is its own call; the pages that present a warrior
        as a person ask for him by this name.
        """
        name = f"{self.LEADER_TITLE} {self.name}" if self.is_leader else self.name
        nickname = self.nickname

        return f"{name} {nickname}" if nickname else name

    @property
    def is_dead(self) -> bool:
        return self.condition == self.ConditionChoices.CONDITION_DEAD

    @property
    def is_unconscious(self) -> bool:
        return self.condition == self.ConditionChoices.CONDITION_UNCONSCIOUS

    @property
    def is_fleeing(self) -> bool:
        return self.condition == self.ConditionChoices.CONDITION_FLEEING

    @property
    def is_healthy(self) -> bool:
        return self.condition == self.ConditionChoices.CONDITION_HEALTHY

    @property
    def has_lost_max_morale(self) -> bool:
        # His ceiling sits below the highest he has held: the scar the card shows and a feast mends
        return self.max_morale < self.peak_max_morale

    @property
    def is_mended_by_a_feast(self) -> bool:
        """
        Whether sitting this man down at a feast gives him any nerve back.

        Only a man carrying a cut has anything to mend, and an unpaid one is fed but not lifted: being
        broke has to cost something, and a feast would otherwise buy that cost straight back - the same
        guard the monthly morale refill keeps. One rule for the reaction that mends and the log line
        that counts, so the two cannot come to disagree about who was helped.
        """
        return self.has_lost_max_morale and self.unpaid_months == 0

    @property
    def slavery_selling_price(self) -> int:
        return int(self.recruitment_price * self.SLAVERY_PRICE_SHARE)

    @property
    def months_in_pub(self) -> int:
        """
        How long this man has been standing on the pub's shelf, and nothing if he is not on it.

        The month is read off his own savegame rather than handed in, so that the button the player
        clicks, the balance the view checks it against and the row the ledger gets all name one
        number. That makes it a foreign key read per warrior, which is why the pub's list brings the
        savegame along with the men - see [Faction.get_pub_stock].
        """
        if self.pub_arrival_month is None:
            return 0

        return self.savegame.current_month - self.pub_arrival_month

    @property
    def idle_surcharge(self) -> int:
        """
        What a man adds to his price for having been left to wait.

        A veteran parked in the pub draws no wages, so the months he spends there are months his old
        faction did not pay for. Without this the round trip - severance, then the hiring price -
        costs three months of his wage whatever happens, while the wages dodged go on mounting, and
        a man is cheaper on the shelf than on the roster from the fourth month onward. Charging the
        wage back from the threshold on is what makes the shelf cost what the roster costs, so
        parking is never a saving and a dismissal the player regrets inside the quarter is never a
        punishment.

        It applies to the generated mercenary too, and comes to nothing for him on its own: the
        restock empties and refills its shelf every month, so his stay is always the month he was
        rolled in.
        """
        idle_months = max(0, self.months_in_pub - self.IDLE_MONTHS_BEFORE_SURCHARGE)

        return self.monthly_salary * self.IDLE_SURCHARGE_SALARY_MONTHS * idle_months

    @property
    def hiring_price(self) -> int:
        """
        What it costs to take this man onto a roster today.

        Read off the wage he draws rather than off "recruitment_price", which was rolled when he was
        generated and describes the levy he was: every level raises his salary, so a veteran who has
        been through a war and come back out of it would otherwise be the cheapest strong man in the
        game. Inverting the share the generators price a wage with is what keeps a mercenary nobody
        has hired at the price he has always had, while a man who earned his levels costs what he
        now costs to keep.

        What the wait adds on top is [idle_surcharge]. A man who draws no wage is free either way,
        which is what keeps a leader out of both halves of this.
        """
        return round(self.monthly_salary / self.SALARY_SHARE_OF_PRICE) + self.idle_surcharge

    @property
    def severance_pay(self) -> int:
        """
        What the faction owes a man it sends away.
        """
        return self.monthly_salary * self.SEVERANCE_SALARY_MONTHS

    @property
    def wage_once_recruited(self) -> int:
        """
        What a captive draws once he is taken on: his own wage, or, for a man who draws none - a leader -
        the wage the recruitment puts him on (see "handle_recruit_captured_warrior").
        """
        return self.monthly_salary or self.salary_for(recruitment_price=self.recruitment_price)

    @staticmethod
    def salary_for(*, recruitment_price: int) -> int:
        """
        The monthly wage a man rolled at a given price draws, for every archetype that draws one.

        Never below MINIMUM_MONTHLY_SALARY: the share of a price of one or two rounds to nothing, and
        a man on nothing is off the payroll in all but name - no wage bill, no walk-out, and free to
        hire, since [hiring_price] inverts the wage.
        """
        return max(round(recruitment_price * Warrior.SALARY_SHARE_OF_PRICE), Warrior.MINIMUM_MONTHLY_SALARY)

    @staticmethod
    def level_for(*, experience: int) -> int:
        """
        The level a given amount of experience buys, as a staticmethod so a handler can ask for the
        level of a number rather than of an instance.

        Derived rather than stored: a column would need a backfill for every warrior generated with
        experience already, and would then be free to drift out of step with the experience it is
        supposed to describe.
        """
        return isqrt(experience // Warrior.XP_LEVEL_BASE) + 1

    @property
    def level(self) -> int:
        return self.level_for(experience=self.experience)

    @property
    def experience_for_next_level(self) -> int:
        """
        The threshold the next level sits behind, so a level can be shown as progress towards
        something rather than as a number that appears from nowhere on a battlefield.
        """
        return self.level**2 * self.XP_LEVEL_BASE

    @staticmethod
    def renown_for_taking_down(*, level: int, is_leader: bool) -> int:
        """
        What putting down a man of "level" is worth, three times over if he leads a faction.
        """
        renown = level * Warrior.RENOWN_PER_LEVEL_OF_THE_FALLEN

        if is_leader:
            renown *= Warrior.RENOWN_FOR_A_LEADER_MULTIPLIER

        return renown

    @staticmethod
    def renown_on_arrival(*, experience: int) -> int:
        """
        What a newly generated man is already known for, read off the experience he arrives with.
        """
        return int(experience * Warrior.RENOWN_ON_ARRIVAL_SHARE_OF_EXPERIENCE)

    @property
    def renown_lost_to_an_idle_month(self) -> int:
        """
        What a month in no fight takes off him: a share of what he has, at least one point, never more
        than he has.
        """
        return min(self.renown, max(1, int(self.renown * self.RENOWN_IDLE_MONTH_SHARE)))

    def get_skirmish_actions(self, *, skirmish: Skirmish) -> list[tuple]:
        return get_offered_actions(warrior=self, skirmish=skirmish)

    def decide_skirmish_action(self, *, skirmish: Skirmish) -> [int, str]:
        service = SkirmishActionDecisionService(warrior=self, skirmish=skirmish)
        return service.process()

    @cached_property
    def _fallback_item_types(self) -> dict[int, ItemType]:
        """
        What an empty slot fights with, keyed by the function of the slot.

        One query for both, and cached on the instance: a card asks for each slot twice - its icon and
        its name - and the fight asks once per blow. The fallbacks are reference data nothing in play
        ever changes, so there is nothing that can move under a cached value.
        """
        return {item_type.function: item_type for item_type in ItemType.objects.filter(is_fallback=True)}

    def _get_gear_or_fallback(self, *, item: Item | None, function: int) -> Item:
        """
        The item in a slot, or the fallback for its function when the slot is empty.

        Built unsaved and owned by his faction, so a bare-handed man reads like any other one holding
        something: the fallback has a type, dice and an owner, and no row.
        """
        if item is not None:
            return item

        return Item(type=self._fallback_item_types[function], owner=self.faction)

    def get_weapon_or_fallback(self) -> Item:
        return self._get_gear_or_fallback(item=self.weapon, function=ItemType.FunctionChoices.FUNCTION_WEAPON)

    def get_armor_or_fallback(self) -> Item:
        return self._get_gear_or_fallback(item=self.armor, function=ItemType.FunctionChoices.FUNCTION_ARMOR)

    @property
    def expected_damage(self) -> float:
        """
        What this man averages with what he is holding, on a plain attack.

        His, not his weapon's: a blow is scaled by "strength / strength_baseline" before it lands
        (`SkirmishActionService._scaled_by_strength`), so the same axe is worth a quarter more in the hands of
        a man a quarter above his kind's mean. The plain attack is the baseline the two other swings
        are quoted against - the fast one halves this and the risky one doubles it, half the time.

        Read off the fallback when the slot is empty, the way the fight reads it: a bare-handed
        warrior still throws 1d3, and a blank here would say he cannot hurt anybody.

        The effective strength, because this is what the gear picker quotes a man's swing at and the
        fight would otherwise disagree with it about a man with a ruined shoulder.
        """
        return self.get_weapon_or_fallback().expectancy_value * self.effective_strength / self.strength_baseline

    @property
    def expected_protection(self) -> float:
        """
        What his armour turns aside on average - the item's own figure and nothing else.

        No strength in it, and so no baseline either: defence is the armour's own roll
        (`SkirmishActionService.get_defense_value`), which is why this and [expected_damage] are not the same
        calculation with a different item in it.
        """
        return self.get_armor_or_fallback().expectancy_value

    def roll_attack(self) -> ActionRoll:
        """
        The weapon's own throw, the die behind it and the gear that threw it - before the fight
        scales any of it.

        What the fight does with the number - scaling it by strength, then doubling or halving it for
        the action - leaves nothing of the die in it, so the die has to travel alongside if a record
        of the blow is ever to say what the man could have rolled. "value" is the bare roll here; the
        action service replaces it with what the fight actually compares.
        """
        return self._roll_gear(item=self.get_weapon_or_fallback())

    def roll_defense(self) -> ActionRoll:
        return self._roll_gear(item=self.get_armor_or_fallback())

    @staticmethod
    def _roll_gear(*, item: Item) -> ActionRoll:
        roll = DiceNotation(dice_string=item.type.base_value, modifier=item.modifier).roll()

        return ActionRoll(roll=roll, item_type=item.type, value=roll.result)
