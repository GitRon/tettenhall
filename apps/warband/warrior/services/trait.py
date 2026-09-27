import random
from collections.abc import Callable

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.models.trait_type import TraitType


class InnateTraitDrawService:
    """
    Which traits a man is born with, drawn once by the generator alongside his attribute rolls.

    Most men are nothing in particular. A few are one thing, and a rare man is two - never two of one
    group, since a man is not both bull-necked and slight. Rivals' men, pub mercenaries and leaders are
    drawn the same way, because the generator is shared: a rival's war band fights differently from its
    numbers for the same reason the player's does.

    Returns the types rather than writing them, the way [InjuryRollService] does: the caller owns the
    man and writes what belongs to him.
    """

    # Chances per man, not per trait: at least one innate trait, and two. Balance numbers owned by this
    # mechanic, see docs/patterns/town-buildings.md
    CHANCE_OF_ANY_INNATE = 0.4
    CHANCE_OF_TWO_INNATE = 0.1

    def process(self) -> list[TraitType]:
        roll = random.uniform(0, 1)

        if roll < self.CHANCE_OF_TWO_INNATE:
            count = 2
        elif roll < self.CHANCE_OF_ANY_INNATE:
            count = 1
        else:
            return []

        candidates = list(TraitType.objects.filter(source=TraitType.SourceChoices.SOURCE_INNATE))
        random.shuffle(candidates)

        # One candidate per group - the first the shuffle put forward - so no two drawn can share one
        one_per_group: dict[str, TraitType] = {}
        for trait_type in candidates:
            one_per_group.setdefault(trait_type.group, trait_type)

        return list(one_per_group.values())[:count]


class TraitEarningService:
    """
    Whether the fight just over made this man into something he was not, and if so, what.

    Asked once the skirmish is finished, against the blow rows it left behind, so a trait can never
    change the fight that earned it. Two rules read this skirmish's blows alone, two read every blow
    the man ever struck or took - which is what "SkirmishBlow" being kept for good is for.

    At most one trait per fight. The earned rows are asked in catalogue order and the first whose rule
    holds wins, skipping any whose group the man already has a trait in - a steady man is precisely the
    one a bad fight does not shake - and nothing at all once he carries [MAX_TRAITS].
    """

    # A man is a body type, a temper and a skill at most, never defined by everything at once
    MAX_TRAITS = 3

    # The thresholds, balance numbers owned by this mechanic - see docs/patterns/town-buildings.md
    SHAKEN_HITS_TAKEN = 4
    CHARMED_SWINGS_SURVIVED = 3
    HEADTAKER_CEILING_ROLLS = 5
    SHIELD_WALL_BLOWS_ABSORBED = 10

    warrior: Warrior
    skirmish: Skirmish

    def __init__(self, *, warrior: Warrior, skirmish: Skirmish) -> None:
        self.warrior = warrior
        self.skirmish = skirmish

    def process(self) -> TraitType | None:
        held = list(TraitType.objects.filter(traits__warrior=self.warrior))

        if len(held) >= self.MAX_TRAITS:
            return None

        # Keyed by the catalogue's hook. An earned row without a rule here raises rather than being
        # skipped: a trait nobody can ever earn is a fixture edit that went wrong, not a trait
        rules: dict[str, Callable[[], bool]] = {
            "shaken": self._is_shaken,
            "charmed": self._is_charmed,
            "headtaker": self._is_headtaker,
            "shield-wall-man": self._is_shield_wall_man,
        }

        earnable = TraitType.objects.filter(source=TraitType.SourceChoices.SOURCE_EARNED).exclude(
            group__in={trait_type.group for trait_type in held}
        )

        for trait_type in earnable:
            if rules[trait_type.hook]():
                return trait_type

        return None

    def _is_shaken(self) -> bool:
        """
        Beaten about in one fight often enough to carry it with him.
        """
        hits_taken = self.warrior.blows_taken.filter(
            skirmish=self.skirmish, outcome=BlowOutcomeChoices.OUTCOME_HIT
        ).count()

        return hits_taken >= self.SHAKEN_HITS_TAKEN

    def _is_charmed(self) -> bool:
        """
        Swung at over and over in one fight, and not one blow of it landed.

        A swing is any blow that was thrown at him, whatever came of it. One that was never thrown - a
        man in a defensive stance swings nothing - is not a swing he survived.
        """
        swings = self.warrior.blows_taken.filter(skirmish=self.skirmish).exclude(
            outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN
        )
        outcomes = list(swings.values_list("outcome", flat=True))

        return len(outcomes) >= self.CHARMED_SWINGS_SURVIVED and BlowOutcomeChoices.OUTCOME_HIT not in outcomes

    def _is_headtaker(self) -> bool:
        """
        His weapon's best throw, often enough over his career that it stops looking like luck.

        Counted in Python rather than in the database, because the ceiling is the weapon's notation read
        through "DiceNotation" and has no column to compare against.
        """
        ceiling_rolls = sum(
            1 for blow in self.warrior.blows_dealt.exclude(attack_dice="") if blow.attack_roll == blow.attack_ceiling
        )

        return ceiling_rolls >= self.HEADTAKER_CEILING_ROLLS

    def _is_shield_wall_man(self) -> bool:
        """
        Enough blows taken on his armour over his career that he has learned to take them there.
        """
        absorbed = self.warrior.blows_taken.filter(outcome=BlowOutcomeChoices.OUTCOME_ABSORBED).count()

        return absorbed >= self.SHIELD_WALL_BLOWS_ABSORBED
