import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.messages.events.month import PlayerMonthPrepared
from apps.warband.quest.handlers.events.month import (
    handle_bring_quest_contracts_home_for_new_month,
    handle_offer_quests_for_new_month,
)
from apps.warband.quest.messages.commands.quest import OfferQuests
from apps.warband.quest.messages.commands.quest_contract import BringQuestContractsHome


@pytest.mark.django_db
def test_handle_offer_quests_for_new_month():
    faction = FactionFactory()

    result = handle_offer_quests_for_new_month(
        context=PlayerMonthPrepared(faction=faction, savegame=faction.savegame, current_month=4)
    )

    assert result == OfferQuests(faction=faction, month=4)


@pytest.mark.django_db
def test_handle_bring_quest_contracts_home_for_new_month():
    faction = FactionFactory()

    result = handle_bring_quest_contracts_home_for_new_month(
        context=PlayerMonthPrepared(faction=faction, savegame=faction.savegame, current_month=4)
    )

    assert result == BringQuestContractsHome(faction=faction, month=4)
