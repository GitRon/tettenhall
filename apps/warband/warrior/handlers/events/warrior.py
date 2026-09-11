from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname
from apps.warband.warrior.messages.events.warrior import WarriorMaxMoraleChanged


@message_registry.register_event(event=WarriorMaxMoraleChanged)
def handle_raised_ceiling_earns_a_nickname(*, context: WarriorMaxMoraleChanged) -> Command | None:
    """
    A relic in the hall is the largest single gain in nerve the game hands out, and the third place a
    man can first become worth naming.

    A fifth of his ceiling against a level's tenth and a training course's one point, so it is the
    likeliest of the three to carry somebody across a threshold - which is exactly why it cannot be the
    one that does not count.

    **The guard is the rule, not a formality.** Unlike the other two, this event is raised for a cut as
    well as a gain: the same share the relic adds, the Devil at the ford takes. Going down can put a man
    at the bottom of what his kind rolls, so an unguarded award here would name a frightened man "the
    Craven" - a rename downward, which is the one thing this must never do. Zero is refused with it: a
    cut is truncated against what the man has, so a levy with four morale loses none of it.
    """
    if context.changed_max_morale <= 0:
        return None

    return AwardEarnedNickname(warrior=context.warrior, month=context.month)
