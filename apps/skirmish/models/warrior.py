from math import isqrt

from django.db import models

from apps.common.domain.dice import DiceNotation
from apps.faction.models.culture import Culture
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.managers.warrior import WarriorManager
from apps.skirmish.services.skirmish.skirmish_action_decision import SkirmishActionDecisionService


# TODO (#95): move to warrior app?
# TODO (#53): permanent injuries would be nice -> each has a modificator and reduces a value like HP or dex
#  -> ankle -> reduce dex, missing finger -> strength etc.
class Warrior(models.Model):
    NO_WEAPON_ATTACK = "1d3"
    NO_ARMOR_DEFENSE = "1d3"

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
    UNPAID_MONTHS_UNTIL_DESERTION = 3

    class ConditionChoices(models.IntegerChoices):
        CONDITION_HEALTHY = 1, "Healthy"
        CONDITION_UNCONSCIOUS = 2, "Unconscious"
        CONDITION_FLEEING = 3, "Fleeing"
        CONDITION_DEAD = 4, "Dead"

    name = models.CharField("Name", max_length=100)
    culture = models.ForeignKey(Culture, verbose_name="Culture", on_delete=models.CASCADE)
    faction = models.ForeignKey(
        "faction.Faction", verbose_name="Faction", null=True, blank=True, on_delete=models.CASCADE
    )
    savegame = models.ForeignKey("savegame.Savegame", verbose_name="Savegame", on_delete=models.CASCADE)

    avatar_id = models.PositiveSmallIntegerField("Avatar-ID", default=1)

    strength = models.PositiveSmallIntegerField("Strength")
    strength_progress = models.PositiveSmallIntegerField("Strength progress", default=0)
    # The mean strength of the population this warrior was drawn from, stamped on him by his generator.
    # It is what his own strength is measured against when he swings: a man at his kind's mean deals his
    # weapon's full damage, one below it less and one above it more. Carried per warrior rather than held
    # as one number for the whole game, because the archetypes do not share a mean - a single pivot would
    # be a standing discount for whichever archetypes sit below it, which is most of them.
    strength_baseline = models.PositiveSmallIntegerField("Strength baseline")

    dexterity = models.PositiveSmallIntegerField("Dexterity")
    dexterity_progress = models.PositiveSmallIntegerField("Dexterity progress", default=0)

    current_health = models.SmallIntegerField("Current health")
    max_health = models.PositiveSmallIntegerField("Maximum health")
    health_progress = models.PositiveSmallIntegerField("Health progress", default=0)

    current_morale = models.SmallIntegerField("Current morale")
    max_morale = models.PositiveSmallIntegerField("Maximum morale")
    morale_progress = models.PositiveSmallIntegerField("Morale progress", default=0)

    experience = models.PositiveIntegerField("Experience", default=0)
    monthly_salary = models.PositiveSmallIntegerField("Monthly salary", default=0)
    # Consecutive months this warrior went without his wages, reset the moment he is paid again.
    # Per warrior rather than per faction because the salary run pays the roster cheapest first and
    # stops when the silver does, so one month leaves some men paid and some not.
    unpaid_months = models.PositiveSmallIntegerField("Unpaid months", default=0)

    recruitment_price = models.PositiveSmallIntegerField("Recruitment price", default=0)

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
        return self.name

    # TODO (#42): add property when a certain value is really high to add a nickname like "Victor the Fast"
    #  (good and bad cases)

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

    def get_skirmish_actions(self) -> list[tuple]:
        # TODO (#52): show only the ones the warrior has depending on his level
        # TODO (#52): use XP to add more skirmish actions -> every level gets a fixed action to keep it simple
        return SkirmishActionChoices.choices

    def decide_skirmish_action(self) -> [int, str]:
        service = SkirmishActionDecisionService(warrior=self)
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

    def roll_attack(self) -> int:
        item = self.get_weapon_or_fallback()
        return DiceNotation(dice_string=item.type.base_value, modifier=item.modifier).result

    def roll_defense(self) -> int:
        item = self.get_armor_or_fallback()
        return DiceNotation(dice_string=item.type.base_value, modifier=item.modifier).result
