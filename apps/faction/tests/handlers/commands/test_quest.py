from unittest import mock

import pytest

from apps.faction.handlers.commands.quest import handle_offer_quests
from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.messages.events.quest import BulletinBoardQuestsOffered, NewBulletinBoardQuestRequired
from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.tests.factories.quest import QuestFactory


def _player_faction() -> Faction:
    """
    A faction its own savegame points to as the player's.

    FactionFactory leaves "savegame.player_faction" unset, and only the player has a bulletin board,
    so a plain factory faction is skipped by the handler.
    """
    faction = FactionFactory()
    faction.savegame.player_faction = faction
    faction.savegame.save()

    return faction


@pytest.mark.django_db
def test_handle_offer_quests_requests_one_quest_per_drawn_slot():
    faction = _player_faction()

    with mock.patch("apps.faction.handlers.commands.quest.random.randrange", return_value=2):
        result = handle_offer_quests(context=OfferNewQuestsOnBulletinBoard(faction=faction, month=3))

    *quest_requests, _ = result
    expected_message = NewBulletinBoardQuestRequired(savegame=faction.savegame, faction=faction, month=3)
    assert quest_requests == [expected_message] * 2


@pytest.mark.django_db
def test_handle_offer_quests_removes_previous_quests():
    faction = _player_faction()
    faction.available_quests.add(QuestFactory())

    with mock.patch("apps.faction.handlers.commands.quest.random.randrange", return_value=2):
        handle_offer_quests(context=OfferNewQuestsOnBulletinBoard(faction=faction, month=3))

    assert faction.available_quests.count() == 0


@pytest.mark.django_db
def test_handle_offer_quests_announces_the_whole_board_once():
    faction = _player_faction()

    with mock.patch("apps.faction.handlers.commands.quest.random.randrange", return_value=2):
        result = handle_offer_quests(context=OfferNewQuestsOnBulletinBoard(faction=faction, month=3))

    assert result[-1] == BulletinBoardQuestsOffered(faction=faction, new_quests=2, month=3)


@pytest.mark.django_db
def test_handle_offer_quests_refuses_a_rival():
    """
    The board a rival was handed is one nothing refreshes and nobody can accept off, so it is not
    built at all - and the quest already pinned to it survives, which is what places the guard above
    the clean-up rather than below it.
    """
    player_faction = _player_faction()
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    rival_faction.available_quests.add(QuestFactory())

    result = handle_offer_quests(context=OfferNewQuestsOnBulletinBoard(faction=rival_faction, month=3))

    assert result == []
    assert rival_faction.available_quests.count() == 1
