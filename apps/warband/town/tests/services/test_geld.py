import pytest

from apps.warband.town.services.geld import (
    ALREADY_GELDED_THIS_MONTH_REFUSAL,
    EMPTY_FYRD_REFUSAL,
    get_geld_refusal,
)


@pytest.mark.django_db
def test_get_geld_refusal_with_a_name_on_the_roll(current_savegame):
    faction = current_savegame.player_faction
    faction.fyrd_reserve = 1

    result = get_geld_refusal(town=faction.town, faction=faction, current_savegame=current_savegame)

    assert result is None


@pytest.mark.django_db
def test_get_geld_refusal_with_nobody_left_on_the_roll(current_savegame):
    faction = current_savegame.player_faction
    faction.fyrd_reserve = 0

    result = get_geld_refusal(town=faction.town, faction=faction, current_savegame=current_savegame)

    assert result == EMPTY_FYRD_REFUSAL


@pytest.mark.django_db
def test_get_geld_refusal_with_a_geld_already_called_this_month(current_savegame):
    faction = current_savegame.player_faction
    faction.fyrd_reserve = 3
    faction.town.last_geld_at = current_savegame.current_month

    result = get_geld_refusal(town=faction.town, faction=faction, current_savegame=current_savegame)

    assert result == ALREADY_GELDED_THIS_MONTH_REFUSAL


@pytest.mark.django_db
def test_get_geld_refusal_names_the_month_before_the_empty_roll(current_savegame):
    faction = current_savegame.player_faction
    faction.fyrd_reserve = 0
    faction.town.last_geld_at = current_savegame.current_month

    result = get_geld_refusal(town=faction.town, faction=faction, current_savegame=current_savegame)

    assert result == ALREADY_GELDED_THIS_MONTH_REFUSAL
