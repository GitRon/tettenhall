from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.warband.skirmish.messages.events import item, skirmish, transaction, warrior
from apps.warband.skirmish.models import BattleHistory


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_log_warrior_takes_damage(*, context: warrior.WarriorTookDamage) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.attacker} strikes at {context.attack.value} against {context.defender}'s "
        f"{context.defense.value} defense, and {context.damage} damage gets through.",
    )


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_log_warrior_defends_all_damage(*, context: warrior.WarriorDefendedAllDamage) -> Command:
    """
    An exchange that cost the defender nothing, worded as whichever of the three it was.

    "OUTCOME_HIT" cannot arrive here - damage above zero is what makes an exchange the other event -
    so the three below are exhaustive over what this handler can see, and a fourth outcome added to
    the choices raises rather than picking up a fallback sentence nobody wrote.
    """
    if context.outcome == BlowOutcomeChoices.OUTCOME_NOT_THROWN:
        message = f"{context.attacker} throws nothing at {context.defender} this round."
    elif context.outcome == BlowOutcomeChoices.OUTCOME_MISSED:
        message = f"{context.attacker} swings at {context.defender} and misses."
    elif context.outcome == BlowOutcomeChoices.OUTCOME_ABSORBED:
        # The sibling line's wording with its tail changed: the two describe one exchange, and
        # naming the same two rolls the same way is what lets them be read as a pair
        message = (
            f"{context.attacker} strikes at {context.attack.value} against {context.defender}'s "
            f"{context.defense.value} defense, and nothing gets through."
        )
    else:
        raise RuntimeError(f"No battle log sentence for blow outcome {context.outcome}.")

    return CreateBattleHistory(skirmish=context.skirmish, message=message)


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_log_attacker_defender_decided(*, context: skirmish.AttackerDefenderDecided) -> Command:
    """
    Who strikes, why it is him rather than the other man, and where the other man's order went.

    The order the defender was given is not swallowed: the damage service feeds it through
    "get_defense_value", so it is spent as his defence. Saying only that he is the defender is what
    reads as a command the game ignored - he chose an attack, and no line accounted for it.

    A third way to become the attacker raises rather than picking up a sentence nobody wrote for it.
    """
    attack = SkirmishActionChoices(context.attacker_action).label
    defence = SkirmishActionChoices(context.defender_action).label

    if context.initiative == InitiativeChoices.INITIATIVE_WON_THE_ROLL:
        message = (
            f"{context.attacker} is quicker than {context.defender} and comes at him with a {attack}, "
            f"so {context.defender}'s {defence} serves as his defence."
        )
    elif context.initiative == InitiativeChoices.INITIATIVE_UNOPPOSED:
        message = (
            f"Nobody is left to face {context.attacker}, so he strikes free at {context.defender} with "
            f"a {attack}, and {context.defender}'s {defence} serves as his defence."
        )
    else:
        raise RuntimeError(f"No battle log sentence for initiative {context.initiative}.")

    return CreateBattleHistory(skirmish=context.skirmish, message=message)


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
def handle_log_warrior_incapacitation(*, context: warrior.WarriorWasIncapacitated) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of the fight being unconscious.",
        kind=BattleHistory.KindChoices.KIND_WARRIOR_INCAPACITATED,
        warrior=context.warrior,
    )


@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_log_warrior_death(*, context: warrior.WarriorWasKilled) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} is out of the fight being killed.",
        kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED,
        warrior=context.warrior,
    )


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_log_round_finished(*, context: skirmish.RoundFinished) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"Round {context.round_number} finished.",
        # The only line the panel reads as structure rather than as narration: it is where one round
        # ends, and no row carries a round number for the panel to group by instead.
        kind=BattleHistory.KindChoices.KIND_ROUND_FINISHED,
    )


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_log_skirmish_finished(*, context: skirmish.SkirmishFinished) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"Skirmish finished. {context.skirmish.victorious_faction} won.",
    )


@message_registry.register_event(event=item.ItemDroppedAsLoot)
def handle_log_item_dropped(*, context: item.ItemDroppedAsLoot) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} dropped the item '{context.item_name}'",
    )


@message_registry.register_event(event=warrior.WarriorWasCaptured)
def handle_warrior_is_captured(*, context: warrior.WarriorWasCaptured) -> Command | None:
    # A leader seized in an occupied town was taken without a fight, so there is no battle log to
    # write into. The line is not lost anywhere else either - an occupation has no history to read
    if context.skirmish is None:
        return None

    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} was captured and arrested.",
    )


@message_registry.register_event(event=warrior.WarriorGainedMorale)
def handle_warrior_gains_morale(*, context: warrior.WarriorGainedMorale) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} gained {int(context.gained_morale)} morale.",
    )


@message_registry.register_event(event=warrior.WarriorLostMorale)
def handle_warrior_lost_morale(*, context: warrior.WarriorLostMorale) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} lost {int(context.lost_morale)} morale.",
    )


@message_registry.register_event(event=warrior.WarriorHasFled)
def handle_warrior_has_fled(*, context: warrior.WarriorHasFled) -> Command:
    # The log is the one place the two ways off the field have to read differently. Telling a player
    # who has just ordered a retreat that his man was out of morale names a cause that is not only
    # absent but usually false - he is most likely to pull a warrior out while there is still nerve
    # in him.
    if context.was_ordered:
        message = f"{context.warrior} was ordered to withdraw and left the field."
    else:
        message = f"{context.warrior} is out of morale and fled the field."

    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=message,
        # One kind for both, although the sentences differ: the panel marks the line because the man
        # is gone, and how he came to be gone is what the sentence above is for
        kind=BattleHistory.KindChoices.KIND_WARRIOR_LEFT_THE_FIELD,
        warrior=context.warrior,
    )


@message_registry.register_event(event=warrior.WarriorGainedExperience)
def handle_warrior_gained_experience(*, context: warrior.WarriorGainedExperience) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} gained {context.gained_experience} experience.",
    )


@message_registry.register_event(event=warrior.WarriorGainedLevel)
def handle_warrior_gained_level(*, context: warrior.WarriorGainedLevel) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} reached level {context.level}.",
    )


@message_registry.register_event(event=warrior.WarriorImprovedStats)
def handle_warrior_improved_stats(*, context: warrior.WarriorImprovedStats) -> Command:
    """
    The wage rise is told to the player at the moment it happens. A bill that grows silently is one he
    discovers as an unexplained shortfall a month later.
    """
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} grew stronger: strength +{context.gained_strength}, "
        f"dexterity +{context.gained_dexterity}, health +{context.gained_max_health}, "
        f"morale +{context.gained_max_morale} — and now costs {context.new_monthly_salary} silver a month.",
    )


@message_registry.register_event(event=transaction.WarriorDroppedSilver)
def handle_warrior_dropped_silver(*, context: transaction.WarriorDroppedSilver) -> Command:
    return CreateBattleHistory(
        skirmish=context.skirmish,
        message=f"{context.warrior} dropped {context.amount} silver.",
    )
