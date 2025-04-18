import typing

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices

if typing.TYPE_CHECKING:
    from apps.skirmish.models import Warrior


class SkirmishActionDecisionService:
    warrior: "Warrior"

    def __init__(self, *, warrior: "Warrior"):
        self.warrior = warrior

    def _determine_decision(self) -> SkirmishActionChoices:
        from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator

        # Warriors will try to save themselves
        if self.warrior.current_health < self.warrior.max_health * 0.25:
            return SkirmishActionChoices.DEFENSIVE_STANCE
        # Warriors with high dexterity will try to hit fast
        if self.warrior.dexterity > MercenaryWarriorGenerator.STATS_MU:
            return SkirmishActionChoices.FAST_ATTACK
        # Warriors with high strength will try to hit hard
        if self.warrior.strength > MercenaryWarriorGenerator.STATS_MU:
            return SkirmishActionChoices.RISKY_ATTACK

        # All others will use the default attack
        return SkirmishActionChoices.SIMPLE_ATTACK

    def process(self) -> [int, str]:
        choice = self._determine_decision()

        return choice.value, choice.label
