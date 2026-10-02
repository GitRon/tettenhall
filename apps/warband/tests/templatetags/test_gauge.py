from apps.warband.templatetags.gauge import gauge_percent, is_below_a_third, is_below_peak


def test_is_below_peak_ceiling_cut_below_the_peak():
    result = is_below_peak(8, 12)

    assert result is True


def test_is_below_peak_ceiling_at_the_peak():
    result = is_below_peak(12, 12)

    assert result is False


def test_is_below_peak_no_peak_kept():
    result = is_below_peak(8, None)

    assert result is False


def test_gauge_percent_rounds_to_a_whole_percent():
    result = gauge_percent(2, 3)

    assert result == 67


def test_gauge_percent_empty_without_a_maximum():
    result = gauge_percent(0, 0)

    assert result == 0


def test_is_below_a_third_under_it():
    result = is_below_a_third(3, 10)

    assert result is True


def test_is_below_a_third_exactly_at_it():
    result = is_below_a_third(3, 9)

    assert result is False


def test_is_below_a_third_above_it():
    result = is_below_a_third(4, 10)

    assert result is False
