import random

from django.db.models import QuerySet

from apps.common.domain.dice import DiceNotation
from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType


class BaseItemGenerator:
    MODIFIER_ROLLS_MU = 2
    MODIFIER_ROLLS_SIGMA = 2

    # What one point of expected damage costs, and the floor an item is priced against. Expectancy is
    # unbounded below - a modifier floored against a small die can leave a weapon barely able to
    # threaten anybody - and such a thing is worth the floor rather than nothing or a negative sum.
    PRICE_PER_EXPECTED_DAMAGE = 10
    MINIMUM_EXPECTED_DAMAGE = 1

    faction: Faction
    function: int
    savegame_id: int
    quality_bonus: int

    def __init__(
        self, *, faction: Faction | None, item_function: int, savegame_id: int, quality_bonus: int = 0
    ) -> None:
        super().__init__()

        self.faction = faction
        self.function = item_function
        self.savegame_id = savegame_id
        # Added to the modifier roll, so a better forge shifts an item up the condition ladder
        # instead of re-centring it: the condition thresholds stay on the generator's own mean
        self.quality_bonus = quality_bonus

    def _determine_condition(self, *, modifier: int) -> int:
        if modifier < self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_RUSTY
        if self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA <= modifier < self.MODIFIER_ROLLS_MU:
            return Item.ConditionChoices.CONDITION_CHEAP
        if self.MODIFIER_ROLLS_MU <= modifier < self.MODIFIER_ROLLS_MU + self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_TRADITIONAL
        # Everything the checks above didn't claim is above the traditional range
        return Item.ConditionChoices.CONDITION_SUPERIOR

    def _get_queryset_for_type(self) -> QuerySet:
        return ItemType.objects.filter(function=self.function).exclude(is_fallback=True).order_by("?")

    def process(self) -> Item:
        item_type = self._get_queryset_for_type().first()
        if not item_type:
            raise RuntimeError("No item type found.")

        # Modifier can be negative, DiceNotation class takes care of not dealing negative damage
        modifier = round(random.gauss(self.MODIFIER_ROLLS_MU, self.MODIFIER_ROLLS_SIGMA)) + self.quality_bonus

        # Floored against the die it is attached to, which is why the type has to be drawn first. The
        # roll is unbounded below, so a small die could come out with a modifier deeper than its own
        # maximum - a "Rusty Pitchfork (1d4-4)" tops out at nothing and cannot hurt anybody for the
        # whole savegame. A floored item is a better one than the roll asked for, so the condition
        # follows.
        best_possible_roll = DiceNotation(dice_string=item_type.base_value).best_possible_roll
        modifier = max(modifier, 1 - best_possible_roll)

        # Priced by what it does, which is the expected damage: dice and modifier together, and
        # nothing else. The number of dice is what actually decides the damage and it reaches
        # expectancy exactly once, so a formula that multiplies the modifier back in on top hands
        # the price to the modifier alone - and the shop's cheapest weapon is then often its best.
        # A "Superior Pitchfork (1d4+5)" averages 7.5 damage and a "Cheap Long sword (4d4+0)" ten,
        # so the sword is the dearer of the two.
        dice_notation = DiceNotation(dice_string=item_type.base_value, modifier=modifier)
        price = round(
            max(dice_notation.expectancy_value, self.MINIMUM_EXPECTED_DAMAGE) * self.PRICE_PER_EXPECTED_DAMAGE
        )

        # TODO (#102): move in "create_record" method
        return Item.objects.create(
            type=item_type,
            condition=self._determine_condition(modifier=modifier),
            price=price,
            modifier=modifier,
            owner=self.faction,
            savegame_id=self.savegame_id,
        )
