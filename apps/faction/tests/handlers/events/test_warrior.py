from apps.faction.handlers.events.warrior import handle_draft_warrior_for_approved_fyrd_draft
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.messages.events.warrior import FyrdDraftApproved
from apps.faction.tests.factories.faction import FactionFactory


def test_handle_draft_warrior_for_approved_fyrd_draft_maps_to_command():
    """
    Pure mapping: handle_consider_fyrd_draft weighed the whole decision, which is what lets a rival's
    monthly draft run through the same command the player's fyrd card dispatches.
    """
    faction = FactionFactory.build()

    result = handle_draft_warrior_for_approved_fyrd_draft(context=FyrdDraftApproved(faction=faction, month=7))

    assert result == DraftWarriorFromFyrd(faction=faction, month=7)
