from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.services.actions.base import AttackService


class RallyService(AttackService):
    """
    A leader who spends his round shouting his men back into the line instead of swinging.

    Inside the pairing he is the wall-stormer: never his pair's attacker, nothing thrown, and his armour
    defends him as it always would. What he gives up is his attack, not his safety - a weaker guard would
    make the rally a way to get the leader killed, and the stance's doubled one would make it strictly
    better than the stance. The steadying itself is not a blow and is not answered here: an action
    service returns a roll and cannot emit, so "RallyRemainingWarriors" is raised where the round is
    assembled.
    """

    @staticmethod
    def get_pair_matching_points(*, warrior_dexterity: int) -> int:
        # He is facing his own men, so he never wins the initiative over the man in front of him
        return AttackService.get_pair_matching_points(warrior_dexterity=warrior_dexterity) * 0

    def get_attack_value(self) -> ActionRoll:
        # Asked only when both men of a pair have no matching points and the tie hands him the attack -
        # he still has nothing to throw
        return ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)
