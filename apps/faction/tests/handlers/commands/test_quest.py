from unittest import mock

import pytest

from apps.faction.handlers.commands.quest import handle_offer_quests
from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.messages.events.quest import NewBulletinBoardQuestRequired
from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.tests.factories.quest import QuestFactory


@pytest.mark.django_db
def test_handle_offer_quests_requests_one_quest_per_drawn_slot():
    faction = FactionFactory()

    with mock.patch("apps.faction.handlers.commands.quest.random.randrange", return_value=2):
        result = handle_offer_quests(context=OfferNewQuestsOnBulletinBoard(faction=faction, month=3))

    expected_message = NewBulletinBoardQuestRequired(savegame=faction.savegame, faction=faction, month=3)
    assert result == [expected_message] * 2


@pytest.mark.django_db
def test_handle_offer_quests_removes_previous_quests():
    faction = FactionFactory()
    faction.available_quests.add(QuestFactory())

    with mock.patch("apps.faction.handlers.commands.quest.random.randrange", return_value=2):
        handle_offer_quests(context=OfferNewQuestsOnBulletinBoard(faction=faction, month=3))

    assert faction.available_quests.count() == 0
