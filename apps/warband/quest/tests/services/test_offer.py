from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.quests.harvest_hands import HarvestHands
from apps.warband.quest.quests.kings_summons import KingsSummons
from apps.warband.quest.quests.merchant_guard import MerchantGuard
from apps.warband.quest.services.offer import draw_quests_to_offer
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_draw_quests_to_offer_draws_an_odd_job_and_an_errand():
    faction = FactionFactory()
    WarriorFactory.create_batch(4, faction=faction)

    with mock.patch(
        "apps.warband.quest.services.offer.random.choices", side_effect=[[MerchantGuard], [DriveOffWolves]]
    ):
        result = draw_quests_to_offer(faction=faction)

    assert result == [MerchantGuard, DriveOffWolves]


@pytest.mark.django_db
def test_draw_quests_to_offer_offers_only_what_the_roster_can_send():
    """One man: every errand wanting two is out of the draw, so only the one-man entries are drawn from."""
    faction = FactionFactory()
    WarriorFactory(faction=faction)

    drawn_from = []

    def first_of(population, weights) -> list:
        drawn_from.append(list(population))
        return [population[0]]

    with mock.patch("apps.warband.quest.services.offer.random.choices", side_effect=first_of):
        draw_quests_to_offer(faction=faction)

    assert drawn_from == [[HarvestHands, MerchantGuard], [KingsSummons]]


@pytest.mark.django_db
def test_draw_quests_to_offer_at_the_founding():
    """The leader's row is not written yet when the first board is drawn, and he still counts."""
    faction = FactionFactory()

    with mock.patch("apps.warband.quest.services.offer.random.choices", side_effect=[[HarvestHands], [KingsSummons]]):
        result = draw_quests_to_offer(faction=faction)

    assert result == [HarvestHands, KingsSummons]
