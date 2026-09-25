import typing

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices

if typing.TYPE_CHECKING:
    from apps.warband.skirmish.models import Skirmish, Warrior


class SkirmishActionDecisionService:
    warrior: Warrior
    skirmish: Skirmish

    def __init__(self, *, warrior: Warrior, skirmish: Skirmish):
        self.warrior = warrior
        self.skirmish = skirmish

    def _determine_decision(self) -> SkirmishActionChoices:
        from apps.warband.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator

        # Warriors will try to save themselves
        if self.warrior.current_health < self.warrior.max_health * 0.25:
            return SkirmishActionChoices.DEFENSIVE_STANCE
        # Strong men batter gates. Ahead of the two below, because a wall left standing shields every
        # defender from every blow, so taking it down is worth more than any single swing at a man
        if self.warrior.effective_strength > MercenaryWarriorGenerator.STATS_MU and self.skirmish.can_be_assaulted_by(
            warrior=self.warrior
        ):
            return SkirmishActionChoices.ASSAULT_FORTIFICATION
        # The effective values in both checks below, so a man stops reaching for the swing his
        # injuries have taken away from him - see docs/patterns/attribute-modifiers.md
        # Warriors with high dexterity will try to hit fast
        if self.warrior.effective_dexterity > MercenaryWarriorGenerator.STATS_MU:
            return SkirmishActionChoices.FAST_ATTACK
        # Warriors with high strength will try to hit hard
        if self.warrior.effective_strength > MercenaryWarriorGenerator.STATS_MU:
            return SkirmishActionChoices.RISKY_ATTACK

        # All others will use the default attack
        return SkirmishActionChoices.SIMPLE_ATTACK

    def process(self) -> [int, str]:
        choice = self._determine_decision()

        return choice.value, choice.label
