from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.savegame.messages.commands.savegame import CreateNewSavegame, DetermineSavegameOutcome
from apps.savegame.messages.events.savegame import NewSavegameCreated, SavegameEnded
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.skirmish import Skirmish


@message_registry.register_command(command=CreateNewSavegame)
def handle_create_new_savegame(*, context: CreateNewSavegame) -> list[Event] | Event:
    # Create savegame object
    savegame = Savegame.objects.create(
        name=f"{context.town_name}/{context.faction_name}",
        created_by_id=context.created_by_id,
    )

    # Set savegame as active savegame and set all others of the current user as inactive
    Savegame.objects.activate_savegame(savegame=savegame)

    return NewSavegameCreated(
        savegame=savegame,
        faction_name=context.faction_name,
        town_name=context.town_name,
        faction_culture_id=context.faction_culture_id,
    )


@message_registry.register_command(command=DetermineSavegameOutcome)
def handle_determine_savegame_outcome(*, context: DetermineSavegameOutcome) -> Event | None:
    """
    Ends the game once a defeat has decided it, one way or the other.

    Returning None while it is still running is also what stops this from looping: force-resolving the
    open skirmish below captures warriors, which can defeat another faction, which lands back here.
    """
    if context.savegame.outcome != Savegame.OutcomeChoices.OUTCOME_RUNNING:
        return None

    still_standing = Faction.objects.still_in_play(savegame_id=context.savegame.id)

    if not still_standing.filter(id=context.savegame.player_faction_id).exists():
        outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    elif not still_standing.exclude(id=context.savegame.player_faction_id).exists():
        outcome = Savegame.OutcomeChoices.OUTCOME_WON
    else:
        return None

    context.savegame.outcome = outcome
    context.savegame.save(update_fields=("outcome",))

    # The fight the game ended in is still open, and deciding it needs a query the consuming event
    # handler is not allowed to make. Evaluated here so the message carries warriors, not a queryset
    open_skirmish_list = list(Skirmish.objects.unresolved().for_savegame(savegame_id=context.savegame.id))

    return SavegameEnded(
        savegame=context.savegame,
        outcome=outcome,
        open_skirmish_list=open_skirmish_list,
        month=context.savegame.current_month,
    )
