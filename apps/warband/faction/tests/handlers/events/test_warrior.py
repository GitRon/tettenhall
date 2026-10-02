import pytest

from apps.warband.faction.handlers.events.warrior import (
    handle_add_dismissed_warrior_to_pub,
    handle_add_new_warrior_to_faction_pub,
    handle_add_warrior_who_walked_out_to_pub,
    handle_draft_warrior_for_approved_fyrd_draft,
    handle_hand_out_gear_for_recruited_warrior,
    handle_recruit_mercenary_for_approved_pub_hire,
    handle_restock_mercenaries_in_pub_for_new_faction,
    handle_restock_mercenaries_in_pub_once_month_is_planned,
)
from apps.warband.faction.messages.commands.item import HandOutFactionGear
from apps.warband.faction.messages.commands.warrior import (
    AddWarriorToPub,
    DraftWarriorFromFyrd,
    RecruitPubMercenary,
    RestockTownMercenaries,
)
from apps.warband.faction.messages.events.faction import FactionMonthPlanned, NewFactionCreated
from apps.warband.faction.messages.events.warrior import (
    FyrdDraftApproved,
    PubMercenaryHireApproved,
    WarriorRecruited,
)
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.messages.events.warrior import (
    WarriorCreated,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


def test_handle_add_new_warrior_to_faction_pub_stocks_the_shelf():
    """
    Stock, because the only thing raising WarriorCreated is the restock asking for a man to fill a
    stool: his row exists to be hired or swept away with the next one.
    """
    pub_owner = FactionFactory.build()
    savegame = SavegameFactory.build()
    warrior = WarriorFactory.build()

    result = handle_add_new_warrior_to_faction_pub(
        context=WarriorCreated(warrior=warrior, savegame=savegame, faction=None, pub_owner=pub_owner, month=7)
    )

    assert result == AddWarriorToPub(
        savegame=savegame, pub_owner=pub_owner, warrior=warrior, is_pub_stock=True, month=7
    )


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

    assert result == AddWarriorToPub(savegame=savegame, pub_owner=faction, warrior=warrior, is_pub_stock=False, month=7)


@pytest.mark.django_db
def test_handle_add_warrior_who_walked_out_to_pub_is_not_stock():
    """
    The restock empties its shelf with a row delete, so a veteran marked as stock would be destroyed
    at the start of the next month - and a war band that cannot pay its wages would lose him twice.
    """
    faction = FactionFactory(is_player=True)
    warrior = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_add_warrior_who_walked_out_to_pub(
        context=WarriorWalkedOutOverUnpaidSalary(warrior=warrior, faction=faction, savegame=faction.savegame, month=7)
    )

    assert result == AddWarriorToPub(
        savegame=faction.savegame, pub_owner=faction, warrior=warrior, is_pub_stock=False, month=7
    )


@pytest.mark.django_db
def test_handle_add_warrior_who_walked_out_to_pub_ignores_a_rival():
    """
    Rivals go unpaid on the same rule, but whose shelf a rival's veteran stands on is #157's decision,
    and parking him in his old faction's pub would take it.
    """
    player_faction = FactionFactory(is_player=True)
    rival = FactionFactory(savegame=player_faction.savegame)
    warrior = WarriorFactory(faction=None, savegame=rival.savegame, culture=rival.culture)

    result = handle_add_warrior_who_walked_out_to_pub(
        context=WarriorWalkedOutOverUnpaidSalary(warrior=warrior, faction=rival, savegame=rival.savegame, month=7)
    )

    assert result is None


def test_handle_draft_warrior_for_approved_fyrd_draft_maps_to_command():
    """
    Pure mapping: handle_plan_faction_month weighed the whole decision, which is what lets a rival's
    monthly draft run through the same command the player's fyrd card dispatches.
    """
    faction = FactionFactory.build()

    result = handle_draft_warrior_for_approved_fyrd_draft(context=FyrdDraftApproved(faction=faction, month=7))

    assert result == DraftWarriorFromFyrd(faction=faction, month=7)


def test_handle_restock_mercenaries_in_pub_for_new_faction_maps_to_command():
    faction = FactionFactory.build()

    result = handle_restock_mercenaries_in_pub_for_new_faction(
        context=NewFactionCreated(faction=faction, current_month=1, is_player=True)
    )

    assert result == RestockTownMercenaries(faction=faction, month=1)


def test_handle_recruit_mercenary_for_approved_pub_hire_maps_to_command():
    """
    Pure mapping: handle_plan_faction_month weighed the whole decision, which is what lets a rival hire
    through the same command the player's pub dispatches.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build()

    result = handle_recruit_mercenary_for_approved_pub_hire(
        context=PubMercenaryHireApproved(faction=faction, warrior=warrior, month=7)
    )

    assert result == RecruitPubMercenary(warrior=warrior, faction=faction, month=7)


def test_handle_restock_mercenaries_in_pub_once_month_is_planned_maps_to_command():
    faction = FactionFactory.build()

    result = handle_restock_mercenaries_in_pub_once_month_is_planned(
        context=FactionMonthPlanned(faction=faction, month=7)
    )

    assert result == RestockTownMercenaries(faction=faction, month=7)


def test_handle_hand_out_gear_for_recruited_warrior_maps_to_command():
    faction = FactionFactory.build()

    result = handle_hand_out_gear_for_recruited_warrior(
        context=WarriorRecruited(faction=faction, warrior=WarriorFactory.build(), recruitment_price=0, month=4)
    )

    assert result == HandOutFactionGear(faction=faction)
