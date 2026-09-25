from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.services.actions.base import AttackService


class AssaultFortificationService(AttackService):
    """
    A man who spends his round on the wall rather than on the man in front of him.

    Inside the pairing he behaves like a man in a defensive stance without the doubled guard: he never
    becomes his pair's attacker and throws nothing at a man, and he defends with his armour as he
    always would. His swing goes to "get_assault_value" instead, which "WarriorAssaultsFortification"
    takes off the wall.
    """

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # His back is to the man he is paired with, so he never wins the initiative over him
        return AttackService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 0

    def get_attack_value(self) -> ActionRoll:
        # Asked only when both men of a pair have no matching points and the tie hands him the attack -
        # he still has nothing to throw at a man
        return ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)

    def get_assault_value(self) -> ActionRoll:
        # The weapon's own throw scaled by strength like every other swing, only aimed at timber
        return self._scaled_by_strength(attack=self.warrior.roll_attack())
