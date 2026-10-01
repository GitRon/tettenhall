from apps.warband.templatetags.gauge import is_below_peak


def test_is_below_peak_ceiling_cut_below_the_peak():
    result = is_below_peak(8, 12)

    assert result is True


def test_is_below_peak_ceiling_at_the_peak():
    result = is_below_peak(12, 12)

    assert result is False


def test_is_below_peak_no_peak_kept():
    result = is_below_peak(8, None)

    assert result is False
