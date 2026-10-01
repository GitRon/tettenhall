"""
The fight told as a story: the sentences of the Saga tab.

The Tally beside it is the audit trail - every roll, every point of damage, every point of morale. The
saga says what a watcher would have seen, and nothing a watcher could not: no numbers, and none of the
bookkeeping the report box already lists once the fight is decided.

Every phrasing comes in several variants and one is drawn when the line is written. The sentence is
stored, so the draw happens once and a round never rewords itself on the next render.
"""

import random

from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.services.skirmish.damage import SkirmishDamageService

# How much of the defender's health a blow took, as a share of his maximum, below which it reads as a
# graze or as a solid hit. Anything above is a blow that nearly ends him. Measured against his maximum
# rather than against what he had left, so the same blow reads the same on a fresh man and a bloodied
# one - how close he is to going down is what the casualty line is for.
GRAZE_SHARE = 0.15
SOLID_SHARE = 0.35

# How the attacker comes in. Only the three actions that throw something can be the approach of a blow
# that was thrown; the others strike nothing and are told whole, see "NOT_THROWN".
APPROACH = {
    SkirmishActionChoices.SIMPLE_ATTACK: (
        "{attacker} cuts at {defender}",
        "{attacker} steps in and swings at {defender}",
        "{attacker} brings his blade down at {defender}",
        "{attacker} hews at {defender}",
        "{attacker} comes on at {defender} with a level stroke",
    ),
    SkirmishActionChoices.RISKY_ATTACK: (
        "{attacker} takes a huge swing at {defender}",
        "{attacker} throws his whole weight into a blow at {defender}",
        "{attacker} winds up and hurls himself at {defender}",
        "{attacker} heaves his blade high over {defender}",
        "{attacker} gambles everything on one great stroke at {defender}",
    ),
    SkirmishActionChoices.FAST_ATTACK: (
        "{attacker} darts in at {defender}",
        "{attacker} jabs quickly at {defender}",
        "{attacker} slips inside {defender}'s guard",
        "{attacker} flicks a quick stroke at {defender}",
        "{attacker} is at {defender} before he is ready",
    ),
}

# How the slower man of a pair comes back at the man who struck first. A table of its own rather than an
# opening put in front of "APPROACH": both men of a pair strike, so every second sentence of a round is
# one of these, and they must not all start alike.
COUNTER_APPROACH = {
    SkirmishActionChoices.SIMPLE_ATTACK: (
        "{attacker} answers with a cut at {defender}",
        "{attacker} gives it back to {defender}",
        "Still on his feet, {attacker} swings back at {defender}",
        "{attacker} returns the stroke at {defender}",
        "{attacker} shakes it off and cuts back at {defender}",
    ),
    SkirmishActionChoices.RISKY_ATTACK: (
        "{attacker} answers with a huge swing at {defender}",
        "{attacker} throws everything back at {defender}",
        "Still on his feet, {attacker} hurls a great blow back at {defender}",
        "{attacker} roars and brings a heavy stroke round at {defender}",
        "{attacker} repays {defender} with all his weight behind it",
    ),
    SkirmishActionChoices.FAST_ATTACK: (
        "{attacker} answers with a quick jab at {defender}",
        "{attacker} darts back in at {defender}",
        "Still on his feet, {attacker} flicks a stroke back at {defender}",
        "{attacker} is back at {defender} in a heartbeat",
        "{attacker} slips past the blade and jabs back at {defender}",
    ),
}

# The counter of a man a fast attack beat to the blow. He swings back at a fraction of his weight, and
# that is what the sentence is about, whichever of the three he meant to throw.
OFF_BALANCE_COUNTER_APPROACH = (
    "Caught off-balance, {attacker} swings back weakly at {defender}",
    "Still reeling, {attacker} manages only a feeble stroke at {defender}",
    "{attacker}, wrong-footed, pokes back at {defender}",
    "Half-turned and unsteady, {attacker} lashes back at {defender}",
    "{attacker} recovers just enough to flail at {defender}",
)

