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


def test_is_at_floor_for_an_attribute_the_generator_could_not_put_lower():
    draw = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)

    assert draw.is_at_floor is True


def test_is_at_floor_for_an_attribute_one_point_above_it():
    draw = AttributeDraw(value=4, baseline=10, spread=4, minimum=3)

    assert draw.is_at_floor is False


def test_is_at_floor_for_a_guarded_attribute_takes_the_default_floor_of_one():
    """
    Health and morale are re-rolled while zero rather than floored, so one is as low as they come and
    nothing has to pass a minimum for them.
    """
    draw = AttributeDraw(value=1, baseline=20, spread=5)

    assert draw.is_at_floor is True
