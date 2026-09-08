from apps.faction.handlers.events.warrior import (
    handle_add_dismissed_warrior_to_pub,
    handle_add_new_warrior_to_faction_pub,
    handle_draft_warrior_for_approved_fyrd_draft,
)
from apps.faction.messages.commands.faction import AddWarriorToPub
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.messages.events.warrior import FyrdDraftApproved
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.events.warrior import WarriorCreated, WarriorWasDismissed


def test_handle_add_new_warrior_to_faction_pub_stocks_the_shelf():
    """
    Stock, because the only thing raising WarriorCreated is the restock asking for a man to fill a
    stool: his row exists to be hired or swept away with the next one.
    """
    faction = FactionFactory.build()
    savegame = SavegameFactory.build()
    warrior = WarriorFactory.build()

    result = handle_add_new_warrior_to_faction_pub(
        context=WarriorCreated(warrior=warrior, savegame=savegame, faction=faction, month=7)
    )

    assert result == AddWarriorToPub(savegame=savegame, faction=faction, warrior=warrior, is_pub_stock=True, month=7)


def test_handle_add_dismissed_warrior_to_pub_is_not_stock():
    """
    The restock empties its shelf with a row delete, so a dismissed veteran marked as stock would be
    destroyed at the start of the next month.
    """
    faction = FactionFactory.build()
    savegame = SavegameFactory.build()
    warrior = WarriorFactory.build()

    result = handle_add_dismissed_warrior_to_pub(
        context=WarriorWasDismissed(warrior=warrior, faction=faction, savegame=savegame, severance_pay=120, month=7)
    )

    assert result == AddWarriorToPub(savegame=savegame, faction=faction, warrior=warrior, is_pub_stock=False, month=7)


def test_handle_draft_warrior_for_approved_fyrd_draft_maps_to_command():
    """
    Pure mapping: handle_consider_fyrd_draft weighed the whole decision, which is what lets a rival's
    monthly draft run through the same command the player's fyrd card dispatches.
    """
    faction = FactionFactory.build()

    result = handle_draft_warrior_for_approved_fyrd_draft(context=FyrdDraftApproved(faction=faction, month=7))

    assert result == DraftWarriorFromFyrd(faction=faction, month=7)