# How the blow is met. The defender's own order serves as his defence, so a man who meant to attack is
# caught doing it rather than described as defending.
MEETING = {
    SkirmishActionChoices.SIMPLE_ATTACK: (
        "{defender} brings his own blade round to parry",
        "{defender} meets it with a cut of his own",
        "{defender} tries to turn it aside",
        "{defender} catches it on his own edge",
        "{defender} swings to meet it",
    ),
    SkirmishActionChoices.RISKY_ATTACK: (
        "{defender}, winding up a great blow of his own, is caught open",
        "{defender} is mid-swing and wide open",
        "{defender} has overreached and cannot recover",
        "{defender} is still hauling his own blade round",
        "{defender} has left himself bare for the sake of his own blow",
    ),
    SkirmishActionChoices.FAST_ATTACK: (
        "{defender} tries to dance clear",
        "{defender} twists away",
        "{defender} ducks aside",
        "{defender} tries to slip it",
        "{defender} skips back a step",
    ),
    SkirmishActionChoices.DEFENSIVE_STANCE: (
        "{defender} is braced behind his shield",
        "{defender} gets his shield up just in time",
        "{defender} crouches low behind his shield",
        "{defender} takes it on the rim of his shield",
        "{defender} sets his feet and raises his shield",
    ),
    SkirmishActionChoices.ASSAULT_FORTIFICATION: (
        "{defender}, hacking at the wall, barely turns",
        "{defender} has his back to him, busy at the wall",
        "{defender} looks round from the wall too late",
        "{defender} is wrestling with the palisade",
        "{defender}, prying at a stake, spins round",
    ),
    SkirmishActionChoices.RALLY: (
        "{defender}, shouting to his men, turns too late",
        "{defender} is calling his men to him and never sees it coming",
        "{defender} breaks off his rallying cry to face him",
        "{defender}, waving his men on, half turns",
        "{defender} has his face to his own line",
    ),
}

# What came of it. A hit is split by how much it took off the defender, see the shares above.
RESULT_MISSED = (
    "the blow goes wide",
    "the swing finds only air",
    "it whistles past him",
    "he is no longer where it lands",
    "it bites only earth",
)
RESULT_ABSORBED = (
    "his mail turns the edge",
    "the blow glances off his armour",
    "it rings off him without drawing blood",
    "the iron holds and he is unhurt",
    "his helm takes the blow",
)
RESULT_GRAZE = (
    "the edge only grazes him",
    "it draws a thin line of blood",
    "he hardly feels it",
    "it nicks him and no more",
    "it barely breaks the skin",
)
RESULT_SOLID = (
    "the blow lands hard",
    "the edge bites into him",
    "it catches him squarely",
    "it opens a red gash",
    "he grunts as it strikes home",
)
RESULT_HEAVY = (
    "the blow staggers him",
    "the edge bites deep",
    "the blow nearly fells him",
    "it drives him to one knee",
    "blood runs freely from the wound",
)

# An exchange in which the attacker threw nothing. There is no blow to meet, so the sentence is whole
# rather than assembled - the defender's order has nothing to answer.
NOT_THROWN = {
    SkirmishActionChoices.DEFENSIVE_STANCE: (
        "{attacker} stays behind his shield and gives {defender} nothing to answer.",
        "{attacker} holds his ground against {defender} and does not strike.",
        "{attacker} watches {defender} over the rim of his shield and waits.",
    ),
    SkirmishActionChoices.ASSAULT_FORTIFICATION: (
        "{attacker} is busy at the wall and never turns on {defender}.",
        "{attacker} keeps hacking at the wall and leaves {defender} be.",
        "{attacker} has eyes only for the wall, not for {defender}.",
    ),
    SkirmishActionChoices.RALLY: (
        "{attacker} is shouting to his men and lets {defender} be.",
        "{attacker} turns from {defender} to call his men together.",
        "{attacker} has no blow for {defender} while he rallies the line.",
    ),
}

