from apps.warband.calendar.months import Blotmonath, Eosturmonath, Haligmonath, Summer, Winter, Winterfylleth


def test_get_season_of_a_summer_month():
    assert Eosturmonath.get_season() is Summer


def test_get_season_of_a_winter_month():
    assert Blotmonath.get_season() is Winter


def test_has_effects_beyond_its_season_for_a_month_that_overrides_one():
    assert Blotmonath.has_effects_beyond_its_season() is True


def test_has_effects_beyond_its_season_for_a_plain_month():
    assert Winterfylleth.has_effects_beyond_its_season() is False


def test_get_march_cost_in_winter():
    assert Winterfylleth.get_march_cost(warrior_count=5) == 50


def test_get_march_cost_in_summer():
    assert Eosturmonath.get_march_cost(warrior_count=5) == 0


def test_get_effects_of_a_plain_summer_month():
    """Summer levers nothing, so a summer month with nothing of its own says only that."""
    assert Eosturmonath.get_effects() == ("Nothing marks this month beyond its season.",)


def test_get_effects_of_a_plain_winter_month():
    assert Winterfylleth.get_effects() == (
        "Winter march: 10 silver per man",
        "Training advances faster",
        "Nothing marks this month beyond its season.",
    )


def test_get_effects_of_the_harvest_month():
    assert Haligmonath.get_effects() == (
        "The harvest brings in 100 silver",
        "The fyrd does not grow: its men are in the fields",
    )


def test_get_effects_of_the_slaughter_month():
    assert Blotmonath.get_effects() == ("Winter march: 5 silver per man", "Training advances faster")
