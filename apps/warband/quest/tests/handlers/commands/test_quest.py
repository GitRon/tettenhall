from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.handlers.commands.quest import handle_accept_quest, handle_offer_quests
from apps.warband.quest.messages.commands.quest import AcceptQuest, OfferQuests
from apps.warband.quest.messages.events.quest import QuestAccepted, QuestsOffered
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.merchant_guard import MerchantGuard
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_offer_quests_pins_the_drawn_quests():
    faction = FactionFactory()

    WarriorFactory.create_batch(2, faction=faction)

    with mock.patch(
        "apps.warband.quest.services.offer.random.choices", side_effect=[[MerchantGuard], [DriveOffWolves]]
    ):
        result = handle_offer_quests(context=OfferQuests(faction=faction, month=4))

    quests = list(Quest.objects.for_player_faction(faction_id=faction.id))
    assert result == QuestsOffered(faction=faction, quests=quests, month=4)
    assert [(quest.quest, quest.title, quest.month) for quest in quests] == [
        ("MerchantGuard", MerchantGuard.TITLE, 4),
        ("DriveOffWolves", DriveOffWolves.TITLE, 4),
    ]


@pytest.mark.django_db
def test_handle_offer_quests_replaces_last_months_board():
    stale_quest = QuestFactory(month=3)

    handle_offer_quests(context=OfferQuests(faction=stale_quest.faction, month=4))

    assert Quest.objects.filter(pk=stale_quest.pk).exists() is False


@pytest.mark.django_db
def test_handle_accept_quest_signs_the_men_on():
    quest = QuestFactory(month=2)
    warrior = WarriorFactory(faction=quest.faction)

    result = handle_accept_quest(
        context=AcceptQuest(accepting_faction=quest.faction, quest=quest, assigned_warriors=[warrior], month=2)
    )

    quest_contract = QuestContract.objects.get(faction=quest.faction)
    assert result == QuestAccepted(
        accepting_faction=quest.faction, quest_contract=quest_contract, assigned_warriors=[warrior], month=2
    )
    assert (quest_contract.quest, quest_contract.title, list(quest_contract.assigned_warriors.all())) == (
        quest.quest,
        quest.title,
        [warrior],
    )


@pytest.mark.django_db
def test_handle_accept_quest_takes_the_offer_off_the_board():
    quest = QuestFactory(month=2)
    warrior = WarriorFactory(faction=quest.faction)

    handle_accept_quest(
        context=AcceptQuest(accepting_faction=quest.faction, quest=quest, assigned_warriors=[warrior], month=2)
    )

    assert Quest.objects.filter(pk=quest.pk).exists() is False


@pytest.mark.django_db
def test_handle_accept_quest_twice():
    """A double click: the second request finds the offer gone and signs nobody on."""
    quest = QuestFactory(month=2)
    warrior = WarriorFactory(faction=quest.faction)
    command = AcceptQuest(accepting_faction=quest.faction, quest=quest, assigned_warriors=[warrior], month=2)
    handle_accept_quest(context=command)

    result = handle_accept_quest(context=command)

    assert result is None
    assert QuestContract.objects.filter(faction=quest.faction).count() == 1
