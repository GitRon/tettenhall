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
from apps.warband.skirmish.services.skirmish.skirmish_action_decision import SkirmishActionDecisionService
from apps.warband.warrior.choices.nickname import NicknameStateChoices
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
    DEATH_OVERKILL_SHARE = 0.15

    # No injury may take an attribute to nothing. Strength scales a blow by
    # "strength / strength_baseline", so a zero is a man who can never hurt anybody again - a worse
    # outcome than the death he was one point away from, and reachable by no other route. The morale
    # ceiling is floored for the same kind of reason, see "WarriorManager.MINIMUM_MAX_MORALE".
    MINIMUM_EFFECTIVE_ATTRIBUTE = 1

    # Reaching level N costs (N - 1) squared times XP_LEVEL_BASE - 100, 400, 900, 1600 - so every level takes
    # longer than the one before it and a veteran does not run away with it. Quadratic rather than
    # anything steeper because isqrt inverts it in one integer expression: no loop walking the
    # levels, and no float to round the wrong way at a threshold.
    XP_LEVEL_BASE = 100
    # What every level adds to the four attributes and to the salary alike
    LEVEL_UP_GROWTH = 0.1

    # What a month without wages costs, as a share of the warrior's maximum morale, and how many
    # such months in a row he puts up with before walking. Two drops and then he is gone, so the
    # player watches the war band sour for two months before it starts shrinking.
    UNPAID_MORALE_LOSS = 0.25
    UNPAID_MONTHS_UNTIL_WALKOUT = 3

    # What a warrior's monthly wage is worth as a share of what it costs to hire him. One number for
    # both directions: the generators price a wage off a rolled recruitment price, and the pub prices
    # a hire off the wage the man draws today - see [hiring_price].
    SALARY_SHARE_OF_PRICE = 0.5
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

    avatar_id = models.PositiveSmallIntegerField("Avatar-ID", default=1)

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
    # differ in spread by a factor of nearly three, so how far from the mean is far depends on which
    # kind of man was rolled, and the minimum is where the whole of the left tail ends up. Both
    # describe his dexterity as well as his strength, drawn as it is from the same "STATS_SIGMA" and
    # "STATS_MIN" - see "get_nickname".
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

    current_morale = models.SmallIntegerField("Current morale")
    max_morale = models.PositiveSmallIntegerField("Maximum morale")
    morale_progress = models.PositiveSmallIntegerField("Morale progress", default=0)
    morale_baseline = models.PositiveSmallIntegerField("Morale baseline")
    morale_spread = models.PositiveSmallIntegerField("Morale spread")

    experience = models.PositiveIntegerField("Experience", default=0)
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

    weapon = models.OneToOneField(
        Item,
        verbose_name="Weapon",
        related_name="warrior_weapon",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    armor = models.OneToOneField(
        Item,
        verbose_name="Armor",
        related_name="warrior_armor",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
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
        take the default floor of one: their generator re-rolls a zero rather than flooring them, so
        one is as low as they come.

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

    @property
    def effective_strength(self) -> int:
        """
        The strength he actually swings with, his injuries taken off.

        The stored column is left alone on purpose: level-up growth and training both write it, so a
        crippled man who levels would silently un-cripple, and nothing could tell an injury from a bad
        roll at generation. Everything that turns strength into an outcome reads this instead -
        "AttackService._scaled_by_strength", [expected_damage] and the action decision. The epithet
        deliberately does not: see [attribute_draws].
        """
        # Imported here rather than at module scope: the injury row points back at this model, so the
        # warrior topic's model package cannot be reached while this module is still being imported
        from apps.warband.warrior.models.injury_type import InjuryType

        malus = self.injury_maluses.get(InjuryType.AttributeChoices.ATTRIBUTE_STRENGTH, 0)

        return max(self.strength - malus, self.MINIMUM_EFFECTIVE_ATTRIBUTE)

    @property
    def effective_dexterity(self) -> int:
        """
        The dexterity he actually moves with, his injuries taken off.

        A bigger swing than it looks: dexterity decides who attacks whom and which action the AI
        picks, so a lame man is attacked more often as well as hitting less.
        """
        from apps.warband.warrior.models.injury_type import InjuryType

        malus = self.injury_maluses.get(InjuryType.AttributeChoices.ATTRIBUTE_DEXTERITY, 0)

        return max(self.dexterity - malus, self.MINIMUM_EFFECTIVE_ATTRIBUTE)

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
    def display_name(self) -> str:
        """
        The warrior as he is introduced to the player: his name, and the epithet he has earned.

        Kept out of "__str__", which every generated user-facing string flows through - the twelve
        battle-history templates, the monthly player log, the reasons on finance transactions. Those
        are all persisted as frozen strings, and a man who earns his epithet in month twenty would
        otherwise be carrying it in rows written in month three. Whether the battle log adopts the
        epithet is its own call; the pages that present a warrior as a person ask for him by this
        name.
        """
        nickname = self.nickname

        return f"{self.name} {nickname}" if nickname else self.name

    @property
    def avatar_url(self) -> str:
        return f"img/warrior/avatars/avatar_{self.avatar_id}.jpg"

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
    def slavery_selling_price(self) -> int:
        return int(self.recruitment_price / 2)

    @property
    def months_in_pub(self) -> int:
        """
        How long this man has been standing on the pub's shelf, and nothing if he is not on it.

        The month is read off his own savegame rather than handed in, so that the button the player
        clicks, the balance the view checks it against and the row the ledger gets all name one
        number. It is a foreign key read per warrior, on a card that already dereferences his
        culture, his weapon and his armour to render.
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

    def get_skirmish_actions(self, *, skirmish: Skirmish) -> list[tuple]:
        # TODO (#52): show only the ones the warrior has depending on his level
        # TODO (#52): use XP to add more skirmish actions -> every level gets a fixed action to keep it simple
        # The wall is the one action that depends on the fight rather than the man: there has to be one
        # standing, and it has to be in front of him rather than at his back
        return [
            choice
            for choice in SkirmishActionChoices.choices
            if choice[0] != SkirmishActionChoices.ASSAULT_FORTIFICATION or skirmish.can_be_assaulted_by(warrior=self)
        ]

    def decide_skirmish_action(self, *, skirmish: Skirmish) -> [int, str]:
        service = SkirmishActionDecisionService(warrior=self, skirmish=skirmish)
        return service.process()

    def get_weapon_or_fallback(self) -> Item:
        return (
            self.weapon
            if self.weapon
            else Item(
                type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
                owner=self.faction,
            )
        )

    def get_armor_or_fallback(self) -> Item:
        return (
            self.armor
            if self.armor
            else Item(
                type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_ARMOR),
                owner=self.faction,
            )
        )

    @property
    def expected_damage(self) -> float:
        """
        What this man averages with what he is holding, on a plain attack.

        His, not his weapon's: a blow is scaled by "strength / strength_baseline" before it lands
        (`AttackService._scaled_by_strength`), so the same axe is worth a quarter more in the hands of
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
        (`AttackService.get_defense_value`), which is why this and [expected_damage] are not the same
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
