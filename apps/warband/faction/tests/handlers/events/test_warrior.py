import pytest

from apps.warband.faction.handlers.events.warrior import (
    handle_add_dismissed_warrior_to_pub,
    handle_add_new_warrior_to_faction_pub,
    handle_add_warrior_who_walked_out_to_pub,
    handle_draft_warrior_for_approved_fyrd_draft,
)
from apps.warband.faction.messages.commands.faction import AddWarriorToPub
from apps.warband.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.warband.faction.messages.events.warrior import FyrdDraftApproved
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.messages.events.warrior import (
    WarriorCreated,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


def _player_faction() -> Faction:
    """
    A faction its own savegame points to as the player's.

    Saved rather than built, because the pub gate compares "savegame.player_faction_id" against the
    faction's id: two unsaved rows are both None and would pass a comparison that decides who may
    stock the player's shelf.
    """
    faction = FactionFactory()
    faction.savegame.player_faction = faction
    faction.savegame.save()

    return faction


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


@pytest.mark.django_db
def test_handle_add_warrior_who_walked_out_to_pub_is_not_stock():
    """
    The restock empties its shelf with a row delete, so a veteran marked as stock would be destroyed
    at the start of the next month - and a war band that cannot pay its wages would lose him twice.
    """
    faction = _player_faction()
    warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_add_warrior_who_walked_out_to_pub(
        context=WarriorWalkedOutOverUnpaidSalary(warrior=warrior, faction=faction, savegame=faction.savegame, month=7)
    )

    assert result == AddWarriorToPub(
        savegame=faction.savegame, faction=faction, warrior=warrior, is_pub_stock=False, month=7
    )


@pytest.mark.django_db
def test_handle_add_warrior_who_walked_out_to_pub_ignores_a_rival():
    """
    Rivals go unpaid on the same rule, and there is one pub in a savegame. Without this, every rival
    that missed its payroll would be stocking the player's shelf with the veterans it could not pay.
    """
    player_faction = _player_faction()
    rival = FactionFactory(savegame=player_faction.savegame)
    warrior = WarriorFactory(faction=None, savegame=rival.savegame, culture=rival.culture)

    result = handle_add_warrior_who_walked_out_to_pub(
        context=WarriorWalkedOutOverUnpaidSalary(warrior=warrior, faction=rival, savegame=rival.savegame, month=7)
    )

    assert result is None


def test_handle_draft_warrior_for_approved_fyrd_draft_maps_to_command():
    """
    Pure mapping: handle_consider_fyrd_draft weighed the whole decision, which is what lets a rival's
    monthly draft run through the same command the player's fyrd card dispatches.
    """
    faction = FactionFactory.build()

    result = handle_draft_warrior_for_approved_fyrd_draft(context=FyrdDraftApproved(faction=faction, month=7))

    assert result == DraftWarriorFromFyrd(faction=faction, month=7)
