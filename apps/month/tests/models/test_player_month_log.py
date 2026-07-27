from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory


def test_str_returns_the_title():
    player_month_log = PlayerMonthLogFactory.build(title="The fyrd has increased!")

    assert str(player_month_log) == "The fyrd has increased!"