# The opening of a sentence whose man has nobody of his own left to fight
UNOPPOSED_PREFIX = (
    "With nobody left to face him, ",
    "With no man of his own to fight, ",
    "Left over when the lines paired off, ",
    "Unopposed, ",
    "Finding nobody in front of him, ",
)

KILLED = (
    "{warrior} falls and does not rise again.",
    "{warrior} is cut down where he stands.",
    "{warrior} goes down, and he is dead before he hits the ground.",
)
INCAPACITATED = (
    "{warrior} crumples to the ground, senseless.",
    "{warrior} drops, out cold.",
    "{warrior} sinks to his knees and knows nothing more.",
)
FLED = (
    "{warrior}'s nerve breaks, and he runs.",
    "{warrior} throws down his guard and flees the field.",
    "{warrior} has had enough and bolts.",
)
WITHDREW = (
    "{warrior} falls back from the line, as he was ordered.",
    "{warrior} steps out of the fight on command.",
    "{warrior} gives ground and leaves the field in good order.",
)
INJURED = (
    "{warrior} will bear the mark of this day: {injury}.",
    "{warrior} carries this fight away with him: {injury}.",
    "{warrior} will not forget this day: {injury}.",
)
CAPTURED = (
    "{warrior} is seized and bound.",
    "{warrior} is dragged off in chains.",
    "{warrior} is hauled up and led away with his hands tied.",
)
ASSAULTED = (
    "{warrior} hacks at the wall, and timber splinters.",
    "{warrior} throws himself against the wall, and it shudders.",
    "{warrior} batters at the wall, and it holds — for now.",
)
FORTIFICATION_FELL = (
    "The wall gives way under {warrior}'s blows, and the defenders fight on in the open.",
    "With a crack the palisade goes down before {warrior}, and there is nothing left to hide behind.",
    "{warrior} tears the last of the wall aside, and the fight spills into the open.",
)
RALLIED = (
    "{leader} roars his men back into the line, and they steady.",
    "{leader} calls his men to him, and the line holds firm.",
    "{leader} bellows at his men, and they close up behind him.",
)
RALLIED_NOBODY = (
    "{leader} calls for his men, but nobody is left beside him to hear.",
    "{leader} shouts for his line, and no voice answers.",
    "{leader} turns to rally his men and finds himself alone.",
)
SKIRMISH_FINISHED = (
    "The fighting is over. {faction} holds the field.",
    "The last blow has fallen, and the field belongs to {faction}.",
    "It is done. {faction} stands over the field.",
)


# The saga draws from a generator of its own, not from the "random" module the fight rolls its dice on. A
# seeded game then plays out the same whatever the wording, and a phrasing added here cannot move a fight
# that the playtest harness replays by seed.
_WORDING = random.Random()


def _pick(*, phrasings: tuple[str, ...]) -> str:
    """
    The one draw in this module, so a test fixes every sentence by patching a single name.
    """
    return _WORDING.choice(phrasings)


def _phrasings_for(*, table: dict[int, tuple[str, ...]], value: int, part: str) -> tuple[str, ...]:
    # A value nobody wrote wording for raises rather than borrowing a sentence meant for something else,
    # the way the Tally's handlers do: a new action has to be told, not mistold
    try:
        return table[value]
    except KeyError:
        raise RuntimeError(f"No saga wording for the {part} of skirmish action {value}.") from None


def _approach_phrasings(*, attacker_action: int, defender_action: int, initiative: int) -> tuple[str, ...]:
    if initiative != InitiativeChoices.INITIATIVE_COUNTER:
        return _phrasings_for(table=APPROACH, value=attacker_action, part="approach")

    # The same rule the damage service halved the swing by, so the sentence cannot drift from it
    if SkirmishDamageService.is_off_balance_counter(defender_action=defender_action):
        return OFF_BALANCE_COUNTER_APPROACH

    return _phrasings_for(table=COUNTER_APPROACH, value=attacker_action, part="strike-back")


