from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.warrior.choices.warrior_milestone import JoinedWayChoices, MilestoneKindChoices
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname, RecordWarriorMilestone
from apps.warband.warrior.messages.events.warrior import (
    NewLeaderWarriorCreated,
    WarriorEarnedNickname,
    WarriorGainedTrait,
    WarriorMaxMoraleChanged,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


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


@message_registry.register_event(event=NewLeaderWarriorCreated)
def handle_record_a_founding_leader(*, context: NewLeaderWarriorCreated) -> Command:
    """
    The man a faction is founded around has led it from its first day, which is how he joined it.
    """
    return RecordWarriorMilestone(
        warrior=context.warrior,
        faction=context.faction,
        kind=MilestoneKindChoices.JOINED,
        month=context.month,
        joined_way=JoinedWayChoices.FOUNDED,
    )


@message_registry.register_event(event=WarriorEarnedNickname)
def handle_record_a_naming(*, context: WarriorEarnedNickname) -> Command:
    """
    The epithet on his card says what he is called; this keeps when he came to be called it, and for
    which deed, which the card cannot - a second deed would overwrite the first, and the month log that
    announced it is cleared at the turn of the month.
    """
    return RecordWarriorMilestone(
        warrior=context.warrior,
        faction=context.faction,
        kind=MilestoneKindChoices.NAMED,
        month=context.month,
        skirmish=context.skirmish,
        other_warrior=context.fallen_warrior,
        nickname_state=context.nickname_state,
    )


@message_registry.register_event(event=WarriorGainedTrait)
def handle_record_a_change_in_a_man(*, context: WarriorGainedTrait) -> Command:
    """
    The fight made something of him. Which trait it was stays off the record's face while traits are
    hidden - see [MilestoneKindChoices.CHANGED] - and who may read even that much is the story's
    question, see "WarriorStory".
    """
    return RecordWarriorMilestone(
        warrior=context.warrior,
        faction=context.faction,
        kind=MilestoneKindChoices.CHANGED,
        month=context.month,
        skirmish=context.skirmish,
    )


@message_registry.register_event(event=WarriorWasDismissed)
def handle_record_a_man_sent_away(*, context: WarriorWasDismissed) -> Command:
    """
    The player sent him away. Without this his story jumps from one roster to the next with nothing
    in between, and the pub card says nothing of why he is standing there.
    """
    return RecordWarriorMilestone(
        warrior=context.warrior, faction=context.faction, kind=MilestoneKindChoices.DISMISSED, month=context.month
    )


@message_registry.register_event(event=WarriorWalkedOutOverUnpaidSalary)
def handle_record_a_man_who_walked_out(*, context: WarriorWalkedOutOverUnpaidSalary) -> Command:
    """
    He took himself off a roster that stopped paying him, which is a thing a future master would want to
    know about him.
    """
    return RecordWarriorMilestone(
        warrior=context.warrior, faction=context.faction, kind=MilestoneKindChoices.WALKED_OUT, month=context.month
    )
