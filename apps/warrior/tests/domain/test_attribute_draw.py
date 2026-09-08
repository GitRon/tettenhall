from apps.warrior.domain.attribute_draw import AttributeDraw


def test_reach_for_an_attribute_above_its_mean():
    draw = AttributeDraw(value=18, baseline=10, spread=4)

    assert draw.reach == 2.0


def test_reach_for_an_attribute_below_its_mean():
    """
    Negative rather than clamped, because the comparison that uses it asks which of four attributes
    reached furthest and a man below his kind's mean in all four has to lose that comparison.
    """
    draw = AttributeDraw(value=6, baseline=10, spread=4)

    assert draw.reach == -1.0
