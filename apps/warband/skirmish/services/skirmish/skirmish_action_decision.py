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

    def _wanted_actions(self) -> list[SkirmishActionChoices]:
        """
        What this man would reach for, most wanted first, before asking whether he may.
        """
        from apps.warband.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator

        wanted = []
        # Warriors will try to save themselves
        if self.warrior.current_health < self.warrior.max_health * 0.25:
            wanted.append(SkirmishActionChoices.DEFENSIVE_STANCE)
        # Strong men batter gates. Ahead of the two below, because a wall left standing shields every
        # defender from every blow, so taking it down is worth more than any single swing at a man
        if self.warrior.effective_strength > MercenaryWarriorGenerator.STATS_MU:
            wanted.append(SkirmishActionChoices.ASSAULT_FORTIFICATION)
        # The effective values in both checks below, so a man stops reaching for the swing his
        # injuries have taken away from him - see docs/patterns/attribute-modifiers.md
        # Warriors with high dexterity will try to hit fast
        if self.warrior.effective_dexterity > MercenaryWarriorGenerator.STATS_MU:
            wanted.append(SkirmishActionChoices.FAST_ATTACK)
        # Warriors with high strength will try to hit hard
        if self.warrior.effective_strength > MercenaryWarriorGenerator.STATS_MU:
            wanted.append(SkirmishActionChoices.RISKY_ATTACK)

        return wanted

    def _determine_decision(self) -> SkirmishActionChoices:
        # Through the same rule the player's select is built from, so a rival never fights with an
        # action his level or his gear has not earned, and the intent shown on his card is the action
        # he fights with. A wish he may not act on falls through to the next one rather than to nothing.
        offered = {action for action, _label in self.warrior.get_skirmish_actions(skirmish=self.skirmish)}

        for action in self._wanted_actions():
            if action in offered:
                return action

        # All others will use the default attack, which every man is always offered
        return SkirmishActionChoices.SIMPLE_ATTACK

    def process(self) -> [int, str]:
        choice = self._determine_decision()

        return choice.value, choice.label
