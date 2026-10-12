from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.messages.events.skirmish import FortificationFell, SkirmishFinished
from apps.warband.skirmish.messages.events.warrior import (
    WarriorImprovedStats,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.messages.commands.warrior import (
    AwardDeedNickname,
    AwardEarnedNickname,
    EarnDeedsInSkirmish,
    EarnTraitsInSkirmish,
    InflictInjury,
)
from apps.warband.warrior.services.nickname import is_a_giant_felled


@message_registry.register_event(event=WarriorImprovedStats)
def handle_level_up_earns_a_nickname(*, context: WarriorImprovedStats) -> Command:
    """
    A level raises all four attributes at once, which is the other place a man can first become worth
    naming.

    The month comes off the fight rather than off the message: nothing in a level-up chain carries one,
    and the skirmish it happened in already knows which month it belongs to. Reading it is an attribute
    access on an instance the event carries, not a query.
    """
    return AwardEarnedNickname(warrior=context.warrior, month=context.skirmish.month)


@message_registry.register_event(event=WarriorWasKilled)
def handle_a_killing_blow_may_name_the_killer(*, context: WarriorWasKilled) -> Command | None:
    """
    The man whose blow killed a faction's leader, or a man far above him, is named for it.

    One handler deciding between the two rather than one each, because a single blow can be both, and
    two awards queued for it would be settled by the order the handlers happen to be registered in. The
    leader goes first: the rarer deed, and the one the war band talks about.

    Killed, not felled, for the leader: a leader beaten senseless is led away or carried home, and the
    name is for the blow that ended him. Read off the flag the blow was struck with, because by the time
    anything reacts his faction may already have seated a successor - see [WarriorWasKilled]. A giant
    felled counts either way - see [handle_felling_a_giant_earns_a_nickname].

    Any man's blow, on either side of any fight, the way an attribute epithet is any man's: a rival's
    man who did it is named on his own roster, and the player meets him that way.
    """
    if context.fell_as_a_leader:
        nickname_state = NicknameStateChoices.LORD_SLAYER
    elif is_a_giant_felled(fallen_level=context.warrior.level, striker_level=context.by_warrior.level):
        nickname_state = NicknameStateChoices.GIANTBANE
    else:
        return None

    return AwardDeedNickname(warrior=context.by_warrior, nickname_state=nickname_state, month=context.skirmish.month)


@message_registry.register_event(event=WarriorWasIncapacitated)
def handle_felling_a_giant_earns_a_nickname(*, context: WarriorWasIncapacitated) -> Command | None:
    """
    The man who beat senseless somebody far above him is named for it.

    Felled is enough here, where the leader's deed wants him dead: what is remarkable is the gap between
    the two men, and it was closed whether the giant wakes up or not. Levels are read off the experience
    on the two instances the event carries, so this asks nothing of the database.
    """
    if not is_a_giant_felled(fallen_level=context.warrior.level, striker_level=context.by_warrior.level):
        return None

    return AwardDeedNickname(
        warrior=context.by_warrior,
        nickname_state=NicknameStateChoices.GIANTBANE,
        month=context.skirmish.month,
    )


@message_registry.register_event(event=FortificationFell)
def handle_bringing_down_the_walls_earns_a_nickname(*, context: FortificationFell) -> Command:
    """
    The man whose swing took the last of the walls is named for it.

    Raised once per fall, to the swing that finished it, so there is one man to name and the event
    already carries him.
    """
    return AwardDeedNickname(
        warrior=context.warrior,
        nickname_state=NicknameStateChoices.WALLBREAKER,
        month=context.skirmish.month,
    )


@message_registry.register_event(event=WarriorWasIncapacitated)
def handle_beating_may_leave_a_mark(*, context: WarriorWasIncapacitated) -> Command:
    """
    A man beaten senseless is the one moment the game can ask whether he keeps anything.

    Read at the end of the blow rather than off the blow record, because the fight has already decided
    what going down means and a second threshold would be a competing definition of it.

    A plain relay, carrying nothing it has to look up. The month comes off the fight the way the
    nickname handler above takes it - an attribute access on an instance the event carries. His
    faction pointedly does not: "reduce_current_health" refreshes the warrior from the database one
    handler earlier, which drops every cached relation on him, so "warrior.faction" here is a query
    in the one place strict mode forbids one. The command's handler reads it instead.
    """
    return InflictInjury(
        skirmish=context.skirmish,
        warrior=context.warrior,
        overkill_health=context.overkill_health,
        month=context.skirmish.month,
    )


@message_registry.register_event(event=SkirmishFinished)
def handle_fight_may_change_a_man(*, context: SkirmishFinished) -> Command:
    """
    A fight over is the one moment the game can ask what it made of the men who fought it.

    A plain relay, and one per fight: which men count is the command handler's to read, see
    [EarnTraitsInSkirmish].
    """
    return EarnTraitsInSkirmish(skirmish=context.skirmish, month=context.month)


@message_registry.register_event(event=SkirmishFinished)
def handle_fight_may_name_a_man(*, context: SkirmishFinished) -> Command:
    """
    A fight over is the moment to ask whether it made anybody a name: the last man standing, and the
    man who has now come home from enough of them.

    A plain relay, and one per fight: who stood on which side, who is still alive and how many fights
    each man has seen are rows - see [EarnDeedsInSkirmish].
    """
    return EarnDeedsInSkirmish(skirmish=context.skirmish, month=context.month)
