from django.db import models

from apps.common.domain.dice import DiceNotation
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.managers.skirmish_blow import SkirmishBlowManager
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class SkirmishBlow(models.Model):
    """
    One exchange between two warriors: who swung at whom, with what, and what came of it.

    One row per blow rather than one per warrior per round, because a man can be drawn as the
    defender twice in the same round and a sum of two defence rolls has no ceiling to be measured
    against - and "did he ever roll his weapon's maximum" is answerable per roll and nowhere else.
    Both halves of the exchange sit on the one row: the domain produces exactly one attacker, one
    attack roll and one defence roll per blow, so splitting it in two would split something the fight
    does not.

    The rolls are recorded rather than a verdict about them. What counts as a critical, a miss or a
    blow through full armour is a question asked of these rows afterwards, and can be redefined
    without a migration or a backfill.

    Rows are kept for good, so a permanent perk can ask whether a man has *ever*. The cost is stated
    rather than avoided: they grow per blow per round per skirmish per savegame, with no pruning.
    """

    skirmish = models.ForeignKey(Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE)
    # Carried on the message and written here, never read off the skirmish: by the time the round is
    # over "current_round" names the next one
    round_number = models.PositiveSmallIntegerField("Round")

    attacker = models.ForeignKey(Warrior, verbose_name="Attacker", related_name="blows_dealt", on_delete=models.CASCADE)
    attacker_action = models.PositiveSmallIntegerField("Attacker action", choices=SkirmishActionChoices.choices)
    defender = models.ForeignKey(Warrior, verbose_name="Defender", related_name="blows_taken", on_delete=models.CASCADE)
    defender_action = models.PositiveSmallIntegerField("Defender action", choices=SkirmishActionChoices.choices)

    outcome = models.PositiveSmallIntegerField("Outcome", choices=BlowOutcomeChoices.choices)

    # The weapon's notation and its own modifier, kept as written so "DiceNotation" can be handed them
    # back and asked what the throw could have been. Blank and null together when no die was thrown at
    # all - a defensive stance swings nothing, and a risky attack that goes wide never reaches the dice
    # The kind of weapon that struck, kept as the type rather than the item: an item is deleted when
    # it is destroyed and would take every blow ever struck with it along, while a type is reference
    # data and outlives the sword. It is also the half that a question like "has this man ever felled
    # someone with an axe" is asking, and it is the only thing that tells bare hands apart from a real
    # 1d3 weapon - the fallback types are rows here like any other
    attack_item_type = models.ForeignKey(
        "item.ItemType",
        verbose_name="Weapon type",
        related_name="blows_struck",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    attack_dice = models.CharField("Attack dice", max_length=10, blank=True)
    attack_modifier = models.SmallIntegerField("Attack modifier", null=True, blank=True)
    attack_roll = models.PositiveSmallIntegerField("Attack roll", null=True, blank=True)
    # What the fight actually set against the defence: the roll scaled by the attacker's strength
    # against his kind's mean, and then by whatever his action does to it
    attack_value = models.PositiveSmallIntegerField("Attack value", default=0)

    # A defence is always rolled, even against a blow that never came, so the armour is always known
    defense_item_type = models.ForeignKey(
        "item.ItemType", verbose_name="Armor type", related_name="blows_absorbed", on_delete=models.CASCADE
    )
    defense_dice = models.CharField("Defense dice", max_length=10)
    defense_modifier = models.SmallIntegerField("Defense modifier")
    defense_roll = models.PositiveSmallIntegerField("Defense roll")
    defense_value = models.PositiveSmallIntegerField("Defense value", default=0)

    damage = models.PositiveSmallIntegerField("Damage", default=0)

    objects = SkirmishBlowManager()

    class Meta:
        verbose_name = "Skirmish blow"
        verbose_name_plural = "Skirmish blows"
        default_related_name = "skirmish_blows"
        # The order the blows were struck in, which is the order a round reads in
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.attacker} vs {self.defender}, round {self.round_number} ({self.skirmish})"

    @property
    def attack_notation(self) -> DiceNotation | None:
        """
        The weapon's die as it was written, or nothing when no die was thrown.
        """
        if not self.attack_dice:
            return None

        return DiceNotation(dice_string=self.attack_dice, modifier=self.attack_modifier)

    @property
    def defense_notation(self) -> DiceNotation:
        return DiceNotation(dice_string=self.defense_dice, modifier=self.defense_modifier)

    @property
    def attack_ceiling(self) -> int | None:
        """
        The highest the attack roll could have come to. What a roll is worth is measured against this
        and not against another warrior's roll, so a heavy weapon rolling badly stays a bad roll.
        """
        notation = self.attack_notation

        return notation.best_possible_result if notation else None

    @property
    def defense_ceiling(self) -> int:
        return self.defense_notation.best_possible_result
