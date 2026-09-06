import pytest

from apps.month.models.player_month_log import PlayerMonthLog
from apps.month.services.player_month_log import group_player_month_logs
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory


@pytest.mark.django_db
def test_group_player_month_logs_splits_by_category():
    deserted = PlayerMonthLogFactory(
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_DESERTED,
        category=PlayerMonthLog.CategoryChoices.CATEGORY_ATTENTION,
    )
    salaries_paid = PlayerMonthLogFactory(kind=PlayerMonthLog.KindChoices.KIND_SALARIES_PAID)
    healed = PlayerMonthLogFactory(
        kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
        category=PlayerMonthLog.CategoryChoices.CATEGORY_UPKEEP,
    )

    result = group_player_month_logs(player_month_logs=[deserted, salaries_paid, healed])

    assert result.attention == [deserted]
    assert result.consequence == [salaries_paid]
    assert result.upkeep == [healed]


@pytest.mark.django_db
def test_group_player_month_logs_tallies_the_upkeep_per_kind():
    """
    The recovery sweeps write one row per warrior, so the upkeep is most of a fought month and none
    of it is worth a line of its own.
    """
    player_month_logs = [
        PlayerMonthLogFactory(
            kind=PlayerMonthLog.KindChoices.KIND_MORALE_RECOVERED,
            category=PlayerMonthLog.CategoryChoices.CATEGORY_UPKEEP,
        )
        for _ in range(3)
    ]
    player_month_logs.append(
        PlayerMonthLogFactory(
            kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
            category=PlayerMonthLog.CategoryChoices.CATEGORY_UPKEEP,
        )
    )

    result = group_player_month_logs(player_month_logs=player_month_logs)

    assert result.upkeep_summary == ["3 warriors recovered their morale", "1 warrior was healed"]


@pytest.mark.django_db
def test_group_player_month_logs_without_any_rows():
    result = group_player_month_logs(player_month_logs=[])

    assert result.is_empty is True


@pytest.mark.django_db
def test_group_player_month_logs_is_not_empty_with_only_upkeep():
    """
    A month whose only news is upkeep still has something to show, so the empty state must not stand
    in for a collapsed one.
    """
    healed = PlayerMonthLogFactory(
        kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
        category=PlayerMonthLog.CategoryChoices.CATEGORY_UPKEEP,
    )

    result = group_player_month_logs(player_month_logs=[healed])

    assert result.is_empty is False


def test_upkeep_summary_phrases_cover_every_upkeep_kind():
    """
    A missing phrase is a KeyError when the month is finished rather than a silent fallback, so the
    two dicts are held to the same set of kinds here instead.
    """
    upkeep_kinds = {
        kind
        for kind, category in PlayerMonthLog.KIND_CATEGORIES.items()
        if category == PlayerMonthLog.CategoryChoices.CATEGORY_UPKEEP
    }

    assert set(PlayerMonthLog.UPKEEP_SUMMARY_PHRASES) == upkeep_kinds


def test_kind_categories_covers_every_kind():
    """
    create_record() looks every kind up here, so a kind without a category cannot write a line at all.
    """
    assert set(PlayerMonthLog.KIND_CATEGORIES) == set(PlayerMonthLog.KindChoices)
