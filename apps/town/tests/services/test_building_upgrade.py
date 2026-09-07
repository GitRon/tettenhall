import pytest

from apps.finance.tests.factories.transaction import TransactionFactory
from apps.town.models import Town
from apps.town.services.building_upgrade import (
    ALREADY_BUILT_THIS_MONTH_REFUSAL,
    MAXIMUM_LEVEL_REFUSAL,
    UNAFFORDABLE_REFUSAL,
    get_building_upgrade_refusal,
)


@pytest.mark.django_db
def test_get_building_upgrade_refusal_with_an_affordable_next_level(current_savegame):
    town = current_savegame.player_faction.town
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    result = get_building_upgrade_refusal(town=town, building_type="hall", current_savegame=current_savegame)

    assert result is None


@pytest.mark.django_db
def test_get_building_upgrade_refusal_at_the_maximum_level(current_savegame):
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_LARGE
    town.save()

    result = get_building_upgrade_refusal(town=town, building_type="hall", current_savegame=current_savegame)

    assert result == MAXIMUM_LEVEL_REFUSAL


@pytest.mark.django_db
def test_get_building_upgrade_refusal_with_a_building_already_commissioned_this_month(current_savegame):
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = current_savegame.current_month
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    result = get_building_upgrade_refusal(town=town, building_type="hall", current_savegame=current_savegame)

    assert result == ALREADY_BUILT_THIS_MONTH_REFUSAL


@pytest.mark.django_db
def test_get_building_upgrade_refusal_one_silver_short_of_the_price(current_savegame):
    town = current_savegame.player_faction.town
    TransactionFactory(faction=current_savegame.player_faction, amount=899)

    result = get_building_upgrade_refusal(town=town, building_type="hall", current_savegame=current_savegame)

    assert result == UNAFFORDABLE_REFUSAL


@pytest.mark.django_db
def test_get_building_upgrade_refusal_reports_the_month_before_the_price(current_savegame):
    """
    Both apply to a player who has built this month and cannot pay either. The month is the one he
    cannot act on until it is over, so naming the price would send him off to raise silver he may
    not spend yet.
    """
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = current_savegame.current_month
    town.save()

    result = get_building_upgrade_refusal(town=town, building_type="hall", current_savegame=current_savegame)

    assert result == ALREADY_BUILT_THIS_MONTH_REFUSAL
