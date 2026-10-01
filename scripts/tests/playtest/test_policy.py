from scripts.playtest.policy import POLICIES


def test_will_march_aggressive_marches_outnumbered():
    assert POLICIES["aggressive"].will_march(band_size=1, defenders=9) is True


def test_will_march_even_marches_at_equal_numbers():
    assert POLICIES["even"].will_march(band_size=4, defenders=4) is True


def test_will_march_even_stays_home_one_short():
    assert POLICIES["even"].will_march(band_size=3, defenders=4) is False


def test_will_march_prudent_marches_two_up():
    assert POLICIES["prudent"].will_march(band_size=6, defenders=4) is True


def test_will_march_prudent_stays_home_one_up():
    assert POLICIES["prudent"].will_march(band_size=5, defenders=4) is False
