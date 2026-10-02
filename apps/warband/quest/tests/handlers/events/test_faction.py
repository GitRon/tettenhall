import pytest

from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.handlers.events.faction import handle_offer_quests_for_new_faction
from apps.warband.quest.messages.commands.quest import OfferQuests


@pytest.mark.django_db
def test_handle_offer_quests_for_new_faction_of_the_player():
    faction = FactionFactory()

    result = handle_offer_quests_for_new_faction(
        context=NewFactionCreated(faction=faction, current_month=1, is_player=True)
    )

    assert result == OfferQuests(faction=faction, month=1)


@pytest.mark.django_db
def test_handle_offer_quests_for_new_faction_of_a_rival():
    faction = FactionFactory()

    result = handle_offer_quests_for_new_faction(
        context=NewFactionCreated(faction=faction, current_month=1, is_player=False)
    )

    assert result is None