def _result_phrasings(*, outcome: int, damage: int, defender: Warrior) -> tuple[str, ...]:
    if outcome == BlowOutcomeChoices.OUTCOME_MISSED:
        return RESULT_MISSED
    if outcome == BlowOutcomeChoices.OUTCOME_ABSORBED:
        return RESULT_ABSORBED
    if outcome == BlowOutcomeChoices.OUTCOME_HIT:
        share = damage / defender.max_health
        if share < GRAZE_SHARE:
            return RESULT_GRAZE
        if share < SOLID_SHARE:
            return RESULT_SOLID
        return RESULT_HEAVY
    raise RuntimeError(f"No saga wording for blow outcome {outcome}.")


def saga_for_blow(
    *,
    attacker: Warrior,
    attacker_action: int,
    defender: Warrior,
    defender_action: int,
    initiative: int,
    outcome: int,
    damage: int,
) -> str:
    """
    One exchange, in one sentence: how he comes in, how it is met, what came of it.

    The initiative line of the Tally is folded in here rather than told on its own - who was quicker is
    the approach: a counter comes in with a strike-back of its own, and a man with nobody left to face
    gets it said at the front.
    """
    if outcome == BlowOutcomeChoices.OUTCOME_NOT_THROWN:
        sentence = _pick(phrasings=_phrasings_for(table=NOT_THROWN, value=attacker_action, part="stand-off")).format(
            attacker=attacker, defender=defender
        )
    else:
        approach = _pick(
            phrasings=_approach_phrasings(
                attacker_action=attacker_action, defender_action=defender_action, initiative=initiative
            )
        )
        meeting = _pick(phrasings=_phrasings_for(table=MEETING, value=defender_action, part="meeting"))
        result = _pick(phrasings=_result_phrasings(outcome=outcome, damage=damage, defender=defender))
        sentence = f"{approach}; {meeting} — {result}.".format(attacker=attacker, defender=defender)

    if initiative == InitiativeChoices.INITIATIVE_UNOPPOSED:
        return f"{_pick(phrasings=UNOPPOSED_PREFIX)}{sentence}"

    return sentence


def saga_for_killed(*, warrior: Warrior) -> str:
    return _pick(phrasings=KILLED).format(warrior=warrior)


def saga_for_incapacitated(*, warrior: Warrior) -> str:
    return _pick(phrasings=INCAPACITATED).format(warrior=warrior)


def saga_for_left_the_field(*, warrior: Warrior, was_ordered: bool) -> str:
    # The two ways off the field read differently here for the reason they do in the Tally: a man pulled
    # out on the player's order did not break
    return _pick(phrasings=WITHDREW if was_ordered else FLED).format(warrior=warrior)


def saga_for_injury(*, warrior: Warrior, injury: str) -> str:
    return _pick(phrasings=INJURED).format(warrior=warrior, injury=injury)


def saga_for_capture(*, warrior: Warrior) -> str:
    return _pick(phrasings=CAPTURED).format(warrior=warrior)


def saga_for_assault(*, warrior: Warrior) -> str:
    return _pick(phrasings=ASSAULTED).format(warrior=warrior)


def saga_for_fortification_fell(*, warrior: Warrior) -> str:
    return _pick(phrasings=FORTIFICATION_FELL).format(warrior=warrior)


def saga_for_rally(*, leader: Warrior, rallied_anybody: bool) -> str:
    return _pick(phrasings=RALLIED if rallied_anybody else RALLIED_NOBODY).format(leader=leader)


def saga_for_skirmish_finished(*, victorious_faction: Faction) -> str:
    return _pick(phrasings=SKIRMISH_FINISHED).format(faction=victorious_faction)
