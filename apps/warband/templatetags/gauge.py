from django import template

register = template.Library()


@register.filter
def is_below_peak(maximum: int, peak: int | None) -> bool:  # noqa: PBR001
    """
    Whether a ceiling sits below the highest one the man has held. Health keeps no peak, so a missing
    one is never above anything.
    """
    return peak is not None and maximum < peak


@register.filter
def gauge_percent(current: int, maximum: int) -> int:  # noqa: PBR001
    """
    How full a gauge is, as the whole percent its bar is drawn to. A man with no maximum has nothing to
    fill, so his bar is empty rather than a division by zero.
    """
    if not maximum:
        return 0

    return round(current * 100 / maximum)


@register.filter
def is_below_a_third(current: int, maximum: int) -> bool:  # noqa: PBR001
    """
    Whether a gauge has fallen below a third of its maximum - where a man is one bad blow from dropping,
    and the roster's bar turns to blood.
    """
    return current * 3 < maximum
