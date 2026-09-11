from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.training.messages.events.training import WarriorUpgradedSkill
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname


@message_registry.register_event(event=WarriorUpgradedSkill)
def handle_training_earns_a_nickname(*, context: WarriorUpgradedSkill) -> Command:
    """
    A filled progress bar is one of the two things in the game that raise an attribute, so it is one
    of the two places a man can first become worth naming.

    Asked on every upgrade rather than only on the ones that could matter, because which ones could is
    exactly the rule the command owns - see [handle_award_earned_nickname].
    """
    return AwardEarnedNickname(warrior=context.warrior, month=context.month)
