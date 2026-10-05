import pytest

from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.town.models import Town
from apps.warband.town.services.feast import (
    ALREADY_FEASTED_THIS_MONTH_REFUSAL,
    NO_HALL_REFUSAL,
    UNAFFORDABLE_FEAST_REFUSAL,
    get_feast_refusal,
)


def _with_hall(current_savegame) -> Town:
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_SMALL
    town.save()

    return town


@pytest.mark.django_db
def test_get_feast_refusal_with_a_hall_and_the_silver_for_every_head(current_savegame):
    town = _with_hall(current_savegame)
    TransactionFactory(faction=current_savegame.player_faction, amount=45)

    result = get_feast_refusal(town=town, head_count=3, current_savegame=current_savegame)

    assert result is None


@pytest.mark.django_db
def test_get_feast_refusal_without_a_hall(current_savegame):
    town = current_savegame.player_faction.town
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    result = get_feast_refusal(town=town, head_count=3, current_savegame=current_savegame)

    assert result == NO_HALL_REFUSAL


@pytest.mark.django_db
def test_get_feast_refusal_with_a_feast_already_thrown_this_month(current_savegame):
    town = _with_hall(current_savegame)
    town.last_feast_at = current_savegame.current_month
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    result = get_feast_refusal(town=town, head_count=3, current_savegame=current_savegame)

    assert result == ALREADY_FEASTED_THIS_MONTH_REFUSAL


@pytest.mark.django_db
def test_get_feast_refusal_short_of_the_whole_table(current_savegame):
    """
    A feast is for the whole roster or nobody: forty-four silver does not feed two of three men.
    """
    town = _with_hall(current_savegame)
    TransactionFactory(faction=current_savegame.player_faction, amount=44)

    result = get_feast_refusal(town=town, head_count=3, current_savegame=current_savegame)

    assert result == UNAFFORDABLE_FEAST_REFUSAL


@pytest.mark.django_db
def test_get_feast_refusal_names_the_month_before_the_price(current_savegame):
    town = _with_hall(current_savegame)
    town.last_feast_at = current_savegame.current_month
    town.save()

    result = get_feast_refusal(town=town, head_count=3, current_savegame=current_savegame)

    assert result == ALREADY_FEASTED_THIS_MONTH_REFUSAL
