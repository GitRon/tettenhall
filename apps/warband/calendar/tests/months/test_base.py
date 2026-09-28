from apps.warband.calendar.months import Blotmonath, Eosturmonath, Haligmonath, Winterfylleth


def test_get_march_cost_in_winter():
    assert Winterfylleth.get_march_cost(warrior_count=5) == 50


def test_get_march_cost_in_summer():
    assert Eosturmonath.get_march_cost(warrior_count=5) == 0


def test_get_effects_of_a_plain_summer_month():
    """Summer levers nothing, so a summer month with nothing of its own has no lines at all."""
    assert Eosturmonath.get_effects() == ()


def test_get_effects_of_a_plain_winter_month():
    assert Winterfylleth.get_effects() == ("Winter march: 10 silver per man", "Training advances faster")


def test_get_effects_of_the_harvest_month():
    assert Haligmonath.get_effects() == (
        "The harvest brings in 100 silver",
        "The fyrd does not grow: its men are in the fields",
    )


def test_get_effects_of_the_slaughter_month():
    assert Blotmonath.get_effects() == ("Winter march: 5 silver per man", "Training advances faster")
